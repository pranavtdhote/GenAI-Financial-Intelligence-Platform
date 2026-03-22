"""Financial analysis API routes."""

from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.models.financial import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    ValidationInfo,
)
from app.services.financial_parser import parse_financial_document

logger = get_logger(__name__)

router = APIRouter(prefix="/financial", tags=["financial"])


@router.post(
    "/analyze",
    response_model=FinancialAnalysisResponse,
    summary="Analyze Financial Document",
    description=(
        "Parse raw text and tables to extract revenue, net income, ratios, "
        "risks, growth indicators. Uses regex, NER (spaCy), and validation."
    ),
)
async def analyze_financial_document(
    body: FinancialAnalysisRequest,
) -> FinancialAnalysisResponse:
    """
    Financial Structuring Engine endpoint.
    Accepts raw_text and extracted_tables (from document processing).
    Returns structured output with validation.
    Always returns partial results — never crashes.
    """
    try:
        result = parse_financial_document(
            raw_text=body.raw_text,
            extracted_tables=body.extracted_tables,
        )

        validation = result.get("validation")
        validation_info = None
        if validation:
            validation_info = ValidationInfo(
                valid=validation.get("valid", True),
                warnings=validation.get("warnings", []),
                errors=validation.get("errors", []),
            )

        return FinancialAnalysisResponse(
            revenue=result.get("revenue"),
            net_income=result.get("net_income"),
            gross_margin=result.get("gross_margin"),
            profit_margin=result.get("profit_margin"),
            liabilities=result.get("liabilities"),
            assets=result.get("assets"),
            expenses=result.get("expenses"),
            risks=result.get("risks", []),
            risk_score=result.get("risk_score"),
            growth_indicators=result.get("growth_indicators", []),
            sections=result.get("sections"),
            validation=validation_info,
            ner_money_count=result.get("ner_money_count"),
            detected_currency=result.get("detected_currency"),
            all_values=result.get("all_values"),
        )
    except Exception as e:
        logger.exception("Financial analysis failed — returning partial results")
        # Return a safe partial response instead of crashing
        return FinancialAnalysisResponse(
            revenue=None,
            net_income=None,
            risks=[f"Analysis error: {type(e).__name__}"],
            risk_score=50,
            validation=ValidationInfo(
                valid=False,
                warnings=[],
                errors=[f"Financial analysis failed: {str(e)}"],
            ),
        )
