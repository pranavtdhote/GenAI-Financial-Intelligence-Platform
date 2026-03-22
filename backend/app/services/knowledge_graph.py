"""Knowledge Graph Engine - Financial entities and relationships using NetworkX."""

import re
from typing import Any, Optional

import networkx as nx

from app.core.logging import get_logger

logger = get_logger(__name__)

# Node types and edge types
NODE_TYPES = frozenset({"Company", "Revenue", "Risk", "Regulation", "Assets", "Market"})
EDGE_TYPES = frozenset({"has_revenue", "exposed_to_risk", "regulated_by", "competes_with"})

# Patterns for entity extraction from text
_COMPANY_PATTERNS = [
    r"\b([A-Z][A-Za-z0-9\s&.,\-]+(?:Inc|Ltd|LLC|Corp|Corporation|Co)\.?)\b",
    r"\b([A-Z][A-Za-z0-9\s&.,\-]{4,40})\s+(?:reported|announced|disclosed)\b",
]
_RISK_PATTERNS = [
    r"(?:risk[s]?\s+(?:of|related\s+to|regarding)\s+)([^.,;]+)",
    r"(?:exposure\s+to\s+)([^.,;]+)",
    r"(?:principal\s+risks?\s*:?\s*)([^.]{10,80})",
    r"(?:regulatory\s+risk[s]?\s*:?\s*)([^.]{10,80})",
    r"(?:market\s+risk[s]?\s*:?\s*)([^.]{10,80})",
    r"(?:cyber(?:security)?\s+risk[s]?\s*:?\s*)([^.]{10,80})",
]
_REGULATION_PATTERNS = [
    r"\b(SEC|FDA|FTC|GDPR|SOX|CFTC|CISA)\b",
    r"(?:regulated\s+by\s+)([^.,;]+)",
    r"(?:compliance\s+with\s+)([^.,;]+)",
    r"(?:subject\s+to\s+)([^.,;]+regulation[^.,;]*)",
]
_MARKET_PATTERNS = [
    r"(?:market\s+(?:in|for|segment)\s+)([^.,;]{5,50})",
    r"(?:(\w+\s+market)\s+(?:growth|share|segment))",
    r"(?:competes?\s+(?:in|with)\s+)([^.,;]{5,50})",
    r"(?:industry\s+(?:leaders?|players?)\s*:?\s*)([^.,;]{5,80})",
]


def _extract_entities(
    llm_output: dict[str, Any],
    company_name: Optional[str] = None,
    financial_data: Optional[dict[str, Any]] = None,
) -> tuple[list[dict], list[tuple[str, str, str]]]:
    """
    Extract entities and relationships from LLM output and optional structured data.
    Returns (nodes, edges) where nodes have id, type, label, and edges are (source_id, target_id, edge_type).
    """
    combined_text = ""
    if llm_output:
        for v in llm_output.values():
            if isinstance(v, str):
                combined_text += " " + v
            elif isinstance(v, list):
                combined_text += " " + " ".join(str(x) for x in v)

    nodes: list[dict] = []
    edges: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()

    def add_node(node_id: str, node_type: str, label: str, data: Optional[dict] = None):
        if node_id not in seen_ids:
            seen_ids.add(node_id)
            n = {"id": node_id, "type": node_type, "label": label}
            if data:
                n["data"] = data
            nodes.append(n)

    def add_edge(source: str, target: str, edge_type: str):
        if source and target and edge_type in EDGE_TYPES:
            edges.append((source, target, edge_type))

    # 1. Company node (from input or text)
    company_id = "company:main"
    company_label = company_name or "Company"
    if company_name:
        add_node(company_id, "Company", company_label)
    else:
        for pat in _COMPANY_PATTERNS:
            m = re.search(pat, combined_text)
            if m:
                lbl = m.group(1).strip()
                if len(lbl) > 3 and len(lbl) < 80:
                    company_label = lbl
                    add_node(company_id, "Company", company_label)
                    break
        if company_id not in seen_ids:
            add_node(company_id, "Company", "Company")

    # 2. Revenue node (from financial_data or text)
    rev_val = None
    if financial_data and financial_data.get("revenue") is not None:
        rev_val = financial_data["revenue"]
    rev_match = re.search(
        r"[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b)?\b",
        combined_text,
        re.IGNORECASE,
    )
    if rev_match:
        try:
            n = float(rev_match.group(1).replace(",", ""))
            u = (rev_match.group(2) or "").lower()
            if u in ("million", "millions", "mn", "m"):
                rev_val = n * 1_000_000
            elif u in ("billion", "billions", "bn", "b"):
                rev_val = n * 1_000_000_000
            else:
                rev_val = n
        except (ValueError, TypeError):
            pass
    revenue_id = "revenue:main"
    rev_label = f"Revenue ${rev_val:,.0f}" if rev_val else "Revenue"
    add_node(revenue_id, "Revenue", rev_label, {"value": rev_val} if rev_val else None)
    add_edge(company_id, revenue_id, "has_revenue")

    # 3. Risk nodes (from text, red_flags, risks)
    risk_texts = []
    if isinstance(llm_output.get("red_flags"), list):
        risk_texts.extend(llm_output["red_flags"])
    if isinstance(llm_output.get("risk_analysis"), str):
        risk_texts.append(llm_output["risk_analysis"])
    if isinstance(financial_data, dict) and isinstance(financial_data.get("risks"), list):
        risk_texts.extend(financial_data["risks"][:10])

    for i, text in enumerate(risk_texts):
        if not text or len(str(text)) < 10:
            continue
        snippet = str(text)[:100].strip()
        risk_id = f"risk:{i}"
        add_node(risk_id, "Risk", snippet[:60] + ("..." if len(snippet) > 60 else ""), {"snippet": snippet})
        add_edge(company_id, risk_id, "exposed_to_risk")

    for pat in _RISK_PATTERNS:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            snippet = m.group(1).strip()[:80]
            if len(snippet) < 10:
                continue
            risk_id = f"risk:ext_{hash(snippet) % 10**8}"
            if risk_id not in seen_ids:
                add_node(risk_id, "Risk", snippet[:50] + ("..." if len(snippet) > 50 else ""), {"snippet": snippet})
                add_edge(company_id, risk_id, "exposed_to_risk")

    # 4. Regulation nodes
    for pat in _REGULATION_PATTERNS:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            lbl = m.group(1).strip()[:60]
            reg_id = f"regulation:{hash(lbl) % 10**8}"
            if reg_id not in seen_ids:
                add_node(reg_id, "Regulation", lbl)
                add_edge(company_id, reg_id, "regulated_by")

    # 5. Assets node (from financial_data)
    assets_val = None
    if financial_data and financial_data.get("assets") is not None:
        assets_val = financial_data["assets"]
    assets_id = "assets:main"
    assets_label = f"Assets ${assets_val:,.0f}" if assets_val else "Assets"
    add_node(assets_id, "Assets", assets_label, {"value": assets_val} if assets_val else None)

    # 6. Market nodes (competitors, market segments)
    for pat in _MARKET_PATTERNS:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            lbl = m.group(1).strip()[:60]
            if len(lbl) < 5:
                continue
            market_id = f"market:{hash(lbl) % 10**8}"
            if market_id not in seen_ids:
                add_node(market_id, "Market", lbl)
                add_edge(company_id, market_id, "competes_with")

    # Competitor mentions (Company competes_with Company)
    comp_pat = r"(?:competitors?\s*(?:include|are|:)\s*)([^.;]+)"
    for m in re.finditer(comp_pat, combined_text, re.IGNORECASE):
        comps = re.split(r"[,;]", m.group(1))
        for c in comps[:5]:
            c = c.strip()
            if len(c) > 3 and len(c) < 50:
                comp_id = f"company:comp_{hash(c) % 10**8}"
                if comp_id not in seen_ids:
                    add_node(comp_id, "Company", c[:40])
                    add_edge(company_id, comp_id, "competes_with")

    return nodes, edges


def _build_graph(nodes: list[dict], edges: list[tuple[str, str, str]]) -> nx.DiGraph:
    """Build NetworkX directed graph from nodes and edges."""
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(
            n["id"],
            type=n.get("type", ""),
            label=n.get("label", n["id"]),
            **{k: v for k, v in n.items() if k not in ("id", "type", "label")},
        )
    for src, tgt, etype in edges:
        if G.has_node(src) and G.has_node(tgt):
            G.add_edge(src, tgt, type=etype)
    return G


def _graph_to_json(G: nx.DiGraph) -> dict[str, Any]:
    """Convert NetworkX graph to frontend-friendly JSON."""
    nodes_out = []
    for nid, attrs in G.nodes(data=True):
        nodes_out.append({
            "id": nid,
            "type": attrs.get("type", ""),
            "label": attrs.get("label", nid),
            "data": {k: v for k, v in attrs.items() if k not in ("type", "label")},
        })

    edges_out = []
    for src, tgt, attrs in G.edges(data=True):
        edges_out.append({
            "source": src,
            "target": tgt,
            "type": attrs.get("type", ""),
        })

    return {
        "nodes": nodes_out,
        "edges": edges_out,
        "stats": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
        },
    }


def build_financial_knowledge_graph(
    llm_output: Optional[dict[str, Any]] = None,
    company_name: Optional[str] = None,
    financial_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Knowledge Graph Engine - main entry point.

    Extracts entities from LLM output and structured data.
    Constructs dynamic financial graph with Company, Revenue, Risk, Regulation, Assets, Market.
    Returns graph JSON for frontend visualization.
    """
    llm_output = llm_output or {}
    nodes, edges = _extract_entities(llm_output, company_name, financial_data)
    G = _build_graph(nodes, edges)
    return _graph_to_json(G)
