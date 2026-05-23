"""
Centralized Logging Configuration
===================================
Single source of truth for logging setup across the match engine.
Prevents duplicate handlers and ensures consistent formatting.
"""

import logging
import sys
from pathlib import Path
from .constants import LOG_FORMAT, LOG_DATE_FORMAT, LOGS_DIR

# Track whether logging has been initialized
_LOGGING_INITIALIZED = False


def setup_logging(name: str = "match_engine", level: int = logging.INFO) -> logging.Logger:
    """
    Initialize logging configuration once.
    
    This is idempotent — safe to call multiple times.
    Only the first call actually configures logging.
    
    Args:
        name: Logger name (for root or specific module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger instance
    """
    global _LOGGING_INITIALIZED
    
    # Only configure once
    if not _LOGGING_INITIALIZED:
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove any existing handlers to prevent duplicates
        root_logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (optional, in logs directory)
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_file = LOGS_DIR / "match_engine.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
            file_handler.setFormatter(console_formatter)
            root_logger.addHandler(file_handler)
        except Exception:
            # Silently skip file logging if directory creation fails
            pass
        
        _LOGGING_INITIALIZED = True
    
    # Return logger for this module
    return logging.getLogger(name)
