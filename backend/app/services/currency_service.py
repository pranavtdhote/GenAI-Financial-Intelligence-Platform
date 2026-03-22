"""Multi-Currency Support Service - Detection, conversion, and formatting."""

from typing import Optional

# Static exchange rates (USD base) for demo purposes
# In production, these would come from a live API (e.g., Alpha Vantage, Open Exchange Rates)
EXCHANGE_RATES: dict[str, float] = {
    "USD": 1.0,
    "INR": 83.0,
    "EUR": 0.92,
    "GBP": 0.79,
}

CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
}

# Reverse map: symbol → currency code
_SYMBOL_TO_CODE: dict[str, str] = {v: k for k, v in CURRENCY_SYMBOLS.items()}


def get_supported_currencies() -> list[dict[str, str]]:
    """Return list of supported currencies with symbols."""
    return [
        {"code": code, "symbol": symbol, "rate": str(EXCHANGE_RATES[code])}
        for code, symbol in CURRENCY_SYMBOLS.items()
    ]


def detect_currency(text: str) -> str:
    """Detect the primary currency used in the document text.

    Looks for currency symbols and keywords. Returns ISO code (default USD).
    """
    if not text:
        return "USD"

    # Check first ~5000 chars for currency indicators
    sample = text[:5000].lower()

    # Count occurrences
    counts: dict[str, int] = {"USD": 0, "INR": 0, "EUR": 0, "GBP": 0}

    counts["USD"] += sample.count("$") + sample.count("usd") + sample.count("dollar")
    counts["INR"] += sample.count("₹") + sample.count("inr") + sample.count("rupee") + sample.count("crore") + sample.count("lakh")
    counts["EUR"] += sample.count("€") + sample.count("eur")
    counts["GBP"] += sample.count("£") + sample.count("gbp") + sample.count("pound sterling")

    # Return currency with highest count, default USD
    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] > 0 else "USD"


def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate from one currency to another."""
    from_rate = EXCHANGE_RATES.get(from_currency.upper(), 1.0)
    to_rate = EXCHANGE_RATES.get(to_currency.upper(), 1.0)
    # Convert via USD base: from → USD → to
    return to_rate / from_rate


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert an amount from one currency to another."""
    if from_currency.upper() == to_currency.upper():
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    return amount * rate


def format_currency(amount: Optional[float], currency: str = "USD") -> str:
    """Format a monetary amount with the appropriate currency symbol and scale.

    Examples:
        format_currency(120_000_000, "USD") → "$120.00M"
        format_currency(9_960_000_000, "INR") → "₹996.00 Cr"
        format_currency(110_000_000, "EUR") → "€110.00M"
    """
    if amount is None:
        return "—"

    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "$")
    abs_amount = abs(amount)
    sign = "-" if amount < 0 else ""

    if currency.upper() == "INR":
        # Indian numbering: Crore (10M) and Lakh (100K)
        if abs_amount >= 1e7:  # >= 1 Crore
            return f"{sign}{symbol}{abs_amount / 1e7:,.2f} Cr"
        elif abs_amount >= 1e5:  # >= 1 Lakh
            return f"{sign}{symbol}{abs_amount / 1e5:,.2f} L"
        else:
            return f"{sign}{symbol}{abs_amount:,.0f}"
    else:
        # Western numbering: B, M, K
        if abs_amount >= 1e9:
            return f"{sign}{symbol}{abs_amount / 1e9:,.2f}B"
        elif abs_amount >= 1e6:
            return f"{sign}{symbol}{abs_amount / 1e6:,.2f}M"
        elif abs_amount >= 1e3:
            return f"{sign}{symbol}{abs_amount / 1e3:,.2f}K"
        else:
            return f"{sign}{symbol}{abs_amount:,.2f}"
