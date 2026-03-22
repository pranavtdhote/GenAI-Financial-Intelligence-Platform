"""Vector Database Service - ChromaDB integration for semantic search and RAG."""

from typing import Any, Optional

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Check ChromaDB availability at module level
_chromadb_available = True
try:
    import chromadb  # noqa: F401
except Exception as _chromadb_err:
    _chromadb_available = False
    logger.warning(
        "ChromaDB not available (vector store features disabled): %s",
        _chromadb_err,
    )

# Lazy-load ChromaDB client and embedding model
_chroma_client = None
_embedding_model = None


def _get_chroma_client(settings: Settings):
    """Lazy load ChromaDB client. Returns None if chromadb is unavailable."""
    global _chroma_client
    if not _chromadb_available:
        return None
    if _chroma_client is None:
        import chromadb

        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    return _chroma_client


def _get_embedding_function(settings: Settings):
    """Get embedding function - sentence-transformers only."""
    if not _chromadb_available:
        return None
    import chromadb.utils.embedding_functions as ef

    try:
        return ef.SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    except Exception as e:
        logger.warning("SentenceTransformer failed, using fallback: %s", e)
        return ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def _chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Preserves sentence boundaries where possible.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        # Try to break at sentence boundary
        segment = text[start:end]
        last_period = segment.rfind(". ")
        last_newline = segment.rfind("\n")
        break_point = max(last_period, last_newline)
        if break_point > chunk_size // 2:
            end = start + break_point + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap if chunk_overlap > 0 else end

    return chunks


def index_report(
    report_id: str,
    raw_text: str,
    company_name: Optional[str] = None,
    report_year: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    settings: Optional[Settings] = None,
) -> dict[str, Any]:
    """
    Convert financial report into chunks, embed, and store in ChromaDB.
    Scalable: batches chunks for efficient indexing.
    Returns graceful fallback if ChromaDB is unavailable.
    """
    from app.config import get_settings

    settings = settings or get_settings()
    client = _get_chroma_client(settings)
    if client is None:
        logger.info("Skipping report indexing — ChromaDB unavailable")
        return {"report_id": report_id, "chunks_indexed": 0, "message": "ChromaDB unavailable"}
    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=_get_embedding_function(settings),
        metadata={"hnsw:space": "cosine"},
    )

    chunks = _chunk_text(
        raw_text,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not chunks:
        return {"report_id": report_id, "chunks_indexed": 0, "message": "No text to index"}

    base_meta = {
        "report_id": report_id,
        "company_name": company_name or "",
        "report_year": report_year or "",
    }
    if metadata:
        base_meta.update({k: str(v) for k, v in metadata.items()})

    ids = [f"{report_id}:{i}" for i in range(len(chunks))]
    metadatas = [{**base_meta, "chunk_index": i} for i in range(len(chunks))]

    # Batch add (ChromaDB handles batching internally for large datasets)
    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info("Indexed report %s: %d chunks", report_id, len(chunks))
    return {
        "report_id": report_id,
        "chunks_indexed": len(chunks),
        "company_name": company_name,
        "report_year": report_year,
    }


def search_reports(
    query: str,
    top_k: int = 5,
    report_id: Optional[str] = None,
    company_name: Optional[str] = None,
    report_year: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> list[dict[str, Any]]:
    """
    Semantic search across indexed financial reports.
    Returns relevant report sections with scores.
    Returns empty list if ChromaDB is unavailable.
    """
    from app.config import get_settings

    settings = settings or get_settings()
    client = _get_chroma_client(settings)
    if client is None:
        return []
    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=_get_embedding_function(settings),
    )

    where = {}
    if report_id:
        where["report_id"] = report_id
    if company_name:
        where["company_name"] = company_name
    if report_year:
        where["report_year"] = report_year

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, 50),
        where=where if where else None,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results["documents"] or not results["documents"][0]:
        return []

    out = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        dist = results["distances"][0][i] if results.get("distances") else None
        # Convert distance to similarity (cosine: 1 - distance for normalized vectors)
        score = 1 - dist if dist is not None and dist <= 2 else None
        out.append({
            "content": doc,
            "metadata": meta,
            "score": round(score, 4) if score is not None else None,
        })
    return out


def rag_query(
    query: str,
    top_k: Optional[int] = None,
    report_id: Optional[str] = None,
    company_name: Optional[str] = None,
    report_year: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> dict[str, Any]:
    """
    RAG: Retrieve relevant report sections and provide contextual insight.
    Returns retrieved context + formatted prompt for LLM augmentation.
    """
    if not _chromadb_available:
        return {"query": query, "context_chunks": [], "context_text": "", "rag_prompt": "", "chunks_retrieved": 0}

    from app.config import get_settings

    settings = settings or get_settings()
    k = top_k or settings.rag_top_k

    results = search_reports(
        query=query,
        top_k=k,
        report_id=report_id,
        company_name=company_name,
        report_year=report_year,
        settings=settings,
    )

    if not results:
        return {
            "query": query,
            "context_chunks": [],
            "context_text": "",
            "rag_prompt": f"Question: {query}\n\nNo relevant report sections found. Answer based on general knowledge or state that the information is not available in the indexed reports.",
        }

    context_parts = []
    for i, r in enumerate(results, 1):
        content = r["content"]
        meta = r.get("metadata", {})
        src = f"[Source: {meta.get('company_name', 'Unknown')} - {meta.get('report_year', '')} - Chunk {meta.get('chunk_index', i)}]"
        context_parts.append(f"{src}\n{content}")

    context_text = "\n\n---\n\n".join(context_parts)
    rag_prompt = f"""Use the following context from financial reports to answer the question. If the context does not contain relevant information, say so.

CONTEXT:
{context_text}

QUESTION: {query}

Provide a concise, factual answer based on the context above."""

    return {
        "query": query,
        "context_chunks": results,
        "context_text": context_text,
        "rag_prompt": rag_prompt,
        "chunks_retrieved": len(results),
    }


def get_collection_stats(settings: Optional[Settings] = None) -> dict[str, Any]:
    """Get collection statistics for monitoring scalability."""
    from app.config import get_settings

    settings = settings or get_settings()
    try:
        client = _get_chroma_client(settings)
        collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            embedding_function=_get_embedding_function(settings),
        )
        count = collection.count()
        return {
            "collection": settings.chroma_collection,
            "total_chunks": count,
            "persist_dir": str(settings.chroma_persist_dir),
        }
    except Exception as e:
        logger.warning("Failed to get collection stats: %s", e)
        return {"collection": settings.chroma_collection, "total_chunks": 0, "error": str(e)}
