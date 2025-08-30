import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from controller import HandCursorController

class HandGestureGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hand Gesture Cursor Controller")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Initialize variables
        self.controller = None
        self.is_running = False
        self.current_mode = tk.StringVar(value="general")
        
        # Load settings
        self.settings = self.load_settings()
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """Setup custom styles for the interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', 
                       background='#2c3e50', 
                       foreground='#ecf0f1', 
                       font=('Arial', 24, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#2c3e50', 
                       foreground='#bdc3c7', 
                       font=('Arial', 12))
        
        style.configure('Mode.TButton', 
                       font=('Arial', 11, 'bold'),
                       padding=10)
        
        style.configure('Control.TButton', 
                       font=('Arial', 10),
                       padding=5)
        
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = ttk.Label(title_frame, 
                               text="Hand Gesture Cursor Controller", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="AI-Powered Touchless Control for Medical & Education", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Mode selection section
        self.create_mode_section(main_frame)
        
        # Settings section
        self.create_settings_section(main_frame)
        
        # Control buttons section
        self.create_control_section(main_frame)
        
        # Status section
        self.create_status_section(main_frame)
        
    def create_mode_section(self, parent):
        """Create mode selection section"""
        mode_frame = ttk.LabelFrame(parent, text="Select Mode", padding="15")
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Mode descriptions
        modes = {
            "general": {
                "title": "General Mode",
                "description": "Standard cursor control with basic gestures",
                "color": "#3498db"
            },
            "medical": {
                "title": "Medical Mode",
                "description": "Sterile control for medical procedures with voice feedback",
                "color": "#e74c3c"
            },
            "education": {
                "title": "Education Mode", 
                "description": "Presentation control with slide navigation features",
                "color": "#2ecc71"
            }
        }
        
        for mode_key, mode_info in modes.items():
            mode_container = ttk.Frame(mode_frame)
            mode_container.pack(fill=tk.X, pady=5)
            
            # Radio button
            radio = ttk.Radiobutton(mode_container, 
                                   text=mode_info["title"],
                                   variable=self.current_mode,
                                   value=mode_key,
                                   command=self.on_mode_change)
            radio.pack(side=tk.LEFT)
            
            # Description
            desc_label = ttk.Label(mode_container, 
                                  text=mode_info["description"],
                                  style='Subtitle.TLabel')
            desc_label.pack(side=tk.LEFT, padx=(10, 0))
            
    def create_settings_section(self, parent):
        """Create settings configuration section"""
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Sensitivity setting
        sens_frame = ttk.Frame(settings_frame)
        sens_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sens_frame, text="Gesture Sensitivity:").pack(side=tk.LEFT)
        
        self.sensitivity_var = tk.DoubleVar(value=self.settings.get('sensitivity', 0.7))
        sensitivity_scale = ttk.Scale(sens_frame, 
                                     from_=0.1, to=1.0, 
                                     variable=self.sensitivity_var,
                                     command=self.on_sensitivity_change)
        sensitivity_scale.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.sens_value_label = ttk.Label(sens_frame, text=f"{self.sensitivity_var.get():.1f}")
        self.sens_value_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Click threshold setting
        click_frame = ttk.Frame(settings_frame)
        click_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(click_frame, text="Click Threshold:").pack(side=tk.LEFT)
        
        self.click_threshold_var = tk.IntVar(value=self.settings.get('click_threshold', 25))
        click_scale = ttk.Scale(click_frame, 
                               from_=15, to=50, 
                               variable=self.click_threshold_var,
                               command=self.on_click_threshold_change)
        click_scale.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.click_value_label = ttk.Label(click_frame, text=f"{self.click_threshold_var.get()}")
        self.click_value_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Voice feedback toggle (for medical mode)
        self.voice_enabled = tk.BooleanVar(value=self.settings.get('voice_enabled', True))
        voice_check = ttk.Checkbutton(settings_frame, 
                                     text="Enable Voice Feedback (Medical Mode)",
                                     variable=self.voice_enabled,
                                     command=self.on_voice_toggle)
        voice_check.pack(pady=5)
        
    def create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, 
                                      text="Start Gesture Control",
                                      style='Mode.TButton',
                                      command=self.toggle_gesture_control)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Settings button
        settings_button = ttk.Button(control_frame, 
                                    text="Advanced Settings",
                                    style='Control.TButton',
                                    command=self.open_advanced_settings)
        settings_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Help button
        help_button = ttk.Button(control_frame, 
                                text="Help & Tutorial",
                                style='Control.TButton',
                                command=self.show_help)
        help_button.pack(side=tk.LEFT)
        
        # Calibrate button
        calibrate_button = ttk.Button(control_frame, 
                                     text="Calibrate Camera",
                                     style='Control.TButton',
                                     command=self.calibrate_camera)
        calibrate_button.pack(side=tk.RIGHT)
        
    def create_status_section(self, parent):
        """Create status display section"""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="15")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status text area
        self.status_text = tk.Text(status_frame, 
                                  height=8, 
                                  bg='#34495e', 
                                  fg='#ecf0f1',
                                  font=('Consolas', 10))
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Add initial status message
        self.add_status("Hand Gesture Controller initialized. Select a mode and click 'Start Gesture Control' to begin.")
        
    def on_mode_change(self):
        """Handle mode selection change"""
        mode = self.current_mode.get()
        self.add_status(f"Mode changed to: {mode.title()}")
        self.save_settings()
        
    def on_sensitivity_change(self, value):
        """Handle sensitivity slider change"""
        val = float(value)
        self.sens_value_label.config(text=f"{val:.1f}")
        self.settings['sensitivity'] = val
        self.save_settings()
        
    def on_click_threshold_change(self, value):
        """Handle click threshold slider change"""
        val = int(float(value))
        self.click_value_label.config(text=f"{val}")
        self.settings['click_threshold'] = val
        self.save_settings()
        
    def on_voice_toggle(self):
        """Handle voice feedback toggle"""
        self.settings['voice_enabled'] = self.voice_enabled.get()
        self.save_settings()
        
    def toggle_gesture_control(self):
        """Start or stop gesture control"""
        if not self.is_running:
            self.start_gesture_control()
        else:
            self.stop_gesture_control()
            
    def start_gesture_control(self):
        """Start the gesture control system"""
        try:
            mode = self.current_mode.get()
            self.add_status(f"Starting gesture control in {mode} mode...")
            
            # Create controller with current settings
            self.controller = HandCursorController(
                mode=mode,
                sensitivity=self.settings['sensitivity'],
                click_threshold=self.settings['click_threshold'],
                voice_enabled=self.settings['voice_enabled']
            )
            
            # Start in separate thread to prevent GUI freeze
            self.gesture_thread = threading.Thread(target=self.run_gesture_control, daemon=True)
            self.gesture_thread.start()
            
            self.is_running = True
            self.start_button.config(text="Stop Gesture Control")
            self.add_status("Gesture control started successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start gesture control: {str(e)}")
            self.add_status(f"Error: {str(e)}")
            
    def run_gesture_control(self):
        """Run gesture control in separate thread"""
        try:
            self.controller.run()
        except Exception as e:
            self.add_status(f"Gesture control error: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, self.reset_start_button)
            
    def stop_gesture_control(self):
        """Stop the gesture control system"""
        if self.controller:
            self.controller.cleanup()
            self.controller = None
            
        self.is_running = False
        self.start_button.config(text="Start Gesture Control")
        self.add_status("Gesture control stopped.")
        
    def reset_start_button(self):
        """Reset start button text (called from main thread)"""
        self.start_button.config(text="Start Gesture Control")
        
    def calibrate_camera(self):
        """Open camera calibration window"""
        messagebox.showinfo("Camera Calibration", 
                           "Camera calibration feature will be implemented in the next update.")
        
    def open_advanced_settings(self):
        """Open advanced settings window"""
        messagebox.showinfo("Advanced Settings", 
                           "Advanced settings panel will be implemented in the next update.")
        
    def show_help(self):
        """Show help and tutorial information"""
        help_text = """
Hand Gesture Controls:

General Gestures:
• Point with index finger to move cursor
• Double-touch thumb and index finger to perform a left click
• Fold all fingers to pause/idle the cursor

Notes on Clicking:
• Cursor locks in place during the touch to prevent drift
• A brief hold keeps it steady after the click for accuracy

Medical Mode:
• Voice confirmations for safety
• Sterile operation mode
• Enhanced precision controls

Education Mode:
• Slide navigation gestures (coming soon)
• Presentation controls (coming soon)

Tips:
• Ensure good lighting for best results
• Keep hand 12-18 inches from camera
• Adjust sensitivity if gestures are too sensitive/slow
        """
        
        messagebox.showinfo("Help & Tutorial", help_text)
        
    def add_status(self, message):
        """Add message to status display"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        
    def load_settings(self):
        """Load settings from JSON file"""
        settings_file = "config.json"
        default_settings = {
            'sensitivity': 0.7,
            'click_threshold': 25,
            'voice_enabled': True,
            'mode': 'general'
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults in case of missing keys
                    default_settings.update(settings)
            return default_settings
        except Exception as e:
            self.add_status(f"Error loading settings: {e}")
            return default_settings
            
    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            self.settings['mode'] = self.current_mode.get()
            with open("config.json", 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_gesture_control()
        self.save_settings()
        self.root.destroy()
        
    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = HandGestureGUI()
    app.run()