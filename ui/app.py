import customtkinter as ctk
from PIL import Image, ImageTk
import logging

logger = logging.getLogger("UI")

class HCursorApp(ctk.CTk):
    def __init__(self, tracker, voice_assistant, sys_controller):
        super().__init__()
        
        self.tracker = tracker
        self.voice_assistant = voice_assistant
        self.sys_controller = sys_controller

        self.title("HCursor - Assistive Control")
        self.geometry("600x650")
        self.resizable(False, False)
        
        # UI configuration
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()
        self.update_video_stream()

    def setup_ui(self):
        # Top Title
        self.title_label = ctk.CTkLabel(self, text="HCursor Control Panel", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))
        
        # Video Feed Frame
        self.video_frame = ctk.CTkFrame(self, width=480, height=360, corner_radius=10)
        self.video_frame.pack(pady=10)
        self.video_frame.pack_propagate(False)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(expand=True, fill="both")
        
        # Status Frame
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=10, fill="x", padx=40)
        
        # Tracking Toggle Status
        self.eye_tracking_var = ctk.StringVar(value="Running")
        self.eye_tracking_label = ctk.CTkLabel(self.status_frame, text="Eye Tracking:", font=ctk.CTkFont(weight="bold"))
        self.eye_tracking_label.grid(row=0, column=0, sticky="w", pady=5)
        self.eye_status = ctk.CTkLabel(self.status_frame, textvariable=self.eye_tracking_var, text_color="green")
        self.eye_status.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        self.voice_tracking_var = ctk.StringVar(value="Running")
        self.voice_tracking_label = ctk.CTkLabel(self.status_frame, text="Voice Assistant:", font=ctk.CTkFont(weight="bold"))
        self.voice_tracking_label.grid(row=1, column=0, sticky="w", pady=5)
        self.voice_status = ctk.CTkLabel(self.status_frame, textvariable=self.voice_tracking_var, text_color="green")
        self.voice_status.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)
        
        self.btn_calibrate = ctk.CTkButton(self.btn_frame, text="Start Calibration", command=self.on_calibrate)
        self.btn_calibrate.grid(row=0, column=0, padx=10)
        
        self.btn_toggle_voice = ctk.CTkButton(self.btn_frame, text="Pause Voice", command=self.on_toggle_voice)
        self.btn_toggle_voice.grid(row=0, column=1, padx=10)
        
    def update_video_stream(self):
        # We assume tracker.latest_frame gives us a numpy RGB image
        if hasattr(self.tracker, 'latest_frame_rgb') and self.tracker.latest_frame_rgb is not None:
            # Resize image to fit frame
            img = Image.fromarray(self.tracker.latest_frame_rgb)
            img = img.resize((480, 360), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image=img)
            
            self.video_label.configure(image=photo)
            self.video_label.image = photo
            
        self.after(30, self.update_video_stream) # ~30 fps update rate

    def on_calibrate(self):
        # To be implemented: A minimal state change to record bounds
        logger.info("Calibration started.")
        self.btn_calibrate.configure(text="Calibrating... (Look at corners)", state="disabled")
        
        # Trigger actual calibration process in tracker or logic here
        # For simplicity, we schedule it to end after 5 seconds
        def end_calib():
            self.btn_calibrate.configure(text="Start Calibration", state="normal")
            logger.info("Calibration completed.")
            # Typically this will gather data and call self.tracker.update_calibration(...)
            
        self.after(5000, end_calib)

    def on_toggle_voice(self):
        if self.voice_assistant.running:
            self.voice_assistant.stop()
            self.btn_toggle_voice.configure(text="Resume Voice")
            self.voice_tracking_var.set("Paused")
            self.voice_status.configure(text_color="orange")
        else:
            self.voice_assistant.start()
            self.btn_toggle_voice.configure(text="Pause Voice")
            self.voice_tracking_var.set("Running")
            self.voice_status.configure(text_color="green")
