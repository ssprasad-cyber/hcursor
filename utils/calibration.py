import json
import os
import logging

logger = logging.getLogger("Calibration")

CONFIG_FILE = "hcursor_config.json"

DEFAULT_CALIBRATION = {
    "min_x": 0.45,
    "max_x": 0.55,
    "min_y": 0.45,
    "max_y": 0.55
}

def load_calibration():
    """
    Loads calibration parameters from a local JSON file.
    Returns the default configuration if the file doesn't exist.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded calibration config: {config}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return DEFAULT_CALIBRATION.copy()
    else:
        logger.info("No calibration file found. Using defaults.")
        return DEFAULT_CALIBRATION.copy()

def save_calibration(min_x, max_x, min_y, max_y):
    """
    Saves the calibration bounds to a JSON file.
    """
    config = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
            logger.info(f"Saved calibration config: {config}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False
