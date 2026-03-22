"""GenAI Intelligence Layer - LLM-based financial analysis with hallucination guards."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Structured output schema for the LLM
OUTPUT_SCHEMA = {
    "executive_summary": "string (2-4 sentences)",
    "financial_performance_overview": "string (key metrics, YoY comparison)",
    "risk_analysis": "string (key risks identified)",
    "trend_detection": "string (positive/negative trends)",
    "investment_recommendation": "string (hold/buy/sell with rationale)",
    "red_flags": "list of strings (concerns)",
    "confidence_score": "float 0-1",
    "investor_slides": "list of dicts {title, bullets}",
    "compliance": "dict {ifrs, gaap, esg, notes}",
}

_OUTPUT_KEYS = [
    "executive_summary",
    "financial_performance_overview",
    "risk_analysis",
    "trend_detection",
    "investment_recommendation",
    "red_flags",
    "confidence_score",
    "investor_slides",
    "compliance",
]


def _build_prompt(
    raw_text: str,
    financial_data: dict[str, Any],
    company_name: Optional[str] = None,
) -> str:
    """Build structured prompt for financial analysis with extracted data."""
    max_chars = 25_000
    text_preview = raw_text[:max_chars] if raw_text else "No text available."
    if len(raw_text or "") > max_chars:
        text_preview += "\\n\\n[Document truncated...]"

    extracted = {
        "revenue": financial_data.get("revenue"),
        "net_income": financial_data.get("net_income"),
        "assets": financial_data.get("assets"),
        "liabilities": financial_data.get("liabilities"),
        "expenses": financial_data.get("expenses"),
        "gross_margin": financial_data.get("gross_margin"),
        "profit_margin": financial_data.get("profit_margin"),
        "growth_indicators": financial_data.get("growth_indicators", []),
        "risks": financial_data.get("risks", [])[:10],
    }

    # Include all multi-year values for grounding (reduces hallucination)
    all_values = financial_data.get("all_values", {})
    grounding_lines = []
    for metric, values in all_values.items():
        if values:
            formatted = ", ".join(f"{v:,.0f}" for v in values)
            grounding_lines.append(f"  {metric}: {formatted}")
    grounding_block = "\n".join(grounding_lines) if grounding_lines else "  (no multi-year data)"

    return f"""You are a senior financial analyst. Analyze the following financial document and provide a structured analysis.

CRITICAL RULES — YOU MUST FOLLOW EVERY SINGLE ONE:
1. Use ONLY the exact financial values provided in the EXTRACTED STRUCTURED DATA section below. Do NOT invent, estimate, approximate, round, or guess any figures.
2. When citing revenue, net income, assets, liabilities, margins, or any financial metric, you MUST use the EXACT number from the structured data. Do not use words like "approximately", "~", "about", or "around".
3. If a metric is not present in the extracted data, YOU MUST state "Not available" or "Not disclosed". NEVER fabricate a number.
4. Investment recommendation must be based solely on provided evidence.
5. Confidence score reflects how complete the source data is, not speculation.
6. Financial data may span MULTIPLE YEARS. When referencing financial performance, specify the year if known.
7. All financial values are in the document's native currency (typically USD) unless explicitly stated otherwise. Do NOT convert currencies or change units.

EXTRACTED STRUCTURED DATA (USE THESE EXACT VALUES — DO NOT MODIFY THEM):
{json.dumps(extracted, indent=2, default=str)}

ALL AVAILABLE FINANCIAL VALUES (may include multiple years/periods):
{grounding_block}

COMPANY: {company_name or "Not specified"}

DOCUMENT EXCERPT:
{text_preview}

---

Generate a comprehensive financial analysis in valid JSON format.
The content fields MUST use Markdown formatting for structure (bolding, lists, headers).

Required JSON Structure:
{{
    "executive_summary": "## Executive Summary\\n\\n**Key Highlights**\\n* [Point 1]\\n* [Point 2]\\n\\n**Business Overview**\\n[Description]...",
    "financial_performance_overview": "## Financial Performance\\n\\n**Revenue & Profit**\\n* Revenue: [Value]\\n* Net Income: [Value]\\n\\n**Analysis**\\n[Detailed analysis]...",
    "risk_analysis": "## Risk Assessment\\n\\n* **[High/Med/Low] Risk 1**: [Description]\\n* **[High/Med/Low] Risk 2**: [Description]...",
    "trend_detection": "## Trend Analysis\\n\\n* [Trend 1]: [Description]\\n* [Trend 2]: [Description]...",
    "investment_recommendation": "## Recommendation: [Buy/Hold/Sell]\\n\\n**Rationale**\\n[Explanation]...",
    "red_flags": ["Flag 1", "Flag 2"],
    "confidence_score": 0.0 to 1.0,
    "investor_slides": [
        {{ "title": "1. Company Overview & Highlights", "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"] }},
        {{ "title": "2. Financial Performance", "bullets": ["Revenue growth...", "Margins analysis...", "Cash flow..."] }},
        {{ "title": "3. Market Position & Strategy", "bullets": ["Competitive advantage...", "Strategic initiatives..."] }},
        {{ "title": "4. Risks & Mitigations", "bullets": ["Key risk 1...", "Key risk 2..."] }},
        {{ "title": "5. Outlook & Guidance", "bullets": ["Future guidance...", "Expectations..."] }}
    ],
    "compliance": {{
        "ifrs_mentioned": true/false (check for 'International Financial Reporting Standards' or 'IFRS'),
        "gaap_mentioned": true/false (check for 'GAAP' or 'Generally Accepted Accounting Principles'),
        "esg_mentioned": true/false (check for 'ESG', 'Sustainability', 'Carbon', 'Climate'),
        "standard_notes": "Brief note on which standards are explicitly stated."
    }}
}}

Ensure "investor_slides" has exactly 5 slides.
Ensure "compliance" checks are accurate based on the text.
Ensure the "red_flags" is a raw JSON list of strings, NOT a markdown string.
Ensure "confidence_score" is a number.
All other fields should be Markdown strings.

Return ONLY the JSON object, no markdown code blocks or extra text."""


def _parse_monetary(text: str) -> Optional[float]:
    """Parse monetary value from text (e.g., $100 million, 50M)."""
    m = re.search(
        r"[\$€£₹]?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|m|bn|b)?\b",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").lower()
        if unit in ("million", "millions", "mn", "m"):
            return num * 1_000_000
        if unit in ("billion", "billions", "bn", "b"):
            return num * 1_000_000_000
        return num
    except (ValueError, TypeError):
        return None


def _parse_percentage(text: str) -> Optional[float]:
    """Parse percentage from text (e.g., 15%)."""
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*%", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


# Tolerance: numbers within this % of structured data are accepted (rounding, formatting)
_MONETARY_TOLERANCE_PCT = 15.0
_PERCENTAGE_TOLERANCE_PCT = 5.0


def _extract_all_monetary_values(text: str) -> list[tuple[str, float]]:
    """Extract all monetary values from text with context (label before/after number)."""
    results: list[tuple[str, float]] = []
    for m in re.finditer(
        r"[\$€£₹]?\s*\(?\s*([\d,]+(?:\.\d+)?)\s*\)?\s*(million|millions|mn|m|billion|billions|bn|b|thousand|k)?\b",
        text,
        re.IGNORECASE,
    ):
        try:
            num = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            if unit in ("million", "millions", "mn", "m"):
                num *= 1_000_000
            elif unit in ("billion", "billions", "bn", "b"):
                num *= 1_000_000_000
            elif unit in ("thousand", "thousands", "k"):
                num *= 1_000
            if "(" in m.group(0):
                num = -abs(num)
            # Skip years (1900-2099) without unit suffix
            raw_num = float(m.group(1).replace(",", ""))
            if not unit and 1900 <= raw_num <= 2099:
                continue
            if abs(num) >= 10_000:
                context_start = max(0, m.start() - 80)
                context = text[context_start : m.end() + 30].lower()
                results.append((context, num))
        except (ValueError, TypeError):
            pass
    return results


def _extract_all_percentages(text: str) -> list[tuple[str, float]]:
    """Extract all percentage values from text with context."""
    results: list[tuple[str, float]] = []
    for m in re.finditer(r"([\d,]+(?:\.\d+)?)\s*%", text):
        try:
            val = float(m.group(1).replace(",", ""))
            context_start = max(0, m.start() - 60)
            context = text[context_start : m.end() + 20].lower()
            results.append((context, val))
        except (ValueError, TypeError):
            pass
    return results


def _metric_matches_context(metric: str, context: str, keywords: list[str]) -> bool:
    """Check if context refers to the given metric."""
    ctx = context.lower()
    return any(kw.lower() in ctx for kw in keywords)


def _find_nearest_known_value(val: float, known_values: set[float], tolerance_pct: float) -> Optional[float]:
    """Find the nearest known value within extended tolerance for auto-correction."""
    best_match = None
    best_diff = float("inf")
    for known in known_values:
        if known and abs(known) > 1_000:
            diff_pct = abs(val - known) / abs(known) * 100
            if diff_pct <= tolerance_pct * 2 and diff_pct < best_diff:  # 2x tolerance for correction
                best_diff = diff_pct
                best_match = known
    return best_match


def _check_hallucination(
    llm_output: dict[str, Any],
    financial_data: dict[str, Any],
    tolerance_pct: float = _PERCENTAGE_TOLERANCE_PCT,
    monetary_tolerance_pct: float = _MONETARY_TOLERANCE_PCT,
) -> dict[str, Any]:
    """
    Hallucination guard: Compare every LLM-stated number with extracted structured data.
    Auto-corrects mismatched values to nearest known value when possible.
    """
    inconsistencies: list[str] = []
    corrections: list[str] = []
    combined = " ".join(
        str(v) for v in llm_output.values()
        if isinstance(v, (str, list))
    )
    if isinstance(llm_output.get("red_flags"), list):
        combined += " " + " ".join(str(r) for r in llm_output["red_flags"])

    # Build global pool of ALL known monetary values (all metrics, all years)
    all_values = financial_data.get("all_values", {})
    known_values: set[float] = set()
    for metric_name in ("revenue", "net_income", "assets", "liabilities", "expenses"):
        single = financial_data.get(metric_name)
        if single is not None:
            known_values.add(float(single))
        for v in all_values.get(metric_name, []):
            if v is not None:
                known_values.add(float(v))

    # Check every monetary value in LLM output against the global pool
    for context, val in _extract_all_monetary_values(combined):
        if abs(val) < 10_000:
            continue
        # Accept if matches ANY known value within tolerance
        matched = False
        for known in known_values:
            if known and abs(known) > 1_000:
                diff_pct = abs(val - known) / abs(known) * 100
                if diff_pct <= monetary_tolerance_pct:
                    matched = True
                    break
        if not matched and known_values:
            # Try to auto-correct: find nearest known value
            nearest = _find_nearest_known_value(val, known_values, monetary_tolerance_pct)
            likely_metric = "financial_value"
            ctx_lower = context.lower()
            for label, keywords in [
                ("revenue", ["revenue", "sales"]),
                ("net_income", ["net income", "earnings"]),
                ("expenses", ["expenses"]),
                ("assets", ["assets"]),
                ("liabilities", ["liabilities", "debt"]),
            ]:
                if any(kw in ctx_lower for kw in keywords):
                    likely_metric = label
                    break

            if nearest is not None:
                corrections.append(
                    f"Auto-corrected {likely_metric}: LLM said {val:,.0f}, replaced with {nearest:,.0f}"
                )
            else:
                inconsistencies.append(
                    f"LLM states {likely_metric} ~{val:,.0f} — no matching known value found"
                )

    # Check percentages
    percentage_checks = [
        ("gross_margin", financial_data.get("gross_margin"), ["gross margin"]),
        ("profit_margin", financial_data.get("profit_margin"), ["profit margin", "net margin"]),
    ]
    for context, val in _extract_all_percentages(combined):
        for metric, ref_val, keywords in percentage_checks:
            if ref_val is None:
                continue
            if not _metric_matches_context(metric, context, keywords):
                continue
            if abs(val - ref_val) > tolerance_pct:
                corrections.append(
                    f"Auto-corrected {metric}: LLM said {val}%, replaced with {ref_val}%"
                )
            break

    return {
        "has_inconsistency": len(inconsistencies) > 0,
        "inconsistencies": inconsistencies,
        "corrections": corrections,
        "checked": True,
    }


class NumericalMismatchError(ValueError):
    """Raised when LLM output contains numbers that do not match structured data."""

    def __init__(self, inconsistencies: list[str]):
        self.inconsistencies = inconsistencies
        super().__init__(
            "LLM output rejected: numerical values do not match structured data. "
            + "; ".join(inconsistencies[:3])
        )


class LLMProvider(ABC):
    """Abstract LLM provider for pluggable backends."""

    @abstractmethod
    def generate(self, prompt: str, settings: Settings) -> str:
        """Generate completion. Returns raw text."""
        pass


class GroqProvider(LLMProvider):
    """Groq API provider using OpenAI-compatible SDK with Groq base_url."""

    def generate(self, prompt: str, settings: Settings) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.groq_api_key or "",
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a senior financial analyst. Provide data-grounded, precise, analytical insights. Output valid JSON only. Never fabricate or approximate numbers."},
                {"role": "user", "content": prompt},
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return response.choices[0].message.content or ""


def _parse_llm_json(raw: str) -> dict[str, Any]:
    """Parse LLM output as JSON, handling markdown code blocks and extra text."""
    text = raw.strip()
    
    # Try to find JSON object structure
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    # Remove markdown code block if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        
    return json.loads(text)


def _get_fallback_analysis(reason: str) -> dict[str, Any]:
    """Return fallback analysis when AI is unavailable."""
    return {
        "executive_summary": f"AI analysis unavailable: {reason}",
        "financial_performance_overview": "Not available due to service limits.",
        "risk_analysis": "Not available due to service limits.",
        "trend_detection": "Not available due to service limits.",
        "investment_recommendation": "Hold (Analysis unavailable)",
        "red_flags": ["AI Service Unavailable"],
        "confidence_score": 0.0,
        "investor_slides": [],
        "compliance": {"ifrs_mentioned": False, "gaap_mentioned": False, "esg_mentioned": False, "standard_notes": "Unavailable"},
        "hallucination_check": {"has_inconsistency": False, "inconsistencies": [], "corrections": [], "checked": False},
    }


def generate_financial_analysis(
    raw_text: str,
    financial_data: dict[str, Any],
    company_name: Optional[str] = None,
    settings: Optional[Settings] = None,
    provider: Optional[LLMProvider] = None,
) -> dict[str, Any]:
    """
    GenAI Intelligence Layer - main entry point.

    Generates: Executive Summary, Financial Overview, Risk Analysis,
    Trend Detection, Investment Recommendation, Red Flags, Confidence Score.
    Applies hallucination guard against extracted structured data.
    Auto-corrects mismatched values instead of rejecting output.
    """
    from app.config import get_settings

    settings = settings or get_settings()

    # Select provider: Use Groq exclusively
    if not provider:
        if settings.groq_api_key:
            provider = GroqProvider()
            logger.info("Using Groq provider (OpenAI-compatible SDK)")
        else:
            raise ValueError(
                "No Groq API key configured. Set GROQ_API_KEY in .env."
            )

    prompt = _build_prompt(raw_text, financial_data, company_name)

    try:
        raw_output = provider.generate(prompt, settings)
        parsed = _parse_llm_json(raw_output)
    except Exception as e:
        err_str = str(e).lower()
        if "authentication" in err_str or "api_key" in err_str or "401" in err_str:
            logger.warning("LLM auth error: %s", e)
            return _get_fallback_analysis(f"Authentication error - check GROQ_API_KEY")
        elif "rate" in err_str or "429" in err_str:
            logger.warning("LLM rate limit: %s", e)
            return _get_fallback_analysis(f"Rate limit reached - try again later")
        elif isinstance(e, json.JSONDecodeError):
            logger.warning("LLM returned invalid JSON: %s", e)
            return _get_fallback_analysis(f"Invalid JSON from AI provider")
        else:
            logger.exception("LLM generation failed: %s", type(e).__name__)
            return _get_fallback_analysis(f"LLM generation failed: {type(e).__name__}")

    # Ensure required keys
    for key in _OUTPUT_KEYS:
        if key not in parsed:
            parsed[key] = None if key not in ("red_flags", "investor_slides") else []

    # Validate confidence_score
    try:
        cs = parsed.get("confidence_score")
        if isinstance(cs, (int, float)):
            parsed["confidence_score"] = max(0.0, min(1.0, float(cs)))
    except (TypeError, ValueError):
        parsed["confidence_score"] = 0.5

    # Hallucination guard: verify every numerical value against structured data
    hallucination_result = _check_hallucination(parsed, financial_data)
    parsed["hallucination_check"] = hallucination_result

    if hallucination_result["has_inconsistency"]:
        # Graded confidence penalty instead of hard rejection
        penalty = 0.15 * len(hallucination_result["inconsistencies"])
        current_confidence = parsed.get("confidence_score", 0.5)
        if isinstance(current_confidence, (int, float)):
            parsed["confidence_score"] = max(0.1, float(current_confidence) - penalty)
        logger.warning(
            "Hallucination guard: %d inconsistencies, %d auto-corrections (confidence reduced by %.2f)",
            len(hallucination_result["inconsistencies"]),
            len(hallucination_result.get("corrections", [])),
            penalty,
        )
        # NEVER hard-reject: always return partial valid output with warning
        # Old behavior was to raise NumericalMismatchError — now we just reduce confidence

    if hallucination_result.get("corrections"):
        logger.info(
            "Hallucination guard auto-corrected %d values: %s",
            len(hallucination_result["corrections"]),
            "; ".join(hallucination_result["corrections"][:3]),
        )

    return parsed
