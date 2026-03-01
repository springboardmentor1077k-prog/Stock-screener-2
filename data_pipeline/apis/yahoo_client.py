import yfinance as yf


def fetch_company_info(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except Exception as e:
        print("Yahoo info fetch failed:", e)
        return None


def fetch_historical_data(symbol: str, period="3mo"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        hist = hist.reset_index()

        # Convert Timestamp to string
        hist["Date"] = hist["Date"].astype(str)

        return hist.to_dict(orient="records")

    except Exception as e:
        print("Yahoo historical fetch failed:", e)
        return None
    
