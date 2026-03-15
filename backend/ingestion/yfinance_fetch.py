import os
import json
import yfinance as yf

# folder where json files will be saved
DATA_DIR = os.path.join("backend", "data")

os.makedirs(DATA_DIR, exist_ok=True)

# 25 companies
SYMBOLS = [
    "INFY.NS",
    "TCS.NS",
    "WIPRO.NS",
    "HCLTECH.NS",
    "TECHM.NS",
    "LTIM.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "KOTAKBANK.NS",
    "AXISBANK.NS",
    "SBIN.NS",
    "RELIANCE.NS",
    "ITC.NS",
    "HINDUNILVR.NS",
    "BAJFINANCE.NS",
    "TITAN.NS",
    "MARUTI.NS",
    "ULTRACEMCO.NS",
    "ASIANPAINT.NS",
    "BHARTIARTL.NS",
    "SUNPHARMA.NS",
    "DRREDDY.NS",
    "ADANIENT.NS",
    "ONGC.NS"
]


def fetch_company(symbol):

    print(f"Fetching {symbol}")

    stock = yf.Ticker(symbol)

    info = stock.info
    history = stock.history(period="6mo")

    # ---------- COMPANY OVERVIEW ----------
    overview_data = {
        "Symbol": symbol,
        "Name": info.get("longName"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Website": info.get("website"),
        "Country": info.get("country"),
        "City": info.get("city"),
        "Employees": info.get("fullTimeEmployees"),
        "MarketCap": info.get("marketCap"),
        "Currency": info.get("currency"),
        "CurrentPrice": info.get("currentPrice"),
        "Description": info.get("longBusinessSummary"),
        "Exchange": "NSE"
    }

    with open(os.path.join(DATA_DIR, f"{symbol}_company_overview.json"), "w") as f:
        json.dump(overview_data, f, indent=4)

    # ---------- FUNDAMENTALS ----------
    fundamentals_data = {
        "Symbol": symbol,

        # valuation
        "PERatio": info.get("trailingPE"),
        "PEGRatio": info.get("pegRatio"),
        "MarketCap": info.get("marketCap"),

        # income metrics
        "RevenueTTM": info.get("totalRevenue"),
        "RevenueGrowth": info.get("revenueGrowth"),
        "EBITDA": info.get("ebitda"),
        "ProfitMargins": info.get("profitMargins"),

        # balance sheet
        "TotalDebt": info.get("totalDebt"),
        "DebtToEquity": info.get("debtToEquity"),

        # profitability
        "ReturnOnEquity": info.get("returnOnEquity"),
        "ReturnOnAssets": info.get("returnOnAssets"),

        # shareholder metrics
        "EPS": info.get("trailingEps"),
        "BookValue": info.get("bookValue"),
        "DividendYield": info.get("dividendYield")
    }

    with open(os.path.join(DATA_DIR, f"{symbol}_fundamentals_income.json"), "w") as f:
        json.dump(fundamentals_data, f, indent=4)

    # ---------- HISTORICAL PRICES ----------
    price_series = []

    for date, row in history.iterrows():

        price_series.append({
            "date": str(date.date()),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"])
        })

    historical_data = {
        "Symbol": symbol,
        "HistoricalPrices": price_series
    }

    with open(os.path.join(DATA_DIR, f"{symbol}_historical_prices.json"), "w") as f:
        json.dump(historical_data, f, indent=4)


for symbol in SYMBOLS:

    try:
        fetch_company(symbol)
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

print("All company JSON files saved.")