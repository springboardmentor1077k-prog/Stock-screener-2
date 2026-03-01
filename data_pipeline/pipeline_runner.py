"""
============================================================
                STOCK DATA PIPELINE RUNNER
============================================================

This file orchestrates the full pipeline:

For each symbol:
    1. Fetch data from APIs
    2. Save raw snapshots
    3. Fallback to stored snapshot if API fails
    4. Parse required fields
    5. Build structured schema
    6. Save structured output

This follows:
Fetch → Raw Save → Parse → Structure → Structured Save
============================================================
"""

# ============================
# IMPORTS
# ============================

from data_pipeline.apis.alpha_client import (
    fetch_company_overview,
    fetch_daily_time_series
)

from data_pipeline.apis.yahoo_client import (
    fetch_company_info,
    fetch_historical_data
)

from data_pipeline.parsers.alpha_parser import (
    parse_company_overview,
    parse_daily_time_series
)

from data_pipeline.parsers.yahoo_parser import (
    parse_yahoo_info,
    parse_yahoo_historical
)

from data_pipeline.utils.storage import (
    save_raw_data,
    load_latest_raw
)

from data_pipeline.utils.structured_storage import save_structured_data


# ============================
# CONTROL FLAGS
# ============================

FETCH_ALPHA = True
FETCH_YAHOO = True

# Multiple companies
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]


# ============================================================
# MAIN PIPELINE LOOP
# ============================================================

for symbol in symbols:

    print("\n================================================")
    print(f"Processing {symbol}")
    print("================================================\n")

    # --------------------------------------------------------
    # ALPHA SECTION
    # --------------------------------------------------------

    overview = None
    daily = None

    if FETCH_ALPHA:

        # --- Fetch Overview ---
        overview = fetch_company_overview(symbol)

        if overview:
            print("Alpha overview fetched")
            save_raw_data("alpha_overview", symbol, overview)
        else:
            print("Alpha overview fetch failed → loading latest snapshot")
            overview = load_latest_raw(symbol, "alpha_overview")

        # --- Fetch Daily Data ---
        daily = fetch_daily_time_series(symbol)

        if daily:
            print("Alpha daily fetched")
            save_raw_data("alpha_daily", symbol, daily)
        else:
            print("Alpha daily fetch failed → loading latest snapshot")
            daily = load_latest_raw(symbol, "alpha_daily")

    # --------------------------------------------------------
    # YAHOO SECTION
    # --------------------------------------------------------

    yahoo_info = None
    yahoo_hist = None

    if FETCH_YAHOO:

        # --- Fetch Company Info ---
        yahoo_info = fetch_company_info(symbol)

        if yahoo_info:
            print("Yahoo info fetched")
            save_raw_data("yahoo_info", symbol, yahoo_info)

        # --- Fetch Historical Data ---
        yahoo_hist = fetch_historical_data(symbol)

        if yahoo_hist:
            print("Yahoo historical fetched")
            save_raw_data("yahoo_hist", symbol, yahoo_hist)

    # --------------------------------------------------------
    # PARSING SECTION
    # --------------------------------------------------------

    parsed_alpha_overview = parse_company_overview(overview) if overview else None
    parsed_alpha_daily = parse_daily_time_series(daily) if daily else None

    parsed_yahoo_info = parse_yahoo_info(yahoo_info) if yahoo_info else None
    parsed_yahoo_hist = parse_yahoo_historical(yahoo_hist) if yahoo_hist else None

    # --------------------------------------------------------
    # STRUCTURED BUILD (ALPHA)
    # --------------------------------------------------------

    if parsed_alpha_overview and parsed_alpha_daily:

        structured_alpha = {
            "ticker": parsed_alpha_overview.get("symbol"),
            "company_profile": {
                "name": parsed_alpha_overview.get("name"),
                "sector": parsed_alpha_overview.get("sector"),
                "industry": parsed_alpha_overview.get("industry")
            },
            "fundamentals": {
                "market_cap": parsed_alpha_overview.get("market_cap"),
                "pe_ratio": parsed_alpha_overview.get("pe_ratio"),
                "eps": parsed_alpha_overview.get("eps"),
                "revenue_ttm": parsed_alpha_overview.get("revenue_ttm")
            },
            "historical_prices": parsed_alpha_daily
        }

        save_structured_data(symbol, "alpha", structured_alpha)
        print("Structured Alpha data saved.")

    else:
        if FETCH_ALPHA:
            print("Alpha structured data skipped due to missing components.")

    # --------------------------------------------------------
    # STRUCTURED BUILD (YAHOO)
    # --------------------------------------------------------

    if parsed_yahoo_info and parsed_yahoo_hist:

        structured_yahoo = {
            "ticker": parsed_yahoo_info.get("symbol"),
            "company_profile": {
                "name": parsed_yahoo_info.get("name"),
                "sector": parsed_yahoo_info.get("sector"),
                "industry": parsed_yahoo_info.get("industry")
            },
            "fundamentals": {
                "market_cap": parsed_yahoo_info.get("market_cap"),
                "pe_ratio": parsed_yahoo_info.get("pe_ratio"),
                "eps": parsed_yahoo_info.get("eps"),
                "revenue_ttm": parsed_yahoo_info.get("revenue_ttm")
            },
            "historical_prices": parsed_yahoo_hist
        }

        save_structured_data(symbol, "yahoo", structured_yahoo)
        print("Structured Yahoo data saved.")

    else:
        if FETCH_YAHOO:
            print("Yahoo structured data skipped due to missing components.")

    print("\nFinished processing:", symbol)