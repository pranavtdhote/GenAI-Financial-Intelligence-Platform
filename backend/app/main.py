"""FastAPI application entry point - Financial Report Analysis Platform."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load env variables explicitly
load_dotenv()

from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.middleware.error_handler import global_exception_handler
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers.documents import router as documents_router
from app.routers.files import router as files_router
from app.routers.financial import router as financial_router
from app.routers.llm import router as llm_router
from app.routers.trends import router as trends_router
from app.routers.knowledge_graph import router as knowledge_graph_router
from app.routers.vector_store import router as vector_store_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Force re-read of .env on every server restart
    from app.config import clear_settings_cache
    clear_settings_cache()
    
    settings = get_settings()
    setup_logging(settings)
    logger = get_logger(__name__)

    # Ensure upload directory exists
    settings.ensure_upload_dir()
    logger.info("Application startup complete - upload dir: %s", settings.upload_dir)
    logger.info("Groq API key configured: %s", bool(settings.groq_api_key))
    logger.info("Groq model: %s", settings.groq_model)

    yield

    logger.info("Application shutdown")


def create_application() -> FastAPI:
    """Application factory for clean architecture and testability."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend for Generative AI–Driven Financial Report Analysis Platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    # Validation error handler - structured 422 response
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )

    # Routers
    app.include_router(files_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(financial_router, prefix="/api/v1")
    app.include_router(llm_router, prefix="/api/v1")
    app.include_router(trends_router, prefix="/api/v1")
    app.include_router(knowledge_graph_router, prefix="/api/v1")
    app.include_router(vector_store_router, prefix="/api/v1")

    # Debug endpoint to check config
    @app.get("/debug/config", tags=["debug"])
    async def debug_config():
        import os
        s = get_settings()
        return {
            "groq_key_present": bool(s.groq_api_key),
            "groq_key_prefix": s.groq_api_key[:10] if s.groq_api_key else None,
            "groq_model": s.groq_model,
            "openai_env": os.environ.get("OPENAI_API_KEY", "NOT_SET")[:15] if os.environ.get("OPENAI_API_KEY") else "NOT_SET",
        }

    # Health check
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}

    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Financial Report Analysis API",
            "docs": "/docs",
            "health": "/health",
            "upload": "/api/v1/files/upload",
            "process": "/api/v1/documents/process",
            "analyze": "/api/v1/financial/analyze",
            "genai": "/api/v1/llm/analyze",
            "trends": "/api/v1/trends/compare",
            "knowledge_graph": "/api/v1/knowledge-graph/build",
            "vector_index": "/api/v1/vector/index",
            "vector_search": "/api/v1/vector/search",
            "vector_rag": "/api/v1/vector/rag",
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
