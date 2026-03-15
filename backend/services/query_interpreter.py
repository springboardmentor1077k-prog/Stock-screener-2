import re

def interpret_query(user_query: str) -> str:
    """
    Normalize investor language before sending to LLM.
    Improves LLM accuracy and reduces ambiguity.
    """

    query = user_query.lower().strip()

    replacements = {

        # sector detection
        "it companies": "sector Technology",
        "tech companies": "sector Technology",
        "banking companies": "sector Financial Services",
        "bank stocks": "sector Financial Services",
        "pharma companies": "sector Healthcare",
        "healthcare companies": "sector Healthcare",

        # valuation
        "cheap": "low pe_ratio",
        "low pe": "low pe_ratio",
        "low p/e": "low pe_ratio",
        "undervalued": "low pe_ratio",
        "expensive": "high pe_ratio",

        # profitability
        "good margins": "high profit_margin",
        "strong margins": "high profit_margin",
        "high margin": "high profit_margin",

        # growth
        "high growth": "high revenue_growth",
        "growing companies": "high revenue_growth",
        "revenue increasing": "high revenue_growth",
        "revenue growing": "high revenue_growth",
        "companies doing better every year": "high revenue_growth",
        "companies with increasing revenue": "high revenue_growth",

        # price trend
        "stocks trending upward": "high price_growth",
        "stocks gaining momentum": "high price_growth",
        "stocks with rising price": "high price_growth",
        "stocks going up": "high price_growth",

        # improving companies
        "improving profits": "high roe",
        "better profits": "high roe",

        # stability
        "low debt": "low debt_to_equity",
        "stable": "low debt_to_equity",

        # strength
        "financially strong": "high roe low debt_to_equity",
        "strong company": "high roe"
    }

    for key, value in replacements.items():
        if key in query:
            query = query.replace(key, value)

    return query