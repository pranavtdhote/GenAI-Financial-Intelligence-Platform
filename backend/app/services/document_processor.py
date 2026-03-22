"""Financial Document Processing Layer - PDF text extraction, OCR, tables, metadata.

Production-ready pipeline with multi-engine fallback, table sanitization,
and fault-tolerant processing. Every stage is wrapped in try-catch to ensure
partial results are always returned.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pymupdf
from PIL import Image

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Default executor for CPU-bound work (avoids blocking async event loop)
_default_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="docproc")


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass


# ──────────────────────────────────────────────────────────────
# Table Sanitization
# ──────────────────────────────────────────────────────────────

def _sanitize_table(table: list[list[Any]]) -> list[list[str]]:
    """
    Sanitize a single table: convert every cell to string, replace None with "".
    Strips whitespace. This prevents Pydantic validation crashes.
    """
    sanitized: list[list[str]] = []
    for row in table:
        if row is None:
            continue
        clean_row: list[str] = []
        for cell in row:
            if cell is None:
                clean_row.append("")
            else:
                clean_row.append(str(cell).strip())
        sanitized.append(clean_row)
    return sanitized


def _sanitize_all_tables(tables: list[Any]) -> list[list[list[str]]]:
    """
    Sanitize all extracted tables. Removes empty tables.
    Returns clean list[list[list[str]]] safe for Pydantic.
    """
    cleaned: list[list[list[str]]] = []
    empty_count = 0

    for table in tables:
        if table is None:
            empty_count += 1
            continue
        sanitized = _sanitize_table(table)
        # Skip tables that are empty or have only headers with no data
        if len(sanitized) <= 1:
            empty_count += 1
            continue
        # Skip tables where all cells are empty strings
        has_data = any(any(cell for cell in row) for row in sanitized)
        if not has_data:
            empty_count += 1
            continue
        cleaned.append(sanitized)

    if empty_count > 0:
        logger.debug("Table sanitization: skipped %d empty/null tables", empty_count)

    return cleaned


# ──────────────────────────────────────────────────────────────
# PDF Type Detection
# ──────────────────────────────────────────────────────────────

def _is_pdf_scanned(doc: pymupdf.Document, settings: Settings) -> bool:
    """
    Detect if PDF is scanned (image-based) vs digital (text-based).
    Uses text density per page - scanned PDFs have minimal/no extractable text.
    """
    total_chars = 0
    page_count = 0

    for page_num in range(min(doc.page_count, 5)):  # Sample first 5 pages
        page = doc[page_num]
        text = page.get_text()
        total_chars += len(text.strip())
        page_count += 1

    if page_count == 0:
        return True  # No pages → treat as scanned

    avg_chars_per_page = total_chars / page_count
    is_scanned = avg_chars_per_page < settings.scanned_text_threshold
    logger.debug(
        "PDF type detection: avg_chars=%.0f threshold=%d is_scanned=%s",
        avg_chars_per_page,
        settings.scanned_text_threshold,
        is_scanned,
    )
    return is_scanned


# ──────────────────────────────────────────────────────────────
# Text Extraction (Multi-Engine)
# ──────────────────────────────────────────────────────────────

def _extract_text_digital(doc: pymupdf.Document) -> str:
    """Extract text directly from digital PDF using PyMuPDF."""
    chunks = []
    for page_num in range(doc.page_count):
        try:
            page = doc[page_num]
            text = page.get_text()
            if text:
                chunks.append(text)
        except Exception as e:
            logger.warning("Text extraction failed for page %d: %s", page_num, e)
    return "\n\n".join(chunks)


def _extract_text_ocr(doc: pymupdf.Document, settings: Settings) -> str:
    """Extract text from scanned PDF using Tesseract OCR with preprocessing."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        logger.warning("Tesseract OCR not available — falling back to digital extraction")
        return _extract_text_digital(doc)

    import pytesseract

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    chunks = []
    for page_num in range(doc.page_count):
        try:
            page = doc[page_num]
            # Render page to image for OCR at configured DPI
            mat = pymupdf.Matrix(settings.ocr_dpi / 72, settings.ocr_dpi / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Preprocess: convert to grayscale for better OCR accuracy
            img = img.convert("L")

            text = pytesseract.image_to_string(img, lang="eng")
            if text:
                chunks.append(text)
        except Exception as e:
            logger.warning("OCR failed for page %d: %s", page_num, e)

    if not chunks:
        logger.warning("OCR produced no text — falling back to digital extraction")
        return _extract_text_digital(doc)

    return "\n\n".join(chunks)


# ──────────────────────────────────────────────────────────────
# Text Cleaning
# ──────────────────────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    """
    Text cleaning pipeline: normalize whitespace, remove control chars,
    fix common OCR artifacts.
    """
    if not raw:
        return ""

    # Remove null bytes and other control characters
    text = "".join(c for c in raw if ord(c) >= 32 or c in "\n\t")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces within lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    # Remove empty lines at start/end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Table Extraction (Multi-Engine with Fallback)
# ──────────────────────────────────────────────────────────────

def _extract_tables_pymupdf(doc: pymupdf.Document) -> list[list[list[Any]]]:
    """Extract tables from PDF using PyMuPDF find_tables (primary engine)."""
    all_tables: list[list[list[Any]]] = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        try:
            tabs = page.find_tables()
            for tab in tabs.tables:
                rows = tab.extract()
                if rows:
                    all_tables.append(rows)
        except Exception as e:
            logger.debug("PyMuPDF table extraction failed for page %d: %s", page_num, e)

    return all_tables


def _extract_tables_pdfplumber(file_path: Path) -> list[list[list[Any]]]:
    """Extract tables using pdfplumber as fallback engine."""
    try:
        import pdfplumber
    except ImportError:
        logger.debug("pdfplumber not installed — skipping fallback table extraction")
        return []

    all_tables: list[list[list[Any]]] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if table:
                                all_tables.append(table)
                except Exception as e:
                    logger.debug("pdfplumber table extraction failed for a page: %s", e)
    except Exception as e:
        logger.warning("pdfplumber failed to open PDF: %s", e)

    return all_tables


def _extract_financial_values_regex(text: str) -> list[list[list[str]]]:
    """
    Last-resort fallback: extract financial values from text using regex patterns
    and construct a pseudo-table from them.
    """
    patterns = [
        (r"(?:Total\s+)?Revenue[s]?\s*[\:|\—|\-]?\s*[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b|cr|crore)?", "Revenue"),
        (r"Net\s+Income\s*[\:|\—|\-]?\s*[\$€£₹]?\s*\(?\s*([\d,]+(?:\.\d+)?)\s*\)?\s*(million|billion|mn|m|bn|b|cr|crore)?", "Net Income"),
        (r"(?:Total\s+)?Assets?\s*[\:|\—|\-]?\s*[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b|cr|crore)?", "Total Assets"),
        (r"(?:Total\s+)?Liabilit(?:y|ies)\s*[\:|\—|\-]?\s*[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b|cr|crore)?", "Total Liabilities"),
        (r"(?:Operating\s+)?Expens(?:e|es)\s*[\:|\—|\-]?\s*[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b|cr|crore)?", "Operating Expenses"),
        (r"Gross\s+(?:Profit|Margin)\s*[\:|\—|\-]?\s*[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(%|percent|million|billion|mn|m|bn|b)?", "Gross Profit"),
    ]

    rows: list[list[str]] = [["Metric", "Value", "Unit"]]
    for pattern, label in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "")
            unit = (match.group(2) or "").strip()
            rows.append([label, value, unit])

    if len(rows) <= 1:
        return []  # No financial values found

    logger.info("Regex fallback extracted %d financial values from text", len(rows) - 1)
    return [rows]


# ──────────────────────────────────────────────────────────────
# Metadata Extraction
# ──────────────────────────────────────────────────────────────

def _extract_metadata(raw_text: str) -> dict[str, Any]:
    """
    Extract metadata from raw text: company name, report year, report type.
    Uses heuristics and common financial report patterns.
    """
    metadata: dict[str, Any] = {
        "company_name": None,
        "report_year": None,
        "report_type": None,
        "page_count": None,
    }

    if not raw_text:
        return metadata

    lines = raw_text.split("\n")
    first_500 = " ".join(lines[:20])[:500]

    # Report year
    year_patterns = [
        (r"(?:year\s+ended\s+[^,]+,\s*)(20\d{2})", 1),
        (r"(?:FY|fiscal\s+year)\s*(20\d{2})", 1),
        (r"(?:annual\s+report\s+)(20\d{2})", 1),
        (r"\b(20\d{2})\b", 1),
    ]
    for pat, group in year_patterns:
        m = re.search(pat, first_500, re.IGNORECASE)
        if m:
            metadata["report_year"] = m.group(group)
            break

    # Report type
    report_type_keywords = [
        ("annual report", "Annual Report"),
        ("quarterly report", "Quarterly Report"),
        ("10-k", "10-K"),
        ("10-q", "10-Q"),
        ("financial statement", "Financial Statement"),
        ("earnings release", "Earnings Release"),
        ("investor presentation", "Investor Presentation"),
    ]
    text_lower = raw_text[:5000].lower()
    for keyword, label in report_type_keywords:
        if keyword in text_lower:
            metadata["report_type"] = label
            break

    # Company name
    company_patterns = [
        r"(?:annual\s+report\s+of)\s+([^\n]+)",
        r"(?:^|\n)\s*([A-Z][A-Za-z0-9\s&.,\-]+(?:Inc|Ltd|LLC|Corp|Corporation)\.?)\s*(?:\n|$)",
        r"(?:^|\n)\s*([A-Z][A-Za-z0-9\s&.,\-]{5,50})\s*(?:\n|$)",
    ]
    for pat in company_patterns:
        m = re.search(pat, first_500, re.MULTILINE)
        if m:
            name = m.group(1).strip()
            if 3 < len(name) < 100:
                metadata["company_name"] = name
                break

    # Fallback: first substantial line
    if not metadata["company_name"]:
        for line in lines[:10]:
            line = line.strip()
            if 5 < len(line) < 80 and line[0].isupper():
                metadata["company_name"] = line
                break

    return metadata


# ──────────────────────────────────────────────────────────────
# Main Processing Pipeline
# ──────────────────────────────────────────────────────────────

def process_pdf_sync(file_path: Path, settings: Settings) -> dict[str, Any]:
    """
    Synchronous pipeline for PDF processing.
    Run in thread pool from async context to avoid blocking.

    Pipeline:
    1. Detect if PDF is scanned
    2. If digital → extract text directly (PyMuPDF)
    3. If scanned → apply OCR (Tesseract) with fallback to digital
    4. Extract tables (PyMuPDF → pdfplumber → regex fallback)
    5. Sanitize all tables (None → "", type coercion)
    6. Clean text
    7. Extract metadata

    Every stage is fault-tolerant: if one fails, the pipeline continues.
    """
    if not file_path.exists():
        raise DocumentProcessingError(f"File not found: {file_path}")

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise DocumentProcessingError(f"Failed to open PDF: {e}") from e

    # Pipeline status flags
    status = {
        "document_processed": False,
        "text_extracted": False,
        "tables_extracted": False,
        "tables_count": 0,
        "fallback_used": None,
        "ocr_used": False,
    }

    raw_text = ""
    extracted_tables: list[list[list[str]]] = []
    is_scanned = False

    try:
        # ── Stage 1: Detect PDF type ──────────────────────
        try:
            is_scanned = _is_pdf_scanned(doc, settings)
            status["ocr_used"] = is_scanned
        except Exception as e:
            logger.warning("PDF type detection failed (assuming digital): %s", e)
            is_scanned = False

        # ── Stage 2 & 3: Extract text ─────────────────────
        try:
            if is_scanned:
                logger.info("Processing scanned PDF with OCR: %s", file_path.name)
                raw_text = _extract_text_ocr(doc, settings)
            else:
                logger.info("Processing digital PDF: %s", file_path.name)
                raw_text = _extract_text_digital(doc)
            status["text_extracted"] = bool(raw_text and len(raw_text.strip()) > 10)
        except Exception as e:
            logger.error("Text extraction failed: %s", e)
            # Try the other method as fallback
            try:
                raw_text = _extract_text_digital(doc) if is_scanned else ""
                status["text_extracted"] = bool(raw_text)
                status["fallback_used"] = "digital_text_fallback"
            except Exception:
                raw_text = ""

        # ── Stage 4: Extract tables (multi-engine) ────────
        try:
            raw_tables = _extract_tables_pymupdf(doc)
            if raw_tables:
                extracted_tables = _sanitize_all_tables(raw_tables)
                status["fallback_used"] = status["fallback_used"] or "none"
                logger.info("PyMuPDF extracted %d tables", len(extracted_tables))
        except Exception as e:
            logger.warning("PyMuPDF table extraction failed: %s", e)

        # Fallback 1: pdfplumber
        if not extracted_tables:
            try:
                raw_tables = _extract_tables_pdfplumber(file_path)
                if raw_tables:
                    extracted_tables = _sanitize_all_tables(raw_tables)
                    status["fallback_used"] = "pdfplumber"
                    logger.info("pdfplumber fallback extracted %d tables", len(extracted_tables))
            except Exception as e:
                logger.debug("pdfplumber fallback failed: %s", e)

        # Fallback 2: regex extraction from text
        if not extracted_tables and raw_text:
            try:
                regex_tables = _extract_financial_values_regex(raw_text)
                if regex_tables:
                    extracted_tables = _sanitize_all_tables(regex_tables)
                    status["fallback_used"] = "regex"
                    logger.info("Regex fallback extracted %d pseudo-tables", len(extracted_tables))
            except Exception as e:
                logger.debug("Regex table fallback failed: %s", e)

        status["tables_extracted"] = len(extracted_tables) > 0
        status["tables_count"] = len(extracted_tables)

        # ── Stage 5: Clean text ───────────────────────────
        try:
            cleaned_text = _clean_text(raw_text)
        except Exception as e:
            logger.warning("Text cleaning failed: %s", e)
            cleaned_text = raw_text  # Use raw text as fallback

        # ── Stage 6: Extract metadata ─────────────────────
        try:
            metadata = _extract_metadata(cleaned_text)
        except Exception as e:
            logger.warning("Metadata extraction failed: %s", e)
            metadata = {"company_name": None, "report_year": None, "report_type": None}

        metadata["page_count"] = doc.page_count
        metadata["is_scanned"] = is_scanned
        metadata["source_file"] = file_path.name
        metadata["pipeline_status"] = status

        status["document_processed"] = True

        logger.info(
            "Document processing complete: file=%s pages=%d text_len=%d tables=%d scanned=%s fallback=%s",
            file_path.name,
            doc.page_count,
            len(cleaned_text),
            len(extracted_tables),
            is_scanned,
            status["fallback_used"],
        )

        return {
            "company_name": metadata.get("company_name"),
            "report_year": metadata.get("report_year"),
            "raw_text": cleaned_text,
            "extracted_tables": extracted_tables,
            "metadata": metadata,
        }
    finally:
        doc.close()


async def process_pdf(
    file_path: Path,
    settings: Settings,
    executor: ThreadPoolExecutor | None = None,
) -> dict[str, Any]:
    """
    Async wrapper for PDF processing. Offloads CPU-bound work to thread pool.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    exec_ = executor or _default_executor
    return await loop.run_in_executor(
        exec_,
        process_pdf_sync,
        file_path,
        settings,
    )
