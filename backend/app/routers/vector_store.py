"""Vector Store - API routes for semantic search and RAG."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.vector_store import (
    IndexReportRequest,
    IndexReportResponse,
    RAGRequest,
    RAGResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.vector_store import get_collection_stats, index_report, rag_query, search_reports

logger = get_logger(__name__)

router = APIRouter(prefix="/vector", tags=["vector-store"])


@router.post(
    "/index",
    response_model=IndexReportResponse,
    summary="Index Financial Report",
    description="Convert report text into chunks, embed, and store in ChromaDB. Scalable for thousands of reports.",
)
async def index_report_endpoint(
    body: IndexReportRequest,
    settings: Settings = Depends(get_settings),
) -> IndexReportResponse:
    """Index a financial report for semantic search."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: index_report(
                report_id=body.report_id,
                raw_text=body.raw_text,
                company_name=body.company_name,
                report_year=body.report_year,
                metadata=body.metadata,
                settings=settings,
            ),
        )
        return IndexReportResponse(**result)
    except Exception as e:
        logger.exception("Report indexing failed")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}") from e


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic Search",
    description="Query financial reports by natural language. Retrieve relevant report sections.",
)
async def search_reports_endpoint(
    body: SearchRequest,
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    """Semantic search across indexed reports."""
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: search_reports(
                query=body.query,
                top_k=body.top_k,
                report_id=body.report_id,
                company_name=body.company_name,
                report_year=body.report_year,
                settings=settings,
            ),
        )
        return SearchResponse(query=body.query, results=results)
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.post(
    "/rag",
    response_model=RAGResponse,
    summary="RAG Query",
    description="Retrieve relevant report sections and get contextual insight for LLM augmentation.",
)
async def rag_query_endpoint(
    body: RAGRequest,
    settings: Settings = Depends(get_settings),
) -> RAGResponse:
    """RAG: retrieve context and generate prompt for LLM."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: rag_query(
                query=body.query,
                top_k=body.top_k,
                report_id=body.report_id,
                company_name=body.company_name,
                report_year=body.report_year,
                settings=settings,
            ),
        )
        return RAGResponse(**result)
    except Exception as e:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}") from e


@router.get(
    "/stats",
    summary="Collection Stats",
    description="Get vector database statistics (total chunks indexed).",
)
async def collection_stats(settings: Settings = Depends(get_settings)):
    """Get ChromaDB collection statistics."""
    try:
        return get_collection_stats(settings)
    except Exception as e:
        logger.warning("Stats failed: %s", e)
        return {"collection": settings.chroma_collection, "total_chunks": 0, "error": str(e)}
