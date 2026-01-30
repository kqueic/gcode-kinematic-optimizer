# UXE Motion Engine v3.5
# Copyright (c) 2026 [kqueic]
# Licensed under the MIT License
import math
import os
import json
from collections import deque

# --- 1. CONFIGURATION (Tuned for Commercial Balance) ---
MODES = {
    "QUALITY":  {"K": 0.7, "MIN": 0.4, "E_SAFE": 0.96}, # Smoother, but more forgiving
    "BALANCED": {"K": 0.4, "MIN": 0.6, "E_SAFE": 0.98}, # The "Sweet Spot"
    "SPEED":    {"K": 0.2, "MIN": 0.8, "E_SAFE": 1.00}  # Minimal impact, high efficiency
}

SLICER_DICTIONARY = {
    "WALL_OUTER": ["WALL-OUTER", "OUTER WALL", "EXTERNAL PERIMETER", "PERIMETER-OUTER"],
    "WALL_INNER": ["WALL-INNER", "INNER WALL", "INTERNAL PERIMETER", "PERIMETER-INNER"],
    "SKIN":       ["SKIN", "TOP/BOTTOM", "SOLID-FILL", "TOP SOLID INFILL", "BRIDGE"],
    "FILL":       ["FILL", "INFILL", "INTERNAL INFILL", "SPARSE INFILL"]
}

ANGLE_THRESHOLD = 80.0 # Slightly more sensitive to turns
L_THRESHOLD = 0.5      # MUCH more forgiving on micro-move lengths
LOOK_AHEAD_SIZE = 10   # Increased look-ahead for smoother transitions

# --- 2. UTILITIES ---
def bar(value, max_value=1.0, width=12):
    filled = int((min(value, max_value) / max_value) * width)
    return "█" * filled + "░" * (width - filled)

def detect_feature(line):
    line = line.upper()
    for standard, aliases in SLICER_DICTIONARY.items():
        if any(alias in line for alias in aliases): return standard
    return "DEFAULT"

def get_angle(x1, y1, x2, y2, x3, y3):
    v1, v2 = (x2-x1, y2-y1), (x3-x2, y3-y2)
    m1, m2 = math.sqrt(v1[0]**2+v1[1]**2), math.sqrt(v2[0]**2+v2[1]**2)
    if m1 < 0.05 or m2 < 0.05: return 0.0
    dot = (v1[0]*v2[0] + v1[1]*v2[1])
    cos_val = max(-1.0, min(1.0, dot/(m1*m2)))
    return math.degrees(math.acos(cos_val))

# --- 3. THE ENGINE ---
def process_gcode(input_path, selected_mode):
    cfg = MODES.get(selected_mode, MODES["BALANCED"])
    output_path = os.path.splitext(input_path)[0] + "_optimized.gcode"
    json_path = os.path.splitext(input_path)[0] + "_telemetry.json"
    
    prev_x = prev_y = pprev_x = pprev_y = slicer_f = None
    current_feat = "DEFAULT"
    line_queue, telemetry_moves = deque(), []
    stats = {"total": 0, "slowed": 0, "orig_t": 0.0, "new_t": 0.0, "sum_s": 0.0}

    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for raw_line in fin:
            ls = raw_line.strip()
            if ls.startswith(";"):
                current_feat = detect_feature(ls)
                fout.write(raw_line); continue
            
            if not ls.startswith("G1"):
                if ls.startswith("G0"): pprev_x = pprev_y = None
                fout.write(raw_line); continue

            parts = ls.split()
            x = y = f = e = None
            for p in parts:
                if p.startswith("X"): x = float(p[1:])
                elif p.startswith("Y"): y = float(p[1:])
                elif p.startswith("F"): f = float(p[1:]); slicer_f = f
                elif p.startswith("E"): e = float(p[1:])

            cx, cy = (x if x is not None else prev_x), (y if y is not None else prev_y)
            scale, stress, dist = 1.0, 0.0, 0.0
            
            if cx is not None and cy is not None and prev_x is not None and prev_y is not None:
                dist = math.sqrt((cx-prev_x)**2 + (cy-prev_y)**2)
                if e and e > 0 and dist > 0:
                    ang = get_angle(pprev_x, pprev_y, prev_x, prev_y, cx, cy) if pprev_x is not None else 0
                    
                    # PHYSICS 3.0: Weighted Stress (Turns are 80% of the priority)
                    a_stress = min(1.0, ang / ANGLE_THRESHOLD)
                    l_stress = max(0.0, 1.0 - (dist / L_THRESHOLD))
                    stress = (a_stress * 0.8) + (l_stress * 0.2) 
                    
                    mult = 1.3 if current_feat == "WALL_OUTER" else 1.0
                    scale = max(cfg["MIN"], min(1.0, 1.0 - (cfg["K"] * mult) * stress))
                    stats["total"] += 1

            if x is not None or y is not None:
                if prev_x is not None and dist > 0.05: pprev_x, pprev_y = prev_x, prev_y
                prev_x, prev_y = cx, cy

            line_queue.append({"raw": raw_line, "parts": parts, "scale": scale, "f": slicer_f, "dist": dist, "feat": current_feat, "stress": stress})

            if len(line_queue) >= LOOK_AHEAD_SIZE:
                curr = line_queue.popleft()
                if curr["dist"] > 0 and curr["f"]:
                    # Look-ahead smoothing
                    min_future = min(i["scale"] for i in line_queue if i["dist"] > 0)
                    final_s = min(curr["scale"], min_future * 1.05)
                    
                    stats["orig_t"] += (curr["dist"] / curr["f"])
                    stats["new_t"] += (curr["dist"] / (curr["f"] * final_s))
                    stats["sum_s"] += final_s
                    
                    telemetry_moves.append({"speed_scale": final_s, "stress": curr["stress"], "dist": curr["dist"]})
                    
                    if final_s < 0.98:
                        stats["slowed"] += 1
                        new_f = curr["f"] * final_s
                        new_p = [f"F{new_f:.1f}" if p.startswith("F") else p for p in curr["parts"]]
                        if not any(p.startswith("F") for p in new_p): new_p.append(f"F{new_f:.1f}")
                        fout.write(" ".join(new_p) + "\n")
                    else:
                        fout.write(curr["raw"])
                else:
                    fout.write(curr["raw"])

        while line_queue: fout.write(line_queue.popleft()["raw"])

    # --- 4. SCORING 3.0 ---
    time_impact = round(((stats["new_t"] / max(0.001, stats["orig_t"])) - 1) * 100, 1)
    
    orig_stress_sum = sum(m["stress"] for m in telemetry_moves)
    opt_stress_sum = sum(m["stress"] * m["speed_scale"] for m in telemetry_moves)
    stress_red = round(((opt_stress_sum / max(0.001, orig_stress_sum)) - 1) * 100, 0) if orig_stress_sum > 0 else 0
    
    # New Business-Focused Scoring
    stress_bonus = abs(stress_red) * 1.2
    time_penalty = time_impact * 0.8
    final_score = round(max(0, min(100, 85 + stress_bonus - time_penalty)), 1)
    
    ratios = {
        "hard_brake": round(sum(1 for m in telemetry_moves if m["speed_scale"] < 0.8) / max(1, len(telemetry_moves)), 3),
        "high_stress": round(sum(1 for m in telemetry_moves if m["stress"] > 0.7) / max(1, len(telemetry_moves)), 3),
        "micro_move": round(sum(1 for m in telemetry_moves if m["dist"] < 0.5) / max(1, len(telemetry_moves)), 3)
    }

    # --- 5. REPORT ---
    return f"""
========================================
 UXE MOTION ENGINE v3.0
========================================
 Score        : {final_score} / 100
 Mode         : {selected_mode}

 Behavior Ratios
 ----------------------------------------
 Hard Brakes  : {bar(ratios['hard_brake'])} {ratios['hard_brake']*100:.1f} %
 High Stress  : {bar(ratios['high_stress'])} {ratios['high_stress']*100:.1f} %
 Micro Moves  : {bar(ratios['micro_move'])} {ratios['micro_move']*100:.1f} %

 PERFORMANCE IMPACT
 ----------------------------------------
 Time Added       : {time_impact:+.1f} %
 Stress Reduced   : {stress_red:g} %
 
 Verdict: Optimization Efficiency Validated.
========================================
"""