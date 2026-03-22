"""Financial Trend Comparison Engine - Growth, CAGR, anomaly detection, chart data."""

from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def _safe_float(val: Any) -> Optional[float]:
    """Safely convert to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _pct_change(current: float, prior: float) -> Optional[float]:
    """Compute percentage change. Returns None if prior is 0 or invalid."""
    if prior is None or prior == 0:
        return None
    if current is None:
        return None
    try:
        return round((current - prior) / abs(prior) * 100, 2)
    except (TypeError, ZeroDivisionError):
        return None


def compute_cagr(
    start_value: float,
    end_value: float,
    years: int,
) -> Optional[float]:
    """
    Compute Compound Annual Growth Rate (CAGR).
    CAGR = (end/start)^(1/years) - 1, expressed as percentage.
    """
    if years <= 0 or start_value is None or end_value is None:
        return None
    if start_value <= 0:
        return None
    try:
        if end_value <= 0:
            return None
        cagr = (end_value / start_value) ** (1 / years) - 1
        return round(cagr * 100, 2)
    except (ZeroDivisionError, ValueError):
        return None


def _sort_by_year(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort records by year/period ascending."""
    def key(r):
        y = r.get("year") or r.get("period") or r.get("report_year") or 0
        try:
            return int(y)
        except (TypeError, ValueError):
            return 0
    return sorted(records, key=key)


def _get_year(r: dict[str, Any]) -> Optional[int]:
    """Extract year from record."""
    y = r.get("year") or r.get("period") or r.get("report_year")
    if y is None:
        return None
    try:
        return int(y)
    except (TypeError, ValueError):
        return None


def _extract_metrics(r: dict[str, Any]) -> dict[str, Optional[float]]:
    """Extract key metrics from a record."""
    return {
        "revenue": _safe_float(r.get("revenue")),
        "net_income": _safe_float(r.get("net_income")),
        "assets": _safe_float(r.get("assets")),
        "liabilities": _safe_float(r.get("liabilities")),
        "expenses": _safe_float(r.get("expenses")),
        "gross_margin": _safe_float(r.get("gross_margin")),
        "profit_margin": _safe_float(r.get("profit_margin")),
    }


# ─── Rule-Based Anomaly Detection ────────────────────────────────────────────

def _detect_anomalies(
    records: list[dict[str, Any]],
    sorted_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Rule-based anomaly detection. Each anomaly includes:
    - rule_id, rule_name, severity, year, explanation, data
    """
    anomalies: list[dict[str, Any]] = []

    for i in range(1, len(sorted_records)):
        curr = sorted_records[i]
        prev = sorted_records[i - 1]
        curr_y = _get_year(curr)
        prev_y = _get_year(prev)

        cm = _extract_metrics(curr)
        pm = _extract_metrics(prev)

        rev_curr, rev_prev = cm["revenue"], pm["revenue"]
        ni_curr, ni_prev = cm["net_income"], pm["net_income"]
        pm_curr, pm_prev = cm["profit_margin"], pm["profit_margin"]
        gm_curr, gm_prev = cm["gross_margin"], pm["gross_margin"]
        liab_curr, liab_prev = cm["liabilities"], pm["liabilities"]
        ast_curr, ast_prev = cm["assets"], pm["assets"]

        # Rule 1: Revenue up but profit down (inverted margin)
        if (
            rev_curr and rev_prev and rev_curr > rev_prev
            and ni_curr is not None and ni_prev is not None and ni_curr < ni_prev
        ):
            rev_chg = _pct_change(rev_curr, rev_prev)
            ni_chg = _pct_change(ni_curr, ni_prev)
            anomalies.append({
                "rule_id": "REV_UP_PROFIT_DOWN",
                "rule_name": "Revenue Growth with Profit Decline",
                "severity": "high",
                "year": curr_y,
                "prior_year": prev_y,
                "explanation": (
                    f"Revenue increased {rev_chg}% ({prev_y}→{curr_y}) while net income "
                    f"decreased {ni_chg}%. Indicates margin compression or cost increases."
                ),
                "data": {
                    "revenue_change_pct": rev_chg,
                    "net_income_change_pct": ni_chg,
                    "revenue_current": rev_curr,
                    "revenue_prior": rev_prev,
                    "net_income_current": ni_curr,
                    "net_income_prior": ni_prev,
                },
            })

        # Rule 2: Profit margin decline > 5pp YoY
        if (
            pm_curr is not None and pm_prev is not None
            and pm_curr < pm_prev and (pm_prev - pm_curr) >= 5
        ):
            anomalies.append({
                "rule_id": "MARGIN_DECLINE",
                "rule_name": "Significant Profit Margin Decline",
                "severity": "medium",
                "year": curr_y,
                "prior_year": prev_y,
                "explanation": (
                    f"Profit margin fell from {pm_prev}% to {pm_curr}% ({prev_y}→{curr_y}), "
                    f"a {pm_prev - pm_curr:.1f} percentage point drop."
                ),
                "data": {
                    "profit_margin_current": pm_curr,
                    "profit_margin_prior": pm_prev,
                    "decline_pp": pm_prev - pm_curr,
                },
            })

        # Rule 3: Gross margin collapse (> 10pp)
        if (
            gm_curr is not None and gm_prev is not None
            and gm_curr < gm_prev and (gm_prev - gm_curr) >= 10
        ):
            anomalies.append({
                "rule_id": "GROSS_MARGIN_COLLAPSE",
                "rule_name": "Gross Margin Collapse",
                "severity": "high",
                "year": curr_y,
                "prior_year": prev_y,
                "explanation": (
                    f"Gross margin dropped from {gm_prev}% to {gm_curr}% ({prev_y}→{curr_y}). "
                    "May indicate pricing pressure or COGS inflation."
                ),
                "data": {
                    "gross_margin_current": gm_curr,
                    "gross_margin_prior": gm_prev,
                },
            })

        # Rule 4: Liabilities growing faster than assets
        if (
            liab_curr and liab_prev and ast_curr and ast_prev
            and liab_prev > 0 and ast_prev > 0
        ):
            liab_chg = _pct_change(liab_curr, liab_prev)
            ast_chg = _pct_change(ast_curr, ast_prev)
            if liab_chg is not None and ast_chg is not None and liab_chg > ast_chg + 15:
                anomalies.append({
                    "rule_id": "LIABILITIES_OUTPACE_ASSETS",
                    "rule_name": "Liabilities Growing Faster Than Assets",
                    "severity": "medium",
                    "year": curr_y,
                    "prior_year": prev_y,
                    "explanation": (
                        f"Liabilities grew {liab_chg}% vs assets {ast_chg}% ({prev_y}→{curr_y}). "
                        "Increasing leverage or deteriorating balance sheet."
                    ),
                    "data": {
                        "liabilities_change_pct": liab_chg,
                        "assets_change_pct": ast_chg,
                    },
                })

        # Rule 5: Negative profit margin (loss)
        if ni_curr is not None and ni_curr < 0 and rev_curr and rev_curr > 0:
            anomalies.append({
                "rule_id": "NEGATIVE_PROFIT",
                "rule_name": "Net Loss",
                "severity": "high" if i == len(sorted_records) - 1 else "medium",
                "year": curr_y,
                "prior_year": prev_y,
                "explanation": f"Net loss in {curr_y} despite positive revenue. {pm_curr}% profit margin.",
                "data": {"net_income": ni_curr, "revenue": rev_curr, "profit_margin": pm_curr},
            })

        # Rule 6: Revenue decline
        if rev_curr and rev_prev and rev_curr < rev_prev:
            rev_chg = _pct_change(rev_curr, rev_prev)
            if rev_chg is not None and rev_chg < -10:
                anomalies.append({
                    "rule_id": "REVENUE_DECLINE",
                    "rule_name": "Significant Revenue Decline",
                    "severity": "medium",
                    "year": curr_y,
                    "prior_year": prev_y,
                    "explanation": f"Revenue declined {rev_chg}% YoY ({prev_y}→{curr_y}).",
                    "data": {"revenue_change_pct": rev_chg, "revenue_current": rev_curr, "revenue_prior": rev_prev},
                })

    return anomalies


# ─── Growth Analysis ────────────────────────────────────────────────────────

def _compute_growth_analysis(
    sorted_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute revenue growth, CAGR, and growth comparison."""
    if len(sorted_records) < 2:
        return {"message": "Need at least 2 years for growth analysis", "cagr": None}

    first = sorted_records[0]
    last = sorted_records[-1]
    first_y = _get_year(first)
    last_y = _get_year(last)

    fm = _extract_metrics(first)
    lm = _extract_metrics(last)

    rev_first = fm["revenue"]
    rev_last = lm["revenue"]
    ni_first = fm["net_income"]
    ni_last = lm["net_income"]

    years = (last_y or 0) - (first_y or 0) if last_y and first_y else len(sorted_records) - 1
    years = max(1, years)

    cagr_revenue = compute_cagr(rev_first or 0, rev_last or 0, years) if rev_first and rev_last else None
    cagr_net_income = compute_cagr(ni_first or 0, ni_last or 0, years) if ni_first and ni_last else None

    yoy_revenue: list[dict[str, Any]] = []
    for i in range(1, len(sorted_records)):
        curr = sorted_records[i]
        prev = sorted_records[i - 1]
        cm = _extract_metrics(curr)
        pm = _extract_metrics(prev)
        rev_c, rev_p = cm["revenue"], pm["revenue"]
        ni_c, ni_p = cm["net_income"], pm["net_income"]
        chg_rev = _pct_change(rev_c or 0, rev_p or 1) if rev_p else None
        chg_ni = _pct_change(ni_c or 0, ni_p or 1) if ni_p else None
        yoy_revenue.append({
            "year": _get_year(curr),
            "prior_year": _get_year(prev),
            "revenue_growth_pct": chg_rev,
            "net_income_growth_pct": chg_ni,
        })

    return {
        "period": {"start_year": first_y, "end_year": last_y, "years": years},
        "cagr_revenue_pct": cagr_revenue,
        "cagr_net_income_pct": cagr_net_income,
        "revenue_start": rev_first,
        "revenue_end": rev_last,
        "net_income_start": ni_first,
        "net_income_end": ni_last,
        "year_over_year": yoy_revenue,
    }


# ─── Year-over-Year Change ──────────────────────────────────────────────────

def _compute_yoy_change(
    sorted_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute detailed YoY changes for all metrics."""
    result: list[dict[str, Any]] = []
    for i in range(1, len(sorted_records)):
        curr = sorted_records[i]
        prev = sorted_records[i - 1]
        curr_y = _get_year(curr)
        prev_y = _get_year(prev)
        cm = _extract_metrics(curr)
        pm = _extract_metrics(prev)

        deltas: dict[str, Any] = {"year": curr_y, "prior_year": prev_y}
        for k in ("revenue", "net_income", "assets", "liabilities", "expenses", "gross_margin", "profit_margin"):
            c, p = cm.get(k), pm.get(k)
            if c is not None and p is not None and p != 0 and k not in ("gross_margin", "profit_margin"):
                deltas[f"{k}_change_pct"] = _pct_change(c, p)
            elif c is not None and p is not None and k in ("gross_margin", "profit_margin"):
                deltas[f"{k}_change_pp"] = round((c - p), 2)  # percentage points
        result.append(deltas)
    return result


# ─── Risk Trend Evolution ───────────────────────────────────────────────────

def _compute_risk_trend(
    sorted_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Risk trend evolution: risk count or risk-related metrics over years."""
    risk_data: list[dict[str, Any]] = []
    for r in sorted_records:
        y = _get_year(r)
        risks = r.get("risks")
        risks_count = len(risks) if isinstance(risks, list) else None
        risk_data.append({"year": y, "risks_count": risks_count})
    return {"by_year": risk_data}


# ─── Visual Chart Data ──────────────────────────────────────────────────────

def _generate_visual_data(
    sorted_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate chart-ready data for revenue, net income, margins."""
    years = [_get_year(r) for r in sorted_records]
    labels = [str(y) for y in years if y is not None]

    revenue = [_extract_metrics(r)["revenue"] for r in sorted_records]
    net_income = [_extract_metrics(r)["net_income"] for r in sorted_records]
    profit_margin = [_extract_metrics(r)["profit_margin"] for r in sorted_records]
    gross_margin = [_extract_metrics(r)["gross_margin"] for r in sorted_records]
    assets = [_extract_metrics(r)["assets"] for r in sorted_records]
    liabilities = [_extract_metrics(r)["liabilities"] for r in sorted_records]

    return {
        "labels": labels,
        "series": {
            "revenue": revenue,
            "net_income": net_income,
            "profit_margin": profit_margin,
            "gross_margin": gross_margin,
            "assets": assets,
            "liabilities": liabilities,
        },
        "growth_series": {
            "revenue_growth_pct": [
                _pct_change(
                    _extract_metrics(sorted_records[i])["revenue"] or 0,
                    _extract_metrics(sorted_records[i - 1])["revenue"] or 1,
                )
                for i in range(1, len(sorted_records))
            ],
            "net_income_growth_pct": [
                _pct_change(
                    _extract_metrics(sorted_records[i])["net_income"] or 0,
                    _extract_metrics(sorted_records[i - 1])["net_income"] or 1,
                )
                for i in range(1, len(sorted_records))
            ],
        },
        "growth_labels": [str(_get_year(sorted_records[i])) for i in range(1, len(sorted_records))],
    }


# ─── Trend Summary ──────────────────────────────────────────────────────────

def _generate_trend_summary(
    growth_analysis: dict[str, Any],
    anomalies: list[dict[str, Any]],
) -> str:
    """Generate explainable, data-driven trend summary."""
    parts: list[str] = []

    ga = growth_analysis
    if ga.get("cagr_revenue_pct") is not None:
        parts.append(f"Revenue CAGR: {ga['cagr_revenue_pct']}% over the period.")
    if ga.get("cagr_net_income_pct") is not None:
        parts.append(f"Net income CAGR: {ga['cagr_net_income_pct']}%.")

    if anomalies:
        high = [a for a in anomalies if a.get("severity") == "high"]
        medium = [a for a in anomalies if a.get("severity") == "medium"]
        if high:
            parts.append(f"{len(high)} high-severity anomaly(ies) detected: "
                        + "; ".join(a["rule_name"] for a in high[:3]))
        if medium:
            parts.append(f"{len(medium)} medium-severity anomaly(ies): "
                        + "; ".join(a["rule_name"] for a in medium[:3]))
    else:
        parts.append("No rule-based anomalies detected.")

    return " ".join(parts) if parts else "Insufficient data for trend summary."


# ─── Main Entry Point ───────────────────────────────────────────────────────

def compare_financial_trends(
    financial_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Financial Trend Comparison Engine - main entry point.

    Input: List of structured financial JSON objects (each with year + metrics).
    Output: growth_analysis, anomaly_flags, trend_summary, year_over_year_change, visual_data.
    """
    if not financial_records:
        return {
            "growth_analysis": {"message": "No records provided"},
            "anomaly_flags": [],
            "trend_summary": "No data to analyze.",
            "year_over_year_change": [],
            "visual_data": {"labels": [], "series": {}},
        }

    sorted_records = _sort_by_year(financial_records)

    growth_analysis = _compute_growth_analysis(sorted_records)
    anomaly_flags = _detect_anomalies(financial_records, sorted_records)
    yoy_change = _compute_yoy_change(sorted_records)
    risk_trend = _compute_risk_trend(sorted_records)
    visual_data = _generate_visual_data(sorted_records)
    visual_data["risk_trend"] = risk_trend

    trend_summary = _generate_trend_summary(growth_analysis, anomaly_flags)

    return {
        "growth_analysis": growth_analysis,
        "anomaly_flags": anomaly_flags,
        "trend_summary": trend_summary,
        "year_over_year_change": yoy_change,
        "visual_data": visual_data,
    }
