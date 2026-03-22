"""Document processing response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """Extracted document metadata."""

    company_name: Optional[str] = None
    report_year: Optional[str] = None
    report_type: Optional[str] = None
    page_count: Optional[int] = None
    is_scanned: Optional[bool] = None
    source_file: Optional[str] = None


class DocumentProcessResponse(BaseModel):
    """Structured response from document processing pipeline."""

    company_name: Optional[str] = Field(None, description="Extracted company name")
    report_year: Optional[str] = Field(None, description="Report fiscal year")
    raw_text: str = Field(default="", description="Cleaned extracted text")
    extracted_tables: list[Any] = Field(
        default_factory=list,
        description="List of tables, each table is list of rows (list of cell strings)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (page_count, is_scanned, report_type, etc.)",
    )

    @field_validator("extracted_tables", mode="before")
    @classmethod
    def sanitize_tables(cls, v: Any) -> list:
        """Ensure extracted_tables is always a clean list — never crashes on None/bad types."""
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
                # Convert every cell to string, None → ""
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
