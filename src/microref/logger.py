import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def setup_logger():
    # --- Log Level Configuration ---
    # Get the log level from .env, defaulting to 'INFO' if not set or invalid.
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_levels.get(log_level_str, logging.INFO)

    # --- File Path Configuration ---
    log_folder_path = os.getenv("LOG_FILE_PATH", ".generated/microref/logs")
    os.makedirs(log_folder_path, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_folder_path, f"log_{timestamp}.log")
    
    # --- Logger Setup ---
    # We now set the level right when we configure the logger.
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file_path,
        filemode='a'
    )
    
    # Get the logger instance
    logger = logging.getLogger("MicroREF")
    
    # Also set the level for the logger instance itself
    logger.setLevel(log_level)
    
    # Add a handler to also print logs to the console
    # This ensures you see errors on screen even if the file log level is high.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) # Console will always show INFO and above
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Avoid adding duplicate handlers if the script is reloaded
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()