import os
# Inject system ALSA paths to fix Conda Pipewire/PulseAudio missing headers issues on Linux
os.environ["ALSA_PLUGIN_DIR"] = "/usr/lib/x86_64-linux-gnu/alsa-lib/"

import logging
from ui.app import HCursorApp
from core.system_control import SystemController
from core.eye_tracker import EyeTracker
from core.voice_assistant import VoiceAssistant
from utils.calibration import load_calibration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def main():
    sys_controller = SystemController()
    calib_data = load_calibration()

    def on_eye_move(norm_x, norm_y):
        sw, sh = sys_controller.get_screen_size()
        sys_controller.move_cursor(norm_x * sw, norm_y * sh)

    def on_eye_click():
        sys_controller.click()

    def on_eye_long_click():
        sys_controller.click(button="right")
        
    def on_voice_command(cmd_text):
        if "double click" in cmd_text:
            sys_controller.double_click()
        elif "click" in cmd_text:
            sys_controller.click()
        elif "scroll down" in cmd_text:
            sys_controller.scroll(-500)
        elif "scroll up" in cmd_text:
            sys_controller.scroll(500)
        elif "type" in cmd_text:
            text = cmd_text.split("type", 1)[1].strip()
            if text:
                sys_controller.type_text(text)
            
    tracker = EyeTracker(on_move=on_eye_move, on_click=on_eye_click, on_long_click=on_eye_long_click)
    tracker.update_calibration(calib_data['min_x'], calib_data['max_x'], calib_data['min_y'], calib_data['max_y'])
    
    voice_assistant = VoiceAssistant(on_command=on_voice_command)
    app = HCursorApp(tracker, voice_assistant, sys_controller)
    
    # Start threads via app so we can stop them
    tracker.start()
    voice_assistant.start()
    
    # Run UI
    try:
        app.mainloop()
    except Exception as e:
        logging.error(f"UI Error: {e}")
    finally:
        # Graceful shutdown
        tracker.stop()
        voice_assistant.stop()

if __name__ == "__main__":
    main()
