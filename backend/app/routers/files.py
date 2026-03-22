"""File upload API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.config import Settings
from app.core.logging import get_logger
from app.models.file import FileUploadResponse
from app.services.file_service import FileService

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(settings: Settings = Depends(get_settings)) -> FileService:
    """Dependency for FileService."""
    return FileService(settings)


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    responses={
        400: {"description": "Invalid file or validation failed"},
        413: {"description": "File too large"},
        500: {"description": "Internal server error"},
    },
    summary="Upload Financial PDF",
    description="Upload a financial report PDF. File is validated and stored securely.",
)
async def upload_financial_pdf(
    file: UploadFile = File(..., description="Financial PDF file"),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload a financial PDF report.
    - Validates file type (PDF only)
    - Validates file size (configurable limit)
    - Stores with secure filename
    - Returns file metadata for downstream processing (LLM/OCR)
    """
    settings = file_service.settings

    # Validate filename
    if not file.filename:
        logger.warning("Upload attempted without filename")
        raise HTTPException(status_code=400, detail="Filename is required")

    # Read content (stream in chunks for large files)
    content = await file.read()

    # Validate before processing
    valid, error_msg = file_service.validate_upload(
        filename=file.filename,
        content_type=file.content_type,
        file_size=len(content),
    )
    if not valid:
        logger.warning("Upload validation failed", extra={"original_filename": file.filename, "error": error_msg})
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        response = await file_service.save_file(
            filename=file.filename,
            content=content,
            content_type=file.content_type or "application/pdf",
        )
        return response
    except OSError as e:
        logger.exception("Failed to save file", extra={"original_filename": file.filename})
        raise HTTPException(
            status_code=500,
            detail="Failed to save file. Please try again.",
        ) from e
