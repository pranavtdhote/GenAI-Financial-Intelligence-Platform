"""Financial Structuring Engine - Extract metrics, sections, ratios with validation."""

import re
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Lazy load spaCy to avoid startup cost when not used
_nlp = None


def _get_spacy_nlp():
    """Lazy load spaCy model. Falls back to None if unavailable."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy

        _nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.warning("spaCy model not available, NER disabled: %s", e)
        _nlp = False  # Mark as tried
    return _nlp if _nlp else None


# ─── Monetary Value Normalization ────────────────────────────────────────────

# Patterns for monetary values: $1.5M, ($1,234), 1,500,000, 1.5 billion
_MONEY_PATTERNS = [
    # ($1,234,567) or (1,234) - parentheses = negative
    (r"\(\s*[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*\)", -1),
    # $1.5M, $1.5 million, $1.5B, $1,234,567
    (r"[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*(million|millions|mn|m)\b", 1_000_000),
    (r"[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*(billion|billions|bn|b)\b", 1_000_000_000),
    (r"[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*(thousand|thousands|k)\b", 1_000),
    (r"[\$€£]\s*([\d,]+(?:\.\d+)?)(?:\s|$|[,\)])", 1),  # Raw dollar amount
    (r"([\d,]+(?:\.\d+)?)\s*(million|millions|mn|m)\b", 1_000_000),
    (r"([\d,]+(?:\.\d+)?)\s*(billion|billions|bn|b)\b", 1_000_000_000),
    (r"([\d,]+(?:\.\d+)?)\s*(thousand|thousands|k)\b", 1_000),
]


def normalize_monetary_value(text: str) -> Optional[float]:
    """
    Parse and normalize monetary string to float.
    Handles: $1.5M, ($1,234), 1,500,000, 1.5 billion
    """
    if not text or not isinstance(text, str):
        return None
    text = str(text).strip()
    text = text.replace(",", "")

    for pattern, multiplier in _MONEY_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                num = float(m.group(1).replace(",", ""))
                return num * multiplier if multiplier > 0 else -num
            except (ValueError, TypeError):
                continue

    # Plain number
    m = re.search(r"^-?[\d,]+(?:\.\d+)?$", text)
    if m:
        try:
            return float(text.replace(",", ""))
        except ValueError:
            pass
    return None


def _extract_value_after_label(
    text: str, patterns: list[str], context_window: int = 150
) -> Optional[float]:
    """Find label in text and extract monetary value from context AFTER the label."""
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            # Prefer text after label (avoids capturing preceding values)
            start = m.end()
            end = min(len(text), m.end() + context_window)
            snippet = text[start:end]
            for pattern, mult in _MONEY_PATTERNS:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    try:
                        num_str = match.group(1).replace(",", "")
                        num = float(num_str)
                        result = num * mult if mult > 0 else -num
                        return result
                    except (ValueError, TypeError, IndexError):
                        continue
    return None


def _extract_all_values_after_label(
    text: str, patterns: list[str], context_window: int = 200
) -> list[float]:
    """Extract ALL monetary values found after each occurrence of the label.
    Returns a deduplicated list of values for multi-year support."""
    values: list[float] = []
    seen: set[float] = set()
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            start = m.end()
            end = min(len(text), m.end() + context_window)
            snippet = text[start:end]
            for pattern, mult in _MONEY_PATTERNS:
                for match in re.finditer(pattern, snippet, re.IGNORECASE):
                    try:
                        num_str = match.group(1).replace(",", "")
                        num = float(num_str)
                        result = num * mult if mult > 0 else -num
                        if abs(result) >= 1000 and result not in seen:
                            seen.add(result)
                            values.append(result)
                    except (ValueError, TypeError, IndexError):
                        continue
    return values


# ─── Regex Patterns for Financial Metrics ────────────────────────────────────

_REVENUE_LABELS = [
    r"total\s+revenue",
    r"net\s+revenue",
    r"net\s+sales",
    r"total\s+sales",
    r"revenue",
    r"sales",
    r"total\s+operating\s+revenue",
]

_NET_INCOME_LABELS = [
    r"net\s+income",
    r"net\s+earnings",
    r"net\s+profit",
    r"income\s+from\s+continuing\s+operations",
    r"earnings\s+attributable\s+to\s+shareholders",
    r"profit\s+for\s+the\s+year",
]

_EXPENSES_LABELS = [
    r"total\s+operating\s+expenses",
    r"operating\s+expenses",
    r"total\s+expenses",
    r"cost\s+of\s+revenue",
    r"cost\s+of\s+goods\s+sold",
    r"cogs",
]

_ASSETS_LABELS = [
    r"total\s+assets",
    r"total\s+current\s+assets",
    r"consolidated\s+total\s+assets",
]

_LIABILITIES_LABELS = [
    r"total\s+liabilities",
    r"total\s+current\s+liabilities",
    r"total\s+shareholders?\s*'\s*equity\s*\(deficit\)",  # Can be negative
]

_COGS_LABELS = [
    r"cost\s+of\s+revenue",
    r"cost\s+of\s+goods\s+sold",
    r"cogs",
]


# ─── Section Identification ──────────────────────────────────────────────────

_SECTION_PATTERNS = {
    "risk_factors": [
        r"item\s+1a?\.?\s*risk\s+factors",
        r"risk\s+factors",
        r"principal\s+risks",
    ],
    "md_and_a": [
        r"item\s+7\.?\s*management'?s?\s+discussion\s+and\s+analysis",
        r"management'?s?\s+discussion\s+and\s+analysis",
        r"md\s*&\s*a",
        r"mda",
    ],
    "financial_statements": [
        r"item\s+8\.?\s*financial\s+statements",
        r"consolidated\s+financial\s+statements",
        r"financial\s+statements",
        r"consolidated\s+balance\s+sheets",
        r"consolidated\s+statements\s+of\s+income",
    ],
}


def identify_sections(text: str) -> dict[str, Optional[tuple[int, int]]]:
    """Identify section boundaries (start, end) for Risk Factors, MD&A, Financial Statements."""
    result: dict[str, Optional[tuple[int, int]]] = {
        "risk_factors": None,
        "md_and_a": None,
        "financial_statements": None,
    }
    text_lower = text.lower()
    section_starts: list[tuple[str, int]] = []

    for section, patterns in _SECTION_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text_lower, re.IGNORECASE)
            if m:
                section_starts.append((section, m.start()))
                break

    section_starts.sort(key=lambda x: x[1])

    for i, (section, start) in enumerate(section_starts):
        end = section_starts[i + 1][1] if i + 1 < len(section_starts) else len(text)
        result[section] = (start, end)

    return result


def extract_risk_factors(text: str) -> list[str]:
    """Extract risk factor items from Risk Factors section."""
    sections = identify_sections(text)
    risk_section = sections.get("risk_factors")
    if not risk_section:
        return []

    start, end = risk_section
    chunk = text[start:end]

    risks: list[str] = []
    # Match bullet points or numbered items
    for m in re.finditer(r"(?:^|\n)\s*(?:\d+\.|\•|\*|-)\s*(.+?)(?=\n\s*(?:\d+\.|\•|\*|-|\n\n)|\Z)", chunk, re.DOTALL | re.MULTILINE):
        item = m.group(1).strip()
        if len(item) > 30 and len(item) < 2000:  # Sanity
            risks.append(item[:500])  # Cap length

    if not risks:
        # Fallback: split by double newline
        for para in re.split(r"\n\s*\n", chunk):
            para = para.strip()
            if len(para) > 50 and len(para) < 1500:
                risks.append(para[:500])

    return risks[:50]  # Limit


# ─── Numerical Pattern Detection ─────────────────────────────────────────────

_NUMERIC_PATTERN = re.compile(
    r"(?:[\$€£]\s*)?\(?([\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand|mn|m|bn|b|k)?\)?"
)


def detect_numerical_patterns(text: str) -> list[dict[str, Any]]:
    """Detect monetary and percentage patterns in text."""
    findings: list[dict[str, Any]] = []
    for m in _NUMERIC_PATTERN.finditer(text):
        findings.append({"value": m.group(0), "position": m.start()})
    return findings


# ─── Financial Ratio Calculator ──────────────────────────────────────────────

def calculate_financial_ratios(
    revenue: Optional[float],
    net_income: Optional[float],
    cogs: Optional[float],
    assets: Optional[float],
    liabilities: Optional[float],
) -> dict[str, Optional[float]]:
    """
    Compute key financial ratios.
    All monetary values should be in same units (e.g. millions).
    """
    ratios: dict[str, Optional[float]] = {
        "gross_margin": None,
        "profit_margin": None,
        "return_on_assets": None,
        "debt_to_assets": None,
    }

    if revenue and revenue > 0 and cogs is not None:
        gross_profit = revenue - cogs
        ratios["gross_margin"] = round((gross_profit / revenue) * 100, 2)

    if revenue and revenue > 0 and net_income is not None:
        ratios["profit_margin"] = round((net_income / revenue) * 100, 2)

    if assets and assets > 0 and net_income is not None:
        ratios["return_on_assets"] = round((net_income / assets) * 100, 2)

    if assets and assets > 0 and liabilities is not None and liabilities >= 0:
        ratios["debt_to_assets"] = round((liabilities / assets) * 100, 2)

    return ratios


# ─── NER-based Extraction (spaCy) ────────────────────────────────────────────

def _extract_money_entities_ner(text: str, max_chars: int = 100_000) -> list[dict[str, Any]]:
    """Extract MONEY entities using spaCy NER."""
    nlp = _get_spacy_nlp()
    if not nlp:
        return []

    # Truncate for performance
    text = text[:max_chars]
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            value = normalize_monetary_value(ent.text)
            entities.append({"text": ent.text, "normalized": value})
    return entities


# ─── Table Parsing for Structured Data ───────────────────────────────────────

def _parse_tables_for_metrics(tables: list[list[list[str]]]) -> dict[str, Optional[float]]:
    """
    Parse extracted tables to find revenue, net income, assets, liabilities.
    Tables are list of tables, each table is list of rows (list of cells).
    """
    found: dict[str, Optional[float]] = {
        "revenue": None,
        "net_income": None,
        "expenses": None,
        "assets": None,
        "liabilities": None,
        "cogs": None,
    }

    for table in tables:
        if not table:
            continue
        for row in table[1:] if len(table) > 1 else table:
            if len(row) < 2:
                continue
            label = str(row[0]).lower().strip()
            for key, label_patterns in [
                ("revenue", _REVENUE_LABELS),
                ("net_income", _NET_INCOME_LABELS),
                ("expenses", _EXPENSES_LABELS),
                ("assets", _ASSETS_LABELS),
                ("liabilities", _LIABILITIES_LABELS),
                ("cogs", _COGS_LABELS),
            ]:
                matched = False
                for pat in label_patterns:
                    if re.search(pat.replace(r"\s+", r"\s*"), label):
                        matched = True
                        val = None
                        for cell in row[1:]:
                            v = normalize_monetary_value(str(cell))
                            if v is not None and (found[key] is None or key in ("revenue", "assets", "liabilities")):
                                val = v
                                break
                        if val is not None:
                            found[key] = val
                        break
                if matched:
                    break

    return found


def _parse_tables_all_values(tables: list[list[list[str]]]) -> dict[str, list[float]]:
    """Extract ALL monetary values per metric from all table columns (multi-year)."""
    all_vals: dict[str, list[float]] = {
        "revenue": [], "net_income": [], "expenses": [],
        "assets": [], "liabilities": [], "cogs": [],
    }

    for table in tables:
        if not table:
            continue
        for row in table[1:] if len(table) > 1 else table:
            if len(row) < 2:
                continue
            label = str(row[0]).lower().strip()
            for key, label_patterns in [
                ("revenue", _REVENUE_LABELS),
                ("net_income", _NET_INCOME_LABELS),
                ("expenses", _EXPENSES_LABELS),
                ("assets", _ASSETS_LABELS),
                ("liabilities", _LIABILITIES_LABELS),
                ("cogs", _COGS_LABELS),
            ]:
                for pat in label_patterns:
                    if re.search(pat.replace(r"\s+", r"\s*"), label):
                        for cell in row[1:]:
                            v = normalize_monetary_value(str(cell))
                            if v is not None and v not in all_vals[key]:
                                all_vals[key].append(v)
                        break

    return all_vals


# ─── Growth Indicators ───────────────────────────────────────────────────────

def _extract_growth_indicators(text: str) -> list[dict[str, Any]]:
    """Extract YoY growth, percentage changes, trend mentions."""
    growth: list[dict[str, Any]] = []

    # YoY patterns
    yoy_pat = re.compile(
        r"(?:year[\s\-]over[\s\-]year|yoy|y\/y)\s*[:\s]*([+-]?\d+(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    )
    for m in yoy_pat.finditer(text):
        growth.append({"type": "yoy_growth", "value": m.group(1), "unit": "%"})

    # "increased by X%", "growth of X%"
    inc_pat = re.compile(
        r"(?:increased?|grew|growth|decreased?|declined?)\s+(?:by\s+)?([+-]?\d+(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    )
    for m in inc_pat.finditer(text[:15000]):  # First 15k chars
        growth.append({"type": "change", "value": m.group(1), "unit": "%"})

    return growth[:20]


# ─── Validation Layer ────────────────────────────────────────────────────────

class ValidationResult:
    """Validation result for extracted numbers."""

    def __init__(self):
        self.valid = True
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.valid = False
        self.errors.append(msg)


def validate_extracted_numbers(
    revenue: Optional[float],
    net_income: Optional[float],
    assets: Optional[float],
    liabilities: Optional[float],
    gross_margin: Optional[float],
    profit_margin: Optional[float],
) -> ValidationResult:
    """Validate consistency of extracted financial numbers."""
    v = ValidationResult()

    if revenue is not None and revenue < 0:
        v.add_warning("Revenue is negative (may be intentional)")

    if net_income is not None and revenue is not None and revenue > 0:
        implied_margin = (net_income / revenue) * 100
        if implied_margin > 100:
            v.add_error("Profit margin > 100% suggests extraction error")
        elif implied_margin < -100:
            v.add_warning("Large loss margin - verify extraction")

    if gross_margin is not None and (gross_margin < 0 or gross_margin > 100):
        v.add_warning("Gross margin outside 0-100% range")

    if profit_margin is not None and (profit_margin < -100 or profit_margin > 100):
        v.add_warning("Profit margin outside typical range")

    if assets is not None and assets < 0:
        v.add_warning("Total assets negative")

    if liabilities is not None and liabilities < 0:
        v.add_warning("Liabilities negative (may be net position)")

    if assets is not None and liabilities is not None and assets > 0:
        if liabilities > assets * 2:
            v.add_warning("Liabilities >> Assets - verify units/context")

    return v


# ─── Risk Score (0–100) ──────────────────────────────────────────────────────

def calculate_risk_score(
    liabilities: Optional[float],
    assets: Optional[float],
    profit_margin: Optional[float],
    growth_indicators: list[dict[str, Any]],
    risks: list[str],
    raw_text: str,
) -> int:
    """
    Calculate risk score 0–100 based on:
    - Debt ratio (liabilities/assets): higher = riskier
    - Profit margin trend: low/negative margin or declining = riskier
    - Risk mentions frequency: more risk factors + 'risk' in text = riskier
    """
    score = 0.0
    weights = {"debt_ratio": 0.35, "profit_margin": 0.35, "risk_mentions": 0.30}

    # 1. Debt ratio component (0–35 pts)
    if assets and assets > 0 and liabilities is not None:
        debt_ratio = liabilities / assets
        # 0 = 0 pts, 0.5 = 17.5, 1.0 = 35, >1.0 = 35
        debt_score = min(1.0, debt_ratio) * weights["debt_ratio"] * 100
        score += debt_score

    # 2. Profit margin trend (0–35 pts)
    if profit_margin is not None:
        # Negative margin = max risk; <5% = high; 5–15% = medium; >15% = low
        if profit_margin < 0:
            margin_score = weights["profit_margin"] * 100
        elif profit_margin < 5:
            margin_score = weights["profit_margin"] * 100 * 0.9
        elif profit_margin < 10:
            margin_score = weights["profit_margin"] * 100 * 0.6
        elif profit_margin < 15:
            margin_score = weights["profit_margin"] * 100 * 0.3
        else:
            margin_score = 0
        score += margin_score

        # Adjust for declining trend if growth_indicators has negative change
        for gi in growth_indicators or []:
            try:
                val = float(gi.get("value", 0))
                if val < -5:
                    score += 10  # Bonus risk for declining metrics
                    break
            except (TypeError, ValueError):
                pass

    # 3. Risk mentions frequency (0–30 pts)
    risk_count = len(risks) if isinstance(risks, list) else 0
    word_count = max(1, len((raw_text or "").split()))
    risk_in_text = (raw_text or "").lower().count("risk")
    risk_per_1k = (risk_in_text / word_count) * 1000 if word_count else 0

    # risk_count: 0=0, 5=5, 15=15, 30+=20 pts
    count_score = min(20, risk_count * 0.7)
    # risk_per_1k: 0=0, 2=5, 5+=10 pts
    freq_score = min(10, risk_per_1k * 2)
    score += (count_score + freq_score) * (weights["risk_mentions"] / 0.30)

    return min(100, max(0, round(score)))


# ─── Main Parser ─────────────────────────────────────────────────────────────

def parse_financial_document(
    raw_text: str,
    extracted_tables: Optional[list[list[list[str]]]] = None,
) -> dict[str, Any]:
    """
    Financial Structuring Engine - main entry point.

    Extracts revenue, net income, expenses, assets, liabilities,
    identifies sections (Risk Factors, MD&A, Financial Statements),
    computes ratios, validates numbers, returns structured output.
    """
    raw_text = raw_text or ""
    extracted_tables = extracted_tables or []

    # 1. Extract from tables first (higher confidence)
    table_metrics = _parse_tables_for_metrics(extracted_tables)
    table_all = _parse_tables_all_values(extracted_tables)

    # 2. Regex extraction from text (fallback/supplement)
    revenue = table_metrics["revenue"] or _extract_value_after_label(
        raw_text, _REVENUE_LABELS
    )
    net_income = table_metrics["net_income"] or _extract_value_after_label(
        raw_text, _NET_INCOME_LABELS
    )
    expenses = table_metrics["expenses"] or _extract_value_after_label(
        raw_text, _EXPENSES_LABELS
    )
    assets = table_metrics["assets"] or _extract_value_after_label(
        raw_text, _ASSETS_LABELS
    )
    liabilities = table_metrics["liabilities"] or _extract_value_after_label(
        raw_text, _LIABILITIES_LABELS
    )
    cogs = table_metrics["cogs"] or _extract_value_after_label(
        raw_text, _COGS_LABELS
    )

    # 2b. Collect ALL values per metric for hallucination guard (multi-year support)
    all_values: dict[str, list[float]] = {}
    for key, labels in [
        ("revenue", _REVENUE_LABELS),
        ("net_income", _NET_INCOME_LABELS),
        ("expenses", _EXPENSES_LABELS),
        ("assets", _ASSETS_LABELS),
        ("liabilities", _LIABILITIES_LABELS),
    ]:
        vals_set: set[float] = set()
        # From tables (all columns = all years)
        for v in table_all.get(key, []):
            vals_set.add(round(v, 2))
        # From text (all occurrences)
        for v in _extract_all_values_after_label(raw_text, labels):
            vals_set.add(round(v, 2))
        # Include the primary extracted value too
        primary = locals().get(key)
        if primary is not None:
            vals_set.add(round(primary, 2))
        all_values[key] = sorted(vals_set)

    # 3. NER supplement for MONEY entities (reconciliation)
    ner_money = _extract_money_entities_ner(raw_text)
    if ner_money and revenue is None:
        # Use largest positive MONEY as revenue heuristic if missing
        vals = [e["normalized"] for e in ner_money if e["normalized"] and e["normalized"] > 0]
        if vals:
            revenue = max(vals)

    # 4. Calculate ratios
    ratios = calculate_financial_ratios(revenue, net_income, cogs, assets, liabilities)
    gross_margin = ratios["gross_margin"]
    profit_margin = ratios["profit_margin"]

    # 5. Sections and risks
    sections = identify_sections(raw_text)
    risks = extract_risk_factors(raw_text)

    # 6. Growth indicators
    growth_indicators = _extract_growth_indicators(raw_text)

    # 7. Risk score (0–100)
    risk_score_val = calculate_risk_score(
        liabilities=liabilities,
        assets=assets,
        profit_margin=profit_margin,
        growth_indicators=growth_indicators,
        risks=risks,
        raw_text=raw_text,
    )

    # 8. Validation
    validation = validate_extracted_numbers(
        revenue, net_income, assets, liabilities, gross_margin, profit_margin
    )

    # 9. Detect currency from document text
    try:
        from app.services.currency_service import detect_currency
        detected_currency = detect_currency(raw_text)
    except Exception:
        detected_currency = "USD"

    return {
        "revenue": round(revenue, 2) if revenue is not None else None,
        "net_income": round(net_income, 2) if net_income is not None else None,
        "gross_margin": gross_margin,
        "profit_margin": profit_margin,
        "liabilities": round(liabilities, 2) if liabilities is not None else None,
        "assets": round(assets, 2) if assets is not None else None,
        "expenses": round(expenses, 2) if expenses is not None else None,
        "risks": risks,
        "growth_indicators": growth_indicators,
        "sections": {
            k: {"start": v[0], "end": v[1]} if v else None
            for k, v in sections.items()
        },
        "validation": {
            "valid": validation.valid,
            "warnings": validation.warnings,
            "errors": validation.errors,
        },
        "ner_money_count": len(ner_money),
        "risk_score": risk_score_val,
        "all_values": all_values,
        "detected_currency": detected_currency,
    }
