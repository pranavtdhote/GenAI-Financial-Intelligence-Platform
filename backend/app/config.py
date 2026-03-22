"""Environment-based configuration management."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # Application
    app_name: str = Field(default="Financial Report Analysis API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security - File Upload
    upload_dir: Path = Field(default=Path("uploads"), alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_extensions: List[str] = Field(
        default=[".pdf"],
        alias="ALLOWED_EXTENSIONS",
    )
    allowed_content_types: List[str] = Field(
        default=["application/pdf"],
        alias="ALLOWED_CONTENT_TYPES",
    )

    # Document Processing (OCR)
    tesseract_cmd: str | None = Field(default=None, alias="TESSERACT_CMD")
    scanned_text_threshold: int = Field(
        default=50,
        alias="SCANNED_TEXT_THRESHOLD",
        description="Min chars per page to consider PDF digital (else scanned)",
    )
    ocr_dpi: int = Field(default=300, alias="OCR_DPI", description="DPI for OCR page rendering")

    # LLM (GenAI) - Groq API
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")

    # Vector Database (ChromaDB)
    chroma_persist_dir: Path = Field(default=Path("chroma_db"), alias="CHROMA_PERSIST_DIR")
    chroma_collection: str = Field(default="financial_reports", alias="CHROMA_COLLECTION")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
        description="sentence-transformers model for embeddings",
    )
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE", description="Characters per chunk")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP", description="Overlap between chunks")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K", description="Number of chunks to retrieve for RAG")

    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        alias="CORS_ORIGINS",
    )
    cors_methods: List[str] = Field(
        default=["*"],
        alias="CORS_METHODS",
    )
    cors_headers: List[str] = Field(
        default=["*"],
        alias="CORS_HEADERS",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_upload_dir(self) -> Path:
        """Create upload directory if it doesn't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        return self.upload_dir

_settings_cache: Settings | None = None


def get_settings() -> Settings:
    """Get settings instance. Re-reads .env on each server restart."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
    return _settings_cache


def clear_settings_cache() -> None:
    """Clear cached settings - call on server startup to force re-read of .env."""
    global _settings_cache
    _settings_cache = None
