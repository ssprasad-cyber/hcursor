import customtkinter as ctk
import logging
import subprocess

logger = logging.getLogger("AssistantBall")

class AssistantBall(ctk.CTkToplevel):
    def __init__(self, sys_controller, voice_assistant, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sys_controller = sys_controller
        self.voice_assistant = voice_assistant
        
        # Window configuration
        self.overrideredirect(True) # Frameless
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.85) # Slight transparency to look more native/floating
        self.geometry("70x70+100+100") # Default starting position
        
        import sys
        if sys.platform.startswith("linux"):
            # Linux X11/Wayland doesn't fully support transparent Toplevel backgrounds easily
            # We use a dark color that blends well
            self.configure(fg_color="#1E1E1E")
        
        # State
        self.is_expanded = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.setup_ball_ui()

    def setup_ball_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        self.geometry("70x70")
        
        self.ball_btn = ctk.CTkButton(
            self, text="AI", width=70, height=70, corner_radius=35,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#1f538d", hover_color="#14375e",
            command=self.toggle_menu
        )
        self.ball_btn.pack(expand=True, fill="both")
        
        # Bind drag events to the button
        self.ball_btn.bind("<ButtonPress-1>", self.on_drag_start)
        self.ball_btn.bind("<B1-Motion>", self.on_drag_motion)

    def setup_menu_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        self.geometry("200x420")
        self.attributes("-alpha", 0.95) # Less transparent when expanded
        
        self.menu_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b", border_width=2, border_color="#1f538d")
        self.menu_frame.pack(expand=True, fill="both")
        
        # Header (draggable)
        self.header = ctk.CTkLabel(self.menu_frame, text="AI Assistant", font=ctk.CTkFont(size=16, weight="bold"))
        self.header.pack(pady=(10, 5))
        self.header.bind("<ButtonPress-1>", self.on_drag_start)
        self.header.bind("<B1-Motion>", self.on_drag_motion)

        # Buttons
        actions = [
            ("⌨ Native Keyboard", self.launch_keyboard),
            ("🌐 Open Browser", self.launch_browser),
            ("📁 Open Files", self.launch_files),
            ("💻 Open Terminal", self.launch_terminal),
            ("📸 Screenshot", self.sys_controller.take_screenshot),
            ("🖱 Left Click", lambda: self.sys_controller.click("left")),
            ("🖱 Right Click", lambda: self.sys_controller.click("right")),
            ("📜 Scroll Up", lambda: self.sys_controller.scroll(5)),
            ("📜 Scroll Down", lambda: self.sys_controller.scroll(-5)),
            ("🎯 Center Cursor", self.sys_controller.center_cursor),
            ("🎤 Toggle Voice", self.toggle_voice),
            ("❌ Close Menu", self.toggle_menu)
        ]

        for text, command in actions:
            btn = ctk.CTkButton(
                self.menu_frame, text=text, width=160, height=26,
                anchor="w", fg_color="transparent", hover_color="#3d3d3d",
                command=command
            )
            btn.pack(pady=2, padx=10)

    def on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_motion(self, event):
        # Calculate new position
        x = self.winfo_x() + event.x - self.drag_start_x
        y = self.winfo_y() + event.y - self.drag_start_y
        self.geometry(f"+{x}+{y}")

    def toggle_menu(self):
        if self.is_expanded:
            self.is_expanded = False
            self.attributes("-alpha", 0.85)
            self.setup_ball_ui()
        else:
            self.is_expanded = True
            self.setup_menu_ui()

    def launch_keyboard(self):
        """Launch the native Linux on-screen keyboard (onboard)."""
        logger.info("Launching native keyboard (onboard)")
        try:
            subprocess.Popen(['onboard'])
        except FileNotFoundError:
            logger.warning("onboard not found, trying gnome-text-input...")
            try:
                subprocess.Popen(['gdbus', 'call', '--session', '--dest', 'org.gnome.Shell', '--object-path', '/org/gnome/Shell', '--method', 'org.gnome.Shell.Eval', 'Main.keyboard.show();'])
            except Exception as e:
                logger.error(f"Failed to launch native keyboard: {e}")

    def launch_browser(self):
        logger.info("Launching default browser")
        try:
            subprocess.Popen(['xdg-open', 'http://'])
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")

    def launch_files(self):
        logger.info("Launching default file manager")
        try:
            subprocess.Popen(['xdg-open', '.'])
        except Exception as e:
            logger.error(f"Failed to launch file manager: {e}")

    def launch_terminal(self):
        logger.info("Launching default terminal")
        try:
            subprocess.Popen(['x-terminal-emulator'])
        except FileNotFoundError:
            try:
                subprocess.Popen(['gnome-terminal'])
            except Exception as e:
                logger.error(f"Failed to launch terminal: {e}")

    def toggle_voice(self):
        if self.voice_assistant.running:
            self.voice_assistant.stop()
            logger.info("Voice assistant paused via Assistant Ball")
        else:
            self.voice_assistant.start()
            logger.info("Voice assistant resumed via Assistant Ball")
