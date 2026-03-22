"""Service layer for file upload and storage operations."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

from app.config import Settings
from app.core.logging import get_logger
from app.core.security import (
    compute_file_hash,
    generate_secure_filename,
    validate_content_type,
    validate_file_extension,
    validate_file_size,
)
from app.models.file import FileMetadata, FileUploadResponse

logger = get_logger(__name__)


class FileService:
    """
    Handles secure file upload, validation, and storage.
    Designed for future extension with LLM and OCR pipelines.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.upload_dir = settings.ensure_upload_dir()

    def validate_upload(
        self,
        filename: str,
        content_type: Optional[str],
        file_size: int,
    ) -> tuple[bool, str]:
        """
        Validate file before processing.
        Returns (is_valid, error_message).
        """
        valid, msg = validate_file_extension(filename, self.settings)
        if not valid:
            return False, msg

        valid, msg = validate_content_type(content_type, self.settings)
        if not valid:
            return False, msg

        valid, msg = validate_file_size(file_size, self.settings)
        if not valid:
            return False, msg

        return True, ""

    async def save_file(
        self,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> FileUploadResponse:
        """
        Save uploaded file to disk and return metadata.
        Uses async I/O for non-blocking writes.
        """
        stored_filename = generate_secure_filename(filename)
        file_path = self.upload_dir / stored_filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        checksum = compute_file_hash(content)
        metadata = FileMetadata(
            filename=filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=len(content),
            checksum_sha256=checksum,
            uploaded_at=datetime.utcnow(),
        )

        logger.info(
            "File saved",
            extra={
                "original_filename": filename,
                "stored_filename": stored_filename,
                "size": len(content),
                "checksum": checksum,
            },
        )

        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            metadata=metadata,
        )

    def get_file_path(self, stored_filename: str) -> Optional[Path]:
        """
        Get safe path to stored file.
        Prevents path traversal attacks.
        """
        path = (self.upload_dir / stored_filename).resolve()
        try:
            path.relative_to(self.upload_dir.resolve())
        except ValueError:
            return None  # Path traversal attempt
        if not path.exists():
            return None
        return path
