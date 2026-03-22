"""Knowledge Graph Engine - API routes."""

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.knowledge_graph import (
    KnowledgeGraphRequest,
    KnowledgeGraphResponse,
)
from app.services.knowledge_graph import build_financial_knowledge_graph

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.post(
    "/build",
    response_model=KnowledgeGraphResponse,
    summary="Build Financial Knowledge Graph",
    description=(
        "Extract entities from LLM output. Construct dynamic financial graph. "
        "Nodes: Company, Revenue, Risk, Regulation, Assets, Market. "
        "Edges: has_revenue, exposed_to_risk, regulated_by, competes_with. "
        "Returns graph JSON for frontend visualization."
    ),
)
async def build_graph(body: KnowledgeGraphRequest) -> KnowledgeGraphResponse:
    """
    Knowledge Graph Engine endpoint.
    Explains how insights were derived and shows relationships between financial indicators.
    """
    try:
        result = build_financial_knowledge_graph(
            llm_output=body.llm_output,
            company_name=body.company_name,
            financial_data=body.financial_data,
        )
        return KnowledgeGraphResponse(**result)
    except Exception as e:
        logger.exception("Knowledge graph build failed")
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge graph build failed: {str(e)}",
        ) from e
