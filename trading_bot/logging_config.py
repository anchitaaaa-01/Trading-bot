"""
logging_config.py
-----------------
Configures application-wide logging with rotating file handler and console handler.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Set up application logging with a rotating file handler and a console handler.

    Args:
        level: The logging level (default: DEBUG).

    Returns:
        The root logger configured with both handlers.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Rotating file handler – max 5 MB per file, keep 5 backups
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler – only WARNING and above so the Rich UI stays clean
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
