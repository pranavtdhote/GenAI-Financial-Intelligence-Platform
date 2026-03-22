"""Vector Store - Pydantic models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class IndexReportRequest(BaseModel):
    """Request for indexing a financial report."""

    report_id: str = Field(..., description="Unique report identifier")
    raw_text: str = Field(..., description="Report text to index")
    company_name: Optional[str] = None
    report_year: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class IndexReportResponse(BaseModel):
    """Response from indexing."""

    report_id: str
    chunks_indexed: int
    company_name: Optional[str] = None
    report_year: Optional[str] = None
    message: Optional[str] = None


class SearchRequest(BaseModel):
    """Request for semantic search."""

    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    report_id: Optional[str] = None
    company_name: Optional[str] = None
    report_year: Optional[str] = None


class SearchResult(BaseModel):
    """Single search result."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class SearchResponse(BaseModel):
    """Response from semantic search."""

    query: str
    results: list[dict[str, Any]] = Field(default_factory=list)


class RAGRequest(BaseModel):
    """Request for RAG query."""

    query: str = Field(..., description="Natural language question")
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    report_id: Optional[str] = None
    company_name: Optional[str] = None
    report_year: Optional[str] = None


class RAGResponse(BaseModel):
    """Response from RAG query."""

    query: str
    context_chunks: list[dict[str, Any]] = Field(default_factory=list)
    context_text: str = ""
    rag_prompt: str = ""
    chunks_retrieved: int = 0
