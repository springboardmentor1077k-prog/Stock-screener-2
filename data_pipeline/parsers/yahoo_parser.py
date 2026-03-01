def parse_yahoo_info(data: dict):
    if not data:
        return None

    return {
        "symbol": data.get("symbol"),
        "name": data.get("longName"),
        "sector": data.get("sector"),
        "industry": data.get("industry"),
        "market_cap": data.get("marketCap"),
        "pe_ratio": data.get("trailingPE"),
        "eps": data.get("trailingEps"),
        "revenue_ttm": data.get("totalRevenue")
    }


def parse_yahoo_historical(data: list):
    if not data:
        return None

    parsed = []

    for row in data:
        parsed.append({
            "date": row.get("Date"),
            "open": row.get("Open"),
            "high": row.get("High"),
            "low": row.get("Low"),
            "close": row.get("Close"),
            "volume": row.get("Volume")
        })

    return parsed


