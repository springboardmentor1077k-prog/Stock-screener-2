"""
============================================================
                    STOCK NORMALIZER
============================================================

Purpose:
Merge structured outputs from multiple APIs
into one unified stock object.

Policy:
- Yahoo is primary source
- Alpha is fallback
- If Yahoo field missing → use Alpha
- I'll refactor this normalizer.py later during scaling
============================================================
"""

def normalize_stock(alpha_data: dict | None,
                    yahoo_data: dict | None) -> dict | None:

    if not alpha_data and not yahoo_data:
        return None

    # Prefer Yahoo for base structure
    base = yahoo_data if yahoo_data else alpha_data

    ticker = base.get("ticker")

    # -----------------------------
    # Company Profile
    # -----------------------------
    def pick(field, section):
        """
        Helper:
        Prefer Yahoo → fallback Alpha
        """
        if yahoo_data and yahoo_data.get(section, {}).get(field):
            return yahoo_data[section][field]

        if alpha_data and alpha_data.get(section, {}).get(field):
            return alpha_data[section][field]

        return None

    company_profile = {
        "name": pick("name", "company_profile"),
        "sector": pick("sector", "company_profile"),
        "industry": pick("industry", "company_profile")
    }

    # -----------------------------
    # Fundamentals
    # -----------------------------
    fundamentals = {
        "market_cap": pick("market_cap", "fundamentals"),
        "pe_ratio": pick("pe_ratio", "fundamentals"),
        "eps": pick("eps", "fundamentals"),
        "revenue_ttm": pick("revenue_ttm", "fundamentals")
    }

    # -----------------------------
    # Historical Prices
    # Prefer Yahoo (more stable)
    # -----------------------------
    historical_prices = None

    if yahoo_data and yahoo_data.get("historical_prices"):
        historical_prices = yahoo_data["historical_prices"]
    elif alpha_data and alpha_data.get("historical_prices"):
        historical_prices = alpha_data["historical_prices"]

    # -----------------------------
    # Final Unified Object
    # -----------------------------
    normalized_stock = {
        "ticker": ticker,
        "company_profile": company_profile,
        "fundamentals": fundamentals,
        "historical_prices": historical_prices,
        "data_sources": {
            "profile": "yahoo" if yahoo_data else "alpha",
            "historical": "yahoo" if yahoo_data else "alpha"
        }
    }

    return normalized_stock