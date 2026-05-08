"""
Logging utilities for the data pipeline.
"""

import io
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from utils.constants import LOG_FORMAT, LOG_DATE_FORMAT, LOGS_DIR


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Setup a logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    console_handler = logging.StreamHandler(console_stream)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def save_report(data: Dict[str, Any], output_path: Path) -> None:
    """Save a report as JSON."""
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_report(report_path: Path) -> Dict[str, Any]:
    """Load a JSON report."""
    with open(report_path, "r") as f:
        return json.load(f)
