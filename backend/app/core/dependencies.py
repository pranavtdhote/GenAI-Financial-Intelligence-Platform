"""FastAPI dependency injection."""

from pathlib import Path

from fastapi import Depends

from app.config import Settings, get_settings


def get_upload_dir(settings: Settings = Depends(get_settings)) -> Path:
    """Get and ensure upload directory exists."""
    return settings.ensure_upload_dir()
