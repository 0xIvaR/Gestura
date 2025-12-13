import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from controller import HandCursorController

class HandGestureGUI:
    def __init__(self):
        # Load configuration from gestura_config.json
        self.config = self.load_gestura_config()
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title(self.config["app_config"]["title"])
        window_config = self.config["app_config"]["window_size"]
        self.root.geometry(f"{window_config['width']}x{window_config['height']}")
        self.root.configure(bg=self.config["app_config"]["theme"]["bg_color"])
        self.root.resizable(False, False)
        
        # Initialize variables
        self.controller = None
        self.is_running = False
        self.current_mode = tk.StringVar()
        
        # Set initial mode from config
        active_mode = next((mode["name"].lower() for mode in self.config["sidebar"]["modes"] if mode["active"]), "study")
        self.current_mode.set(active_mode)
        
        # Initialize settings from config
        self.settings = self.initialize_settings_from_config()
        
        # Create GUI
        self.create_widgets()
        
    def load_gestura_config(self):
        """Load configuration from gestura_config.json"""
        try:
            with open("gestura_config.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading gestura_config.json: {e}")
            # Return default config if file not found
            return {
                "app_config": {
                    "title": "GESTURA",
                    "window_size": {"width": 1000, "height": 700},
                    "theme": {
                        "bg_color": "#f5f5f5",
                        "sidebar_color": "#ffffff",
                        "text_color": "#333333",
                        "accent_color": "#6b7280",
                        "button_color": "#ffffff",
                        "button_hover": "#f3f4f6",
                        "slider_color": "#d1d5db",
                        "slider_active": "#6b7280"
                    }
                },
                "sidebar": {
                    "modes": [
                        {"name": "Study", "icon": "📚", "active": True},
                        {"name": "General", "icon": "⚙️", "active": False}
                    ]
                },
                "cursor_control": {
                    "title": "Cursor Control",
                    "settings": [
                        {"name": "Smoothness", "type": "slider", "min": 0, "max": 100, "default": 40},
                        {"name": "Sensitivity", "type": "slider", "min": 0, "max": 100, "default": 60},
                        {"name": "Live Camera Preview", "type": "toggle", "default": False}
                    ]
                },
                "main_button": {
                    "text": "Start Gesture Control",
                    "icon": "▶️",
                    "action": "start_gesture_control"
                },
                "status_bar": {
                    "status": "ready",
                    "camera": "connected"
                }
            }

    def initialize_settings_from_config(self):
        """Initialize settings based on config"""
        settings = {}
        for setting in self.config["cursor_control"]["settings"]:
            if setting["type"] == "slider":
                settings[setting["name"].lower()] = setting["default"]
            elif setting["type"] == "toggle":
                settings[setting["name"].lower().replace(" ", "_")] = setting["default"]
        return settings

    def create_widgets(self):
        """Create main GUI layout following config structure"""
        # Create main container
        main_container = tk.Frame(self.root, bg=self.config["app_config"]["theme"]["bg_color"])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.create_sidebar(main_container)
        
        # Create main content area
        self.create_main_content(main_container)
        
        # Create status bar
        self.create_status_bar(main_container)

    def create_sidebar(self, parent):
        """Create sidebar with modes according to config"""
        theme = self.config["app_config"]["theme"]
        sidebar = tk.Frame(parent, bg=theme["sidebar_color"], width=200, relief='flat', bd=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        sidebar.pack_propagate(False)
        
        # Sidebar header
        header_frame = tk.Frame(sidebar, bg=theme["sidebar_color"], height=80)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text=self.config["app_config"]["title"],
                              font=('Segoe UI', 18, 'bold'),
                              fg=theme["text_color"],
                              bg=theme["sidebar_color"])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(header_frame,
                                 text="Gesture Control",
                                 font=('Segoe UI', 10),
                                 fg=theme["accent_color"],
                                 bg=theme["sidebar_color"])
        subtitle_label.pack(anchor='w', pady=(2, 0))
        
        # Mode selection buttons
        modes_frame = tk.Frame(sidebar, bg=theme["sidebar_color"])
        modes_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.mode_buttons = {}
        for mode in self.config["sidebar"]["modes"]:
            mode_frame = tk.Frame(modes_frame, bg=theme["sidebar_color"])
            mode_frame.pack(fill=tk.X, pady=5)
            
            mode_btn = tk.Button(mode_frame,
                               text=f"{mode['icon']} {mode['name']}",
                               font=('Segoe UI', 11),
                               fg=theme["text_color"],
                               bg=theme["button_color"] if mode["active"] else theme["sidebar_color"],
                               activebackground=theme["button_hover"],
                               relief='flat',
                               bd=0,
                               cursor='hand2',
                               anchor='w',
                               padx=15,
                               pady=10,
                               command=lambda m=mode["name"].lower(): self.select_mode(m))
            mode_btn.pack(fill=tk.X)
            
            self.mode_buttons[mode["name"].lower()] = mode_btn
        
        # Update initial selection
        self.update_mode_selection()

    def create_main_content(self, parent):
        """Create main content area with cursor control settings"""
        theme = self.config["app_config"]["theme"]
        content_area = tk.Frame(parent, bg=theme["bg_color"])
        content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cursor Control Section
        control_frame = tk.Frame(content_area, bg=theme["sidebar_color"], relief='flat', bd=0)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Section header
        header_frame = tk.Frame(control_frame, bg=theme["sidebar_color"], height=60)
        header_frame.pack(fill=tk.X, padx=30, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame,
                              text=self.config["cursor_control"]["title"],
                              font=('Segoe UI', 16, 'bold'),
                              fg=theme["text_color"],
                              bg=theme["sidebar_color"])
        title_label.pack(anchor='w', pady=(15, 0))
        
        # Settings from config
        settings_frame = tk.Frame(control_frame, bg=theme["sidebar_color"])
        settings_frame.pack(fill=tk.X, padx=30, pady=(10, 30))
        
        self.setting_vars = {}
        self.setting_labels = {}
        
        for setting in self.config["cursor_control"]["settings"]:
            setting_container = tk.Frame(settings_frame, bg=theme["sidebar_color"])
            setting_container.pack(fill=tk.X, pady=10)
            
            if setting["type"] == "slider":
                self.create_slider_setting(setting_container, setting, theme)
            elif setting["type"] == "toggle":
                self.create_toggle_setting(setting_container, setting, theme)
        
        # Main action button
        button_frame = tk.Frame(content_area, bg=theme["bg_color"])
        button_frame.pack(fill=tk.X, pady=20)
        
        main_btn_config = self.config["main_button"]
        self.main_button = tk.Button(button_frame,
                                   text=f"{main_btn_config['icon']} {main_btn_config['text']}",
                                   font=('Segoe UI', 14, 'bold'),
                                   fg='white',
                                   bg=theme["accent_color"],
                                   activebackground='#4b5563',
                                   relief='flat',
                                   bd=0,
                                   cursor='hand2',
                                   padx=30,
                                   pady=15,
                                   command=self.toggle_gesture_control)
        self.main_button.pack()

    def create_slider_setting(self, parent, setting, theme):
        """Create a slider setting widget"""
        # Label
        label = tk.Label(parent,
                        text=setting["name"],
                        font=('Segoe UI', 11),
                        fg=theme["text_color"],
                        bg=theme["sidebar_color"])
        label.pack(anchor='w', pady=(0, 5))
        
        # Slider container
        slider_container = tk.Frame(parent, bg=theme["sidebar_color"])
        slider_container.pack(fill=tk.X)
        
        # Variable for slider
        var = tk.IntVar(value=setting["default"])
        self.setting_vars[setting["name"].lower()] = var
        
        # Slider
        slider = tk.Scale(slider_container,
                         from_=setting["min"],
                         to=setting["max"],
                         orient=tk.HORIZONTAL,
                         variable=var,
                         bg=theme["sidebar_color"],
                         fg=theme["text_color"],
                         activebackground=theme["slider_active"],
                         troughcolor=theme["slider_color"],
                         highlightthickness=0,
                         bd=0,
                         font=('Segoe UI', 9),
                         command=lambda val, name=setting["name"]: self.on_setting_change(name, val))
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Value label
        value_label = tk.Label(slider_container,
                              text=str(setting["default"]),
                              font=('Segoe UI', 10, 'bold'),
                              fg=theme["accent_color"],
                              bg=theme["sidebar_color"],
                              width=5)
        value_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.setting_labels[setting["name"].lower()] = value_label

    def create_toggle_setting(self, parent, setting, theme):
        """Create a toggle setting widget"""
        var = tk.BooleanVar(value=setting["default"])
        self.setting_vars[setting["name"].lower().replace(" ", "_")] = var
        
        toggle = tk.Checkbutton(parent,
                               text=setting["name"],
                               variable=var,
                               font=('Segoe UI', 11),
                               fg=theme["text_color"],
                               bg=theme["sidebar_color"],
                               activebackground=theme["sidebar_color"],
                               selectcolor=theme["slider_color"],
                               command=lambda: self.on_toggle_change(setting["name"]))
        toggle.pack(anchor='w')

    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        theme = self.config["app_config"]["theme"]
        status_config = self.config["status_bar"]
        
        status_bar = tk.Frame(parent, bg=theme["accent_color"], height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)
        
        # Status indicators
        status_frame = tk.Frame(status_bar, bg=theme["accent_color"])
        status_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.status_label = tk.Label(status_frame,
                                   text=f"Status: {status_config['status'].title()}",
                                   font=('Segoe UI', 9),
                                   fg='white',
                                   bg=theme["accent_color"])
        self.status_label.pack(side=tk.LEFT)
        
        self.camera_label = tk.Label(status_frame,
                                   text=f"Camera: {status_config['camera'].title()}",
                                   font=('Segoe UI', 9),
                                   fg='white',
                                   bg=theme["accent_color"])
        self.camera_label.pack(side=tk.LEFT, padx=(20, 0))
        
    def select_mode(self, mode):
        """Handle mode selection"""
        self.current_mode.set(mode)
        self.update_mode_selection()
        self.update_status(f"Mode changed to: {mode.title()}")

    def update_mode_selection(self):
        """Update visual state of mode buttons"""
        theme = self.config["app_config"]["theme"]
        current = self.current_mode.get()
        
        for mode_name, button in self.mode_buttons.items():
            if mode_name == current:
                button.config(bg=theme["button_hover"])
            else:
                button.config(bg=theme["sidebar_color"])

    def on_setting_change(self, setting_name, value):
        """Handle slider setting changes"""
        val = int(float(value))
        self.settings[setting_name.lower()] = val
        if setting_name.lower() in self.setting_labels:
            self.setting_labels[setting_name.lower()].config(text=str(val))

    def on_toggle_change(self, setting_name):
        """Handle toggle setting changes"""
        key = setting_name.lower().replace(" ", "_")
        if key in self.setting_vars:
            self.settings[key] = self.setting_vars[key].get()

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
            self.update_status(f"Starting gesture control in {mode} mode...")
            self.update_camera_status("initializing")
            
            # Create controller with current settings
            self.controller = HandCursorController(
                mode=mode,
                sensitivity=self.settings.get('sensitivity', 60) / 100.0,  # Convert to 0-1 range
                click_threshold=self.settings.get('smoothness', 40),
                voice_enabled=self.settings.get('live_camera_preview', False)
            )
            
            # Start in separate thread to prevent GUI freeze
            self.gesture_thread = threading.Thread(target=self.run_gesture_control, daemon=True)
            self.gesture_thread.start()
            
            self.is_running = True
            self.main_button.config(text="⏹️ Stop Gesture Control")
            self.update_status("Gesture control started successfully!")
            self.update_camera_status("active")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start gesture control: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            self.update_camera_status("error")

    def run_gesture_control(self):
        """Run gesture control in separate thread"""
        try:
            self.controller.run()
        except Exception as e:
            self.update_status(f"Gesture control error: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, self.reset_main_button)

    def stop_gesture_control(self):
        """Stop the gesture control system"""
        if self.controller:
            self.controller.cleanup()
            self.controller = None
            
        self.is_running = False
        self.main_button.config(text="▶️ Start Gesture Control")
        self.update_status("Gesture control stopped.")
        self.update_camera_status("connected")

    def reset_main_button(self):
        """Reset main button text (called from main thread)"""
        self.main_button.config(text="▶️ Start Gesture Control")
        self.update_camera_status("connected")

    def update_status(self, message):
        """Update status in status bar"""
        self.status_label.config(text=f"Status: {message}")

    def update_camera_status(self, status):
        """Update camera status in status bar"""
        self.camera_label.config(text=f"Camera: {status.title()}")

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_gesture_control()
        self.root.destroy()

    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = HandGestureGUI()
    app.run()