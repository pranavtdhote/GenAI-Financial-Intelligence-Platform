"""Financial Trend Comparison Engine - Pydantic models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FinancialRecord(BaseModel):
    """Single year/period financial record for trend comparison."""

    year: Optional[int] = Field(None, description="Fiscal year (e.g., 2023)")
    period: Optional[str] = Field(None, description="Period label if not year")
    report_year: Optional[str] = Field(None, description="Report year as string")
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    expenses: Optional[float] = None
    gross_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    risks: Optional[list[str]] = Field(None, description="Risk items for risk trend")


class TrendCompareRequest(BaseModel):
    """Request body for trend comparison."""

    financial_records: list[dict[str, Any]] = Field(
        ...,
        description="List of structured financial JSON objects (year + metrics per record)",
        min_length=1,
    )


class AnomalyFlag(BaseModel):
    """Single anomaly from rule-based detection."""

    rule_id: str
    rule_name: str
    severity: str = Field(..., description="high | medium | low")
    year: Optional[int] = None
    prior_year: Optional[int] = None
    explanation: str
    data: dict[str, Any] = Field(default_factory=dict)


class GrowthAnalysis(BaseModel):
    """Growth analysis output."""

    period: Optional[dict[str, Any]] = None
    cagr_revenue_pct: Optional[float] = None
    cagr_net_income_pct: Optional[float] = None
    revenue_start: Optional[float] = None
    revenue_end: Optional[float] = None
    net_income_start: Optional[float] = None
    net_income_end: Optional[float] = None
    year_over_year: list[dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class VisualData(BaseModel):
    """Chart-ready visual data."""

    labels: list[str] = Field(default_factory=list)
    series: dict[str, Any] = Field(default_factory=dict)
    growth_series: Optional[dict[str, Any]] = None
    growth_labels: Optional[list[str]] = None
    risk_trend: Optional[dict[str, Any]] = None


class TrendCompareResponse(BaseModel):
    """Structured output from Financial Trend Comparison Engine."""

    growth_analysis: dict[str, Any] = Field(...)
    anomaly_flags: list[dict[str, Any]] = Field(default_factory=list)
    trend_summary: str = Field(...)
    year_over_year_change: list[dict[str, Any]] = Field(default_factory=list)
    visual_data: dict[str, Any] = Field(default_factory=dict)
