"""GenAI Intelligence Layer - API routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.llm import ComplianceInfo, HallucinationCheck, InvestorSlide, LLMAnalysisRequest, LLMAnalysisResponse
from app.services.llm_engine import NumericalMismatchError, generate_financial_analysis

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post(
    "/analyze",
    response_model=LLMAnalysisResponse,
    summary="GenAI Financial Analysis",
    description=(
        "Generate Executive Summary, Financial Overview, Risk Analysis, "
        "Trend Detection, Investment Recommendation, Red Flags, Confidence Score. "
        "Uses temperature 0.2 for reliability. Applies hallucination guard with auto-correction."
    ),
    responses={
        400: {"description": "GROQ_API_KEY not configured"},
        500: {"description": "LLM generation failed"},
    },
)
async def genai_financial_analysis(
    body: LLMAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> LLMAnalysisResponse:
    """
    GenAI Intelligence Layer endpoint.
    Accepts raw_text and financial_data (from document + financial parsing).
    Returns structured LLM analysis with hallucination check using Groq API.
    Auto-corrects mismatched values instead of rejecting output.
    """
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=400,
            detail="GROQ_API_KEY not configured. Set it in .env for GenAI analysis.",
        )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: generate_financial_analysis(
                raw_text=body.raw_text,
                financial_data=body.financial_data,
                company_name=body.company_name,
                settings=settings,
            ),
        )

        # Parse hallucination check
        hc = result.get("hallucination_check")
        hallucination_check = None
        if hc:
            hallucination_check = HallucinationCheck(
                has_inconsistency=hc.get("has_inconsistency", False),
                inconsistencies=hc.get("inconsistencies", []),
                corrections=hc.get("corrections", []),
                checked=hc.get("checked", True),
            )

        # Parse investor slides
        raw_slides = result.get("investor_slides") or []
        investor_slides = []
        for s in raw_slides:
            if isinstance(s, dict):
                investor_slides.append(InvestorSlide(
                    title=s.get("title", ""),
                    bullets=s.get("bullets", []),
                ))

        # Parse compliance
        raw_compliance = result.get("compliance")
        compliance = None
        if isinstance(raw_compliance, dict):
            compliance = ComplianceInfo(
                ifrs_mentioned=raw_compliance.get("ifrs_mentioned", False),
                gaap_mentioned=raw_compliance.get("gaap_mentioned", False),
                esg_mentioned=raw_compliance.get("esg_mentioned", False),
                standard_notes=raw_compliance.get("standard_notes"),
            )

        return LLMAnalysisResponse(
            executive_summary=result.get("executive_summary"),
            financial_performance_overview=result.get("financial_performance_overview"),
            risk_analysis=result.get("risk_analysis"),
            trend_detection=result.get("trend_detection"),
            investment_recommendation=result.get("investment_recommendation"),
            red_flags=result.get("red_flags") or [],
            confidence_score=result.get("confidence_score"),
            investor_slides=investor_slides,
            compliance=compliance,
            hallucination_check=hallucination_check,
            parse_error=result.get("parse_error"),
        )
    except NumericalMismatchError as e:
        # Fail-safe: return partial output with warning instead of 422
        logger.warning("Hallucination guard mismatch (returning partial): %s", e.inconsistencies[:3])
        return LLMAnalysisResponse(
            executive_summary="Analysis completed with data validation warnings. Some numerical values could not be verified against extracted data.",
            financial_performance_overview="Financial data extracted but AI-generated narrative has unverified numerical claims.",
            risk_analysis="Risk analysis may contain unverified figures. Please cross-reference with source document.",
            investment_recommendation="Hold (Pending manual verification of financial figures)",
            red_flags=["Numerical mismatch detected between AI output and extracted data"],
            confidence_score=0.15,
            hallucination_check=HallucinationCheck(
                has_inconsistency=True,
                inconsistencies=e.inconsistencies[:5],
                corrections=[],
                checked=True,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.exception("LLM analysis failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("LLM analysis failed")
        raise HTTPException(
            status_code=500,
            detail="GenAI analysis failed. Please try again.",
        ) from e
