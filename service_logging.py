import logging
import os

def setup_logger(name: str) -> logging.Logger:
    """Creates and configures a logger with the given name.

    :param name: Name of the logger (typically `__name__`).
    :type name: str
    :return: Configured logger instance.
    :rtype: logging.Logger
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    custom_logger = logging.getLogger(name)
    custom_logger.setLevel(log_level)

    # Prevent duplicate log entries if already configured
    if not custom_logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        custom_logger.addHandler(console_handler)

    return custom_logger

# ✅ Root logger setup (for services that don’t explicitly configure a logger)
log = setup_logger("hvac_sim")