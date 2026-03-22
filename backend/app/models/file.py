"""File-related Pydantic models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Metadata for an uploaded file."""

    filename: str = Field(..., description="Original filename")
    stored_filename: str = Field(..., description="Secure filename on disk")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 hash of file content")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class FileUploadResponse(BaseModel):
    """Response model for successful file upload."""

    success: bool = True
    message: str = "File uploaded successfully"
    metadata: FileMetadata = Field(..., description="File metadata")

    model_config = {"json_schema_extra": {"example": {"success": True}}}
