"""Financial Trend Comparison Engine - API routes."""

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.trend import TrendCompareRequest, TrendCompareResponse
from app.services.trend_engine import compare_financial_trends

logger = get_logger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])


@router.post(
    "/compare",
    response_model=TrendCompareResponse,
    summary="Compare Financial Trends",
    description=(
        "Compare revenue growth across years, detect anomalies (e.g., revenue up profit down), "
        "compute CAGR, generate growth chart data, risk trend evolution. "
        "Rule-based anomaly detection, explainable and data-driven."
    ),
    responses={400: {"description": "Invalid input"}},
)
async def compare_trends(body: TrendCompareRequest) -> TrendCompareResponse:
    """
    Financial Trend Comparison Engine endpoint.
    Accepts multiple structured financial JSON objects (one per year/period).
    Returns growth_analysis, anomaly_flags, trend_summary, year_over_year_change, visual_data.
    """
    try:
        result = compare_financial_trends(body.financial_records)
        return TrendCompareResponse(**result)
    except Exception as e:
        logger.exception("Trend comparison failed")
        raise HTTPException(
            status_code=500,
            detail=f"Trend comparison failed: {str(e)}",
        ) from e
