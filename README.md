UXE Motion Engine


Physics-Based G-Code Kinematics Optimizer

UXE Motion Engine is a post-processing tool designed to eliminate 3D printing vibrations (ringing/ghosting) by analyzing geometric stress. Unlike standard slicers, UXE uses a Weighted RSS Stress Model to 
intelligently smooth motion only where it matters.

Based on telemetry data from a 74,000-line 3DBenchy test:

Mode,UXE Score,Time Impact,Stress Reduction,Behavior
SPEED,91.5 / 100,+11.4%,-13%,0.0% Hard Brakes (Fluid Motion)
BALANCED,92.5 / 100,+32.6%,-28%,Balanced protection & speed
QUALITY,72.8 / 100,+88.8%,-49%,Max vibration suppression

How It Works

Angle Stress (80% Weight): Detects sharp directional changes that cause mechanical "jerk."

Micro-Move Stress (20% Weight): Filters high-frequency data segments that overwhelm stepper drivers.

Adaptive Feedrate: Automatically recalculates $F$ values to maintain constant momentum through complex geometry.
Key Features

Zero-Jerk Speed Mode: Achieve smoother prints with almost no increase in print time.

Slicer Agnostic: Supports Cura, PrusaSlicer, Orca Slicer, and Bambu Studio.

Telemetry Reports: Generates a detailed .json file for every run, allowing you to visualize machine stress.

Progressive UI: Easy-to-use interface with real-time optimization tracking.

If you want to run from source:

pip install -r requirements.txt
python main_gui.py

Core Logic
The engine calculates stress using:
Stress = (AngleStress \times 0.8) + (LengthStress \times 0.2)
It then applies a look-ahead smoothing algorithm to ensure transitions are non-violent.

License
This project is licensed under the MIT License - see the LICENSE file for details.
