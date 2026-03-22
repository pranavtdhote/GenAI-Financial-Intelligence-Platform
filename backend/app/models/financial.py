"""Financial structuring response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class FinancialAnalysisRequest(BaseModel):
    """Request body for financial analysis."""

    raw_text: str = Field(default="", description="Extracted text from document")
    extracted_tables: list[Any] = Field(
        default_factory=list,
        description="List of extracted tables",
    )

    @field_validator("extracted_tables", mode="before")
    @classmethod
    def sanitize_tables(cls, v: Any) -> list:
        """Ensure extracted_tables never crashes on None/bad cell types."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []

        cleaned = []
        for table in v:
            if table is None:
                continue
            if not isinstance(table, list):
                continue
            clean_table = []
            for row in table:
                if row is None:
                    continue
                if not isinstance(row, list):
                    continue
                clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                clean_table.append(clean_row)
            if clean_table:
                cleaned.append(clean_table)
        return cleaned

    @field_validator("raw_text", mode="before")
    @classmethod
    def ensure_text_string(cls, v: Any) -> str:
        """Ensure raw_text is always a string."""
        if v is None:
            return ""
        return str(v)


class ValidationInfo(BaseModel):
    """Validation result for extracted numbers."""

    valid: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FinancialAnalysisResponse(BaseModel):
    """Structured output from Financial Structuring Engine."""

    revenue: Optional[float] = Field(None, description="Total revenue")
    net_income: Optional[float] = Field(None, description="Net income")
    gross_margin: Optional[float] = Field(None, description="Gross margin %")
    profit_margin: Optional[float] = Field(None, description="Profit margin %")
    liabilities: Optional[float] = Field(None, description="Total liabilities")
    assets: Optional[float] = Field(None, description="Total assets")
    expenses: Optional[float] = Field(None, description="Total expenses")
    risks: list[str] = Field(default_factory=list, description="Risk factors")
    risk_score: Optional[int] = Field(None, ge=0, le=100, description="Risk score 0-100")
    growth_indicators: list[dict[str, Any]] = Field(
        default_factory=list,
        description="YoY growth, percentage changes",
    )
    sections: Optional[dict[str, Any]] = Field(None, description="Section boundaries")
    validation: Optional[ValidationInfo] = Field(None, description="Validation result")
    ner_money_count: Optional[int] = Field(None, description="MONEY entities found by NER")
    detected_currency: Optional[str] = Field(None, description="Detected currency code")
    all_values: Optional[dict[str, Any]] = Field(None, description="All extracted multi-year values")
