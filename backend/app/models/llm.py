"""GenAI Intelligence Layer - Pydantic models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class LLMAnalysisRequest(BaseModel):
    """Request body for GenAI financial analysis."""

    raw_text: str = Field(..., description="Extracted document text")
    financial_data: dict[str, Any] = Field(
        ...,
        description="Extracted structured financial data (revenue, net_income, etc.)",
    )
    company_name: Optional[str] = Field(None, description="Company name if known")


class HallucinationCheck(BaseModel):
    """Result of hallucination guard check."""

    has_inconsistency: bool = False
    inconsistencies: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    checked: bool = True


class InvestorSlide(BaseModel):
    """Single investor slide."""
    title: str = ""
    bullets: list[str] = Field(default_factory=list)


class ComplianceInfo(BaseModel):
    """Compliance check result."""
    ifrs_mentioned: bool = False
    gaap_mentioned: bool = False
    esg_mentioned: bool = False
    standard_notes: Optional[str] = None


class LLMAnalysisResponse(BaseModel):
    """Structured output from GenAI Intelligence Layer."""

    executive_summary: Optional[str] = None
    financial_performance_overview: Optional[str] = None
    risk_analysis: Optional[str] = None
    trend_detection: Optional[str] = None
    investment_recommendation: Optional[str] = None
    red_flags: list[str] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    investor_slides: list[InvestorSlide] = Field(default_factory=list)
    compliance: Optional[ComplianceInfo] = None
    hallucination_check: Optional[HallucinationCheck] = None
    parse_error: Optional[str] = None
