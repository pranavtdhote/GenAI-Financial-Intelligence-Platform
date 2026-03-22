"""Security utilities for file validation and handling."""

import hashlib
import uuid
from pathlib import Path
from typing import Tuple

from app.config import Settings


def validate_file_extension(filename: str, settings: Settings) -> Tuple[bool, str]:
    """
    Validate file extension against allowed list.
    Returns (is_valid, error_message).
    """
    if not filename:
        return False, "Filename is required"

    path = Path(filename)
    ext = path.suffix.lower()

    if ext not in [e.lower() for e in settings.allowed_extensions]:
        return False, f"File type not allowed. Allowed: {', '.join(settings.allowed_extensions)}"

    return True, ""


def validate_file_size(file_size: int, settings: Settings) -> Tuple[bool, str]:
    """
    Validate file size against maximum allowed.
    Returns (is_valid, error_message).
    """
    if file_size <= 0:
        return False, "File is empty"

    if file_size > settings.max_upload_size_bytes:
        return False, (
            f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
        )

    return True, ""


def validate_content_type(content_type: str | None, settings: Settings) -> Tuple[bool, str]:
    """
    Validate content type against allowed list.
    Returns (is_valid, error_message).
    """
    if not content_type:
        return False, "Content type is required"

    if "*" in settings.allowed_content_types:
        return True, ""

    if content_type not in settings.allowed_content_types:
        return False, f"Content type not allowed. Allowed: {', '.join(settings.allowed_content_types)}"

    return True, ""


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a unique, secure filename to prevent path traversal and collisions.
    Preserves original extension for downstream processing (e.g., OCR, LLM).
    """
    path = Path(original_filename)
    ext = path.suffix.lower() or ".bin"
    unique_id = uuid.uuid4().hex[:16]
    return f"{unique_id}{ext}"


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for integrity checks."""
    return hashlib.sha256(content).hexdigest()
