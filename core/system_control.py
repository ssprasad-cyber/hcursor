import pyautogui
import logging
import time
import datetime
import os
import subprocess

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
        
        # Edge Scrolling State
        self.edge_scroll_margin = 50
        self.edge_scroll_delay = 0.3
        self.edge_scroll_start_time = None
        self.edge_scroll_direction = None
        self.last_scroll_time = None
        
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

    def scroll(self, amount, silent=False):
        """Scrolls vertically by the given amount (+ is up, - is down)."""
        try:
            if not silent:
                logger.info(f"Scrolling by {amount}")
            try:
                from pynput.mouse import Controller
                Controller().scroll(0, amount)
            except ImportError:
                pyautogui.scroll(amount * 100) # fallback
        except Exception as e:
            if not silent:
                logger.error(f"Failed to scroll: {e}")
                
    def check_edge_scroll(self, x, y):
        """
        Checks if the cursor is at the top or bottom edge and triggers continuous scrolling.
        """
        current_time = time.time()
        
        direction = None
        if y < self.edge_scroll_margin:
            direction = "up"
        elif y > self.screen_height - self.edge_scroll_margin:
            direction = "down"
            
        if direction:
            if self.edge_scroll_direction != direction:
                # Just entered the edge zone
                self.edge_scroll_direction = direction
                self.edge_scroll_start_time = current_time
                self.last_scroll_time = current_time
            else:
                # Been at the edge for a while
                elapsed_total = current_time - self.edge_scroll_start_time
                if elapsed_total > self.edge_scroll_delay:
                    # Speed multiplier increases the longer they stay at the edge (max 5x)
                    speed_mult = min(5.0, 1.0 + (elapsed_total - self.edge_scroll_delay))
                    
                    # Scroll interval determines how frequently we send a scroll event
                    # At 1x speed, 1 event every 0.1s. At 5x speed, 1 event every 0.02s
                    scroll_interval = 0.1 / speed_mult
                    
                    if (current_time - self.last_scroll_time) > scroll_interval:
                        amount = 1 if direction == "up" else -1
                        self.scroll(amount, silent=True)
                        self.last_scroll_time = current_time
        else:
            self.edge_scroll_direction = None
            self.edge_scroll_start_time = None
            
    def type_text(self, text, interval=0.01):
        """Types out a given string."""
        try:
            logger.info(f"Typing text: '{text}'")
            try:
                from pynput.keyboard import Controller
                Controller().type(text)
            except ImportError:
                pyautogui.write(text, interval=interval)
        except Exception as e:
            logger.error(f"Failed to type text: {e}")

    def press_key(self, key):
        """Presses a specific key (e.g., 'enter', 'tab', 'esc')."""
        try:
            logger.info(f"Pressing key: {key}")
            try:
                from pynput.keyboard import Controller, Key
                keyboard = Controller()
                if key == 'enter':
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)
                else:
                    pyautogui.press(key)
            except ImportError:
                pyautogui.press(key)
        except Exception as e:
            logger.error(f"Failed to press key: {e}")

    def center_cursor(self):
        """Moves the cursor to the center of the screen."""
        try:
            logger.info("Centering cursor")
            self.move_cursor(self.screen_width // 2, self.screen_height // 2)
        except Exception as e:
            logger.error(f"Failed to center cursor: {e}")

    def take_screenshot(self, filename_prefix="screenshot"):
        """Takes a screenshot and saves it locally using native tools."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            logger.info(f"Taking screenshot: {filename}")
            
            # On Linux (Wayland/X11), native screenshot tools are more reliable than pyautogui
            try:
                subprocess.run(['gnome-screenshot', '-f', filename], check=True)
            except Exception as e:
                logger.warning(f"gnome-screenshot failed ({e}), falling back to pyautogui...")
                pyautogui.screenshot(filename)
                
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

# Example usage
if __name__ == "__main__":
    controller = SystemController()
    controller.move_cursor(500, 500)
    time.sleep(0.5)
    controller.move_cursor(600, 600)
