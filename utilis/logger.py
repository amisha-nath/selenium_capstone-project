import logging
import os
from datetime import datetime

# Create log directory if not present
LOG_DIR = "reports/logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def get_logger(name=__name__):
    """Setup and return a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_format)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_format)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.propagate = False  # Prevent duplicate logs

    return logger