"""Structured logging configuration."""

import logging
import sys
from typing import Optional

from app.config import Settings


def setup_logging(settings: Optional[Settings] = None) -> None:
    """
    Configure structured logging for the application.
    Uses JSON-like format for production and readable format for development.
    """
    from app.config import get_settings

    settings = settings or get_settings()
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger("app")
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the app namespace."""
    return logging.getLogger(f"app.{name}")
