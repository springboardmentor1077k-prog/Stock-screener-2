def parse_company_overview(data: dict):
    if not data:
        return None

    return {
        "symbol": data.get("Symbol"),
        "name": data.get("Name"),
        "sector": data.get("Sector"),
        "industry": data.get("Industry"),
        "market_cap": data.get("MarketCapitalization"),
        "pe_ratio": data.get("PERatio"),
        "eps": data.get("EPS"),
        "revenue_ttm": data.get("RevenueTTM")
    }


def parse_daily_time_series(data: dict):
    if not data:
        return None

    time_series = data.get("Time Series (Daily)", {})

    parsed_prices = []

    for date, values in time_series.items():
        parsed_prices.append({
            "date": date,
            "open": values.get("1. open"),
            "high": values.get("2. high"),
            "low": values.get("3. low"),
            "close": values.get("4. close"),
            "volume": values.get("5. volume")
        })

    return parsed_prices