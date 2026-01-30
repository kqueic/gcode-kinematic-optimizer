# UXE Motion Engine v3.5
# Copyright (c) 2026 [kqueic]
# Licensed under the MIT License
import customtkinter as ctk
from tkinter import filedialog, messagebox
import main  # This imports your main.py file
import os

class UXE_App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW CONFIGURATION ---
        self.title("UXE Motion Path Optimizer v2.7")
        self.geometry("540x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- UI LAYOUT ---
        # Header
        self.title_label = ctk.CTkLabel(self, text="UXE KINEMATICS", font=("Courier New", 32, "bold"), text_color="#3b8ed0")
        self.title_label.pack(pady=(30, 10))

        self.subtitle_label = ctk.CTkLabel(self, text="G-Code Physics & Motion Optimizer", font=("Roboto", 12), text_color="gray")
        self.subtitle_label.pack(pady=(0, 20))

        # 1. File Selection Frame
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=10, padx=30, fill="x")
        
        self.btn_select = ctk.CTkButton(self.file_frame, text="SELECT G-CODE FILE", font=("Roboto", 14, "bold"), command=self.browse_file)
        self.btn_select.pack(pady=(15, 5), padx=20)
        
        self.lbl_filename = ctk.CTkLabel(self.file_frame, text="No file loaded...", font=("Roboto", 11), text_color="gray")
        self.lbl_filename.pack(pady=(0, 15))

        # 2. Optimization Mode Frame
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(pady=10, padx=30, fill="x")

        self.lbl_mode = ctk.CTkLabel(self.settings_frame, text="SELECT OPTIMIZATION PRESET", font=("Roboto", 12, "bold"))
        self.lbl_mode.pack(pady=(10, 5))
        
        self.mode_selector = ctk.CTkSegmentedButton(self.settings_frame, values=["QUALITY", "BALANCED", "SPEED"], font=("Roboto", 12))
        self.mode_selector.set("BALANCED")
        self.mode_selector.pack(pady=(5, 15), padx=20)

        # 3. Action Button
        self.btn_run = ctk.CTkButton(self, text="RUN OPTIMIZATION ENGINE", height=50, 
                                     fg_color="#1f538d", hover_color="#14375e", 
                                     font=("Roboto", 16, "bold"),
                                     command=self.execute)
        self.btn_run.pack(pady=25, padx=30, fill="x")

        # 4. Diagnostic Terminal (ASCII Report)
        self.lbl_terminal = ctk.CTkLabel(self, text="DIAGNOSTIC TELEMETRY REPORT", font=("Roboto", 11, "bold"), text_color="gray")
        self.lbl_terminal.pack(padx=30, anchor="w")

        self.txt_output = ctk.CTkTextbox(self, height=250, font=("Courier New", 12), border_width=2)
        self.txt_output.pack(pady=(5, 20), padx=30, fill="both", expand=True)

        self.status_bar = ctk.CTkLabel(self, text="Ready", font=("Roboto", 10), text_color="gray")
        self.status_bar.pack(side="bottom", pady=5)

    def browse_file(self):
        file = filedialog.askopenfilename(filetypes=[("G-Code", "*.gcode"), ("All Files", "*.*")])
        if file:
            self.lbl_filename.configure(text=os.path.basename(file), text_color="#3b8ed0")
            self.input_file = file
            self.status_bar.configure(text=f"Loaded: {os.path.basename(file)}")

    def execute(self):
        # Validation
        if not hasattr(self, 'input_file'):
            messagebox.showwarning("File Missing", "Please select a G-code file first.")
            return
        
        # UI Feedback
        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("end", ">>> INITIALIZING ENGINE...\n")
        self.txt_output.insert("end", f">>> MODE: {self.mode_selector.get()}\n")
        self.txt_output.insert("end", ">>> ANALYZING KINEMATICS...\n\n")
        self.status_bar.configure(text="Processing...")
        self.update() # Forces the window to update while processing

        try:
            # CALLING THE MAIN ENGINE
            # This assumes you renamed your 'main' function in main.py to 'process_gcode'
            # and it returns the ASCII string.
            report = main.process_gcode(self.input_file, self.mode_selector.get())
            
            self.txt_output.delete("0.0", "end")
            self.txt_output.insert("end", report)
            self.status_bar.configure(text="Optimization Complete!")
            
            messagebox.showinfo("Success", "Optimization complete!\nNew G-code and Telemetry JSON generated.")
            
        except Exception as e:
            self.txt_output.insert("end", f"\n❌ ERROR ENCOUNTERED:\n{str(e)}")
            self.status_bar.configure(text="Error occurred.")

if __name__ == "__main__":
    app = UXE_App()
    app.mainloop()