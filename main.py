import os
# Inject system ALSA paths to fix Conda Pipewire/PulseAudio missing headers issues on Linux
os.environ["ALSA_PLUGIN_DIR"] = "/usr/lib/x86_64-linux-gnu/alsa-lib/"

import logging
from ui.app import HCursorApp
from core.system_control import SystemController
from core.eye_tracker import EyeTracker
from core.voice_assistant import VoiceAssistant
from utils.calibration import load_calibration
from ui.assistant_ball import AssistantBall

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def main():
    sys_controller = SystemController()
    calib_data = load_calibration()

    def on_eye_move(norm_x, norm_y):
        sw, sh = sys_controller.get_screen_size()
        px, py = norm_x * sw, norm_y * sh
        sys_controller.move_cursor(px, py)
        sys_controller.check_edge_scroll(px, py)

    def on_eye_click():
        sys_controller.click()

    def on_eye_long_click():
        sys_controller.click(button="right")

    from autocorrect import Speller
    spell = Speller(lang='en')
    
    assistant_ball = None # Will be initialized after app

    def on_voice_command(cmd_text):
        first_word = cmd_text.split()[0] if cmd_text else ""
        type_triggers = ["type", "tie", "time", "tight", "typed"]
        
        if first_word in type_triggers:
            parts = cmd_text.split(" ", 1)
            if len(parts) > 1:
                raw_typed = parts[1].strip()
                corrected_text = spell(raw_typed)
                sys_controller.type_text(corrected_text + " ")
            return

        words = cmd_text.split()
        if len(words) <= 3:
            if "double" in cmd_text and "click" in cmd_text:
                sys_controller.double_click()
            elif "right" in cmd_text and "click" in cmd_text:
                sys_controller.click(button="right")
            elif "click" in cmd_text:
                sys_controller.click()
            elif "down" in cmd_text:
                sys_controller.scroll(-5)
            elif "up" in cmd_text:
                sys_controller.scroll(5)
            elif any(k in cmd_text for k in ["enter", "center", "hunter", "enter."]):
                if "center cursor" in cmd_text:
                    sys_controller.center_cursor()
                else:
                    sys_controller.press_key('enter')
            elif "open keyboard" in cmd_text:
                if assistant_ball:
                    assistant_ball.launch_keyboard()
            elif "open browser" in cmd_text:
                if assistant_ball:
                    assistant_ball.launch_browser()
            elif "open file" in cmd_text:
                if assistant_ball:
                    assistant_ball.launch_files()
            elif "open terminal" in cmd_text:
                if assistant_ball:
                    assistant_ball.launch_terminal()
            elif "take screenshot" in cmd_text:
                sys_controller.take_screenshot()
            elif "hide menu" in cmd_text:
                if assistant_ball and assistant_ball.is_expanded:
                    assistant_ball.toggle_menu()
            
    tracker = EyeTracker(on_move=on_eye_move, on_click=on_eye_click, on_long_click=on_eye_long_click)
    tracker.update_calibration(calib_data['min_x'], calib_data['max_x'], calib_data['min_y'], calib_data['max_y'])
    
    voice_assistant = VoiceAssistant(on_command=on_voice_command)
    app = HCursorApp(tracker, voice_assistant, sys_controller)
    assistant_ball = AssistantBall(sys_controller, voice_assistant)
    
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
