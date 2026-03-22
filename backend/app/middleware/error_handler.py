"""Global error handling middleware."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler for unhandled errors.
    Logs the error and returns a safe generic response.
    """
    from app.config import get_settings

    logger.exception(
        "Unhandled exception: %s - path=%s method=%s",
        str(exc),
        request.url.path,
        request.method,
    )
    settings = get_settings()
    detail = str(exc) if settings.debug else "An unexpected error occurred. Please try again later."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": detail,
        },
    )
