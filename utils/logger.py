"""Structured logging setup with rotation."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from utils.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """Structured formatter with extra fields support."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured output.

        Args:
            record: Log record

        Returns:
            Formatted string
        """
        # Base format
        base = super().format(record)

        # Add extra fields if present
        if hasattr(record, "extra_fields") and record.extra_fields:
            extra = " | ".join(f"{k}={v}" for k, v in record.extra_fields.items())
            return f"{base} | {extra}"

        return base


def setup_logger(name: str = "text_message_bot", use_json: bool = False) -> logging.Logger:
    """
    Set up structured logger with console and file handlers.

    Args:
        name: Logger name
        use_json: Whether to use JSON formatting

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Choose formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error log file (separate file for errors)
    error_handler = RotatingFileHandler(
        log_dir / "bot_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# Global logger instance
logger = setup_logger()

