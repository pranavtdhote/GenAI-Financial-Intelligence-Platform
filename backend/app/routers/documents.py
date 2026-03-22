"""Document processing API routes."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.document import DocumentProcessResponse
from app.services.document_processor import DocumentProcessingError, process_pdf
from app.services.file_service import FileService

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def get_file_service(settings: Settings = Depends(get_settings)) -> FileService:
    """Dependency for FileService."""
    return FileService(settings)


@router.post(
    "/process",
    response_model=DocumentProcessResponse,
    summary="Process Financial PDF",
    description=(
        "Upload and process a financial PDF. Pipeline: "
        "1) Detect scanned vs digital, 2) Extract text (direct or OCR), "
        "3) Extract tables, 4) Clean text, 5) Extract metadata."
    ),
    responses={
        400: {"description": "Invalid file or processing failed"},
        500: {"description": "Internal server error"},
        503: {"description": "OCR not available (Tesseract required for scanned PDFs)"},
    },
)
async def process_financial_pdf(
    file: UploadFile = File(..., description="Financial PDF file"),
    settings: Settings = Depends(get_settings),
    file_service: FileService = Depends(get_file_service),
) -> DocumentProcessResponse:
    """
    Process a financial PDF document.
    Returns structured JSON with company_name, report_year, raw_text, extracted_tables, metadata.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="PDF file required",
        )

    content = await file.read()

    # Validate file
    valid, error_msg = file_service.validate_upload(
        filename=file.filename,
        content_type=file.content_type,
        file_size=len(content),
    )
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        result = await process_pdf(tmp_path, settings)
        return DocumentProcessResponse(**result)
    except DocumentProcessingError as e:
        logger.warning("Document processing failed: %s", str(e))
        status = 503 if "Tesseract" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error during document processing")
        raise HTTPException(
            status_code=500,
            detail="Document processing failed. Please try again.",
        ) from e
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@router.post(
    "/process/{stored_filename}",
    response_model=DocumentProcessResponse,
    summary="Process Uploaded PDF by Stored Filename",
    description="Process an already-uploaded PDF by its stored filename.",
    responses={
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
        503: {"description": "OCR not available"},
    },
)
async def process_uploaded_pdf(
    stored_filename: str,
    settings: Settings = Depends(get_settings),
    file_service: FileService = Depends(get_file_service),
) -> DocumentProcessResponse:
    """Process a PDF that was previously uploaded (by stored_filename)."""
    file_path = file_service.get_file_path(stored_filename)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {stored_filename}",
        )

    try:
        result = await process_pdf(file_path, settings)
        return DocumentProcessResponse(**result)
    except DocumentProcessingError as e:
        logger.warning("Document processing failed: %s", str(e))
        status = 503 if "Tesseract" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error during document processing")
        raise HTTPException(
            status_code=500,
            detail="Document processing failed. Please try again.",
        ) from e
