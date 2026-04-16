import pyautogui
import logging
import time

# Configure PyAutoGUI to be safe and responsive
pyautogui.FAILSAFE = False # Disable fail-safe to prevent accidental crashes during eye tracking
pyautogui.PAUSE = 0.0 # Remove delays after PyAutoGUI calls for real-time responsiveness

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SystemControl")

class SystemController:
    """
    Handles translation of application events into OS-level mouse and keyboard actions.
    Implements cursor smoothing for less jittery eye tracking.
    """
    def __init__(self, smoothing_alpha=0.3):
        self.smoothing_alpha = smoothing_alpha
        
        # Cursor state for EMA smoothing
        self.current_x = None
        self.current_y = None
        
        # Screen dimensions
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception as e:
            logger.warning(f"Failed to get screen size: {e}")
            self.screen_width, self.screen_height = 1920, 1080 # Fallback
            
        logger.info(f"SystemController initialized. Screen Size: {self.screen_width}x{self.screen_height}")

    def get_screen_size(self):
        return self.screen_width, self.screen_height

    def move_cursor(self, target_x, target_y):
        """
        Moves the cursor to the specified target coordinates using Exponential Moving Average for smoothing.
        target_x and target_y should be absolute pixel coordinates.
        """
        # Constrain coordinates to screen bounds
        target_x = max(0, min(self.screen_width - 1, target_x))
        target_y = max(0, min(self.screen_height - 1, target_y))
        
        if self.current_x is None or self.current_y is None:
            # First movement, just jump to it
            self.current_x = target_x
            self.current_y = target_y
        else:
            # Apply EMA
            self.current_x = (self.smoothing_alpha * target_x) + ((1.0 - self.smoothing_alpha) * self.current_x)
            self.current_y = (self.smoothing_alpha * target_y) + ((1.0 - self.smoothing_alpha) * self.current_y)
            
        try:
            pyautogui.moveTo(int(self.current_x), int(self.current_y))
        except Exception as e:
            logger.error(f"Failed to move cursor: {e}")

    def move_cursor_relative(self, delta_x, delta_y):
        """
        Moves the cursor relatively from current position. (No EMA here as it's typically for discrete pushes)
        """
        try:
            pyautogui.move(delta_x, delta_y)
            # Update EMA state to follow relative jumps
            pos = pyautogui.position()
            self.current_x, self.current_y = pos.x, pos.y
        except Exception as e:
            logger.error(f"Failed to move cursor relatively: {e}")

    def click(self, button="left"):
        """Performs a single click."""
        try:
            logger.info(f"Performing {button} click")
            pyautogui.click(button=button)
        except Exception as e:
            logger.error(f"Failed to click: {e}")

    def double_click(self):
        """Performs a double click."""
        try:
            logger.info("Performing double click")
            pyautogui.doubleClick()
        except Exception as e:
            logger.error(f"Failed to double click: {e}")

    def scroll(self, amount):
        """Scrolls vertically by the given amount (+ is up, - is down)."""
        try:
            logger.info(f"Scrolling by {amount}")
            pyautogui.scroll(amount)
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
            
    def type_text(self, text, interval=0.01):
        """Types out a given string."""
        try:
            logger.info(f"Typing text: {text}")
            pyautogui.write(text, interval=interval)
        except Exception as e:
            logger.error(f"Failed to type text: {e}")

    def press_key(self, key):
        """Presses a specific key (e.g., 'enter', 'tab', 'esc')."""
        try:
            logger.info(f"Pressing key: {key}")
            pyautogui.press(key)
        except Exception as e:
            logger.error(f"Failed to press key: {e}")

# Example usage
if __name__ == "__main__":
    controller = SystemController()
    controller.move_cursor(500, 500)
    time.sleep(0.5)
    controller.move_cursor(600, 600)
