

import logging
import os
from dotenv import load_dotenv
from httpcore.AppConstants import AppConstants


def setup_logging(log_level_str):
    """Sets up logging based on a single configuration parameter in a .env file.

    Args:
        env_var_name: The name of the environment variable containing the log level.

    Returns:
        The logger object.  Returns None if there's an issue.
    """

    if log_level_str is None:
        print(f"Environment variable '{log_level_str}' not found. Using default logging level INFO.")
        log_level = logging.INFO
    else:
        try:
            log_level = getattr(logging, log_level_str.upper())  # Convert string to logging level
            if not isinstance(log_level, int): # Check if the level is valid
              raise AttributeError # Raise error if invalid log level
        except AttributeError:
            print(f"Invalid log level '{log_level_str}'. Using default logging level INFO.")
            log_level = logging.INFO

    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    return logger

# Example Usage:

# Create a .env file in your project directory (or a parent directory) with:
# LOG_LEVEL=DEBUG  # Or INFO, WARNING, ERROR, CRITICAL

level = AppConstants.LOG_LEVEL if AppConstants else "INFO"

logger = setup_logging(level)  # Uses default environment variable name "LOG_LEVEL"

