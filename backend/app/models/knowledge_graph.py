"""Knowledge Graph Engine - Pydantic models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Node in the knowledge graph."""

    id: str
    type: str = Field(..., description="Company | Revenue | Risk | Regulation | Assets | Market")
    label: str
    data: Optional[dict[str, Any]] = None


class GraphEdge(BaseModel):
    """Edge in the knowledge graph."""

    source: str
    target: str
    type: str = Field(
        ...,
        description="has_revenue | exposed_to_risk | regulated_by | competes_with",
    )


class KnowledgeGraphRequest(BaseModel):
    """Request body for knowledge graph build."""

    llm_output: dict[str, Any] = Field(
        default_factory=dict,
        description="LLM analysis output (executive_summary, risk_analysis, red_flags, etc.)",
    )
    company_name: Optional[str] = None
    financial_data: Optional[dict[str, Any]] = Field(
        None,
        description="Extracted financial data (revenue, assets, risks)",
    )


class KnowledgeGraphResponse(BaseModel):
    """Graph JSON for frontend visualization."""

    nodes: list[dict[str, Any]] = Field(
        ...,
        description="Graph nodes (id, type, label, data)",
    )
    edges: list[dict[str, Any]] = Field(
        ...,
        description="Graph edges (source, target, type)",
    )
    stats: dict[str, int] = Field(
        default_factory=dict,
        description="node_count, edge_count",
    )
