import yfinance as yf
import json
import os


def fetch_multiple_stocks(symbols):
    companies = []
    metrics = []
    historical_prices = {}

    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            # Company Info
            company = {
                "symbol": symbol,
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country")
            }
            companies.append(company)

            # Metrics
            metric = {
                "symbol": symbol,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "roe": info.get("returnOnEquity")
            }
            metrics.append(metric)

            # Historical Prices (1 Year)
            history = stock.history(period="1y")
            history.reset_index(inplace=True)
            history["Date"] = history["Date"].astype(str)

            historical_prices[symbol] = history.to_dict(orient="records")

            print(f" Fetched {symbol}")

        except Exception as e:
            print(f" Error fetching {symbol}: {e}")

    return companies, metrics, historical_prices


def save_to_json(companies, metrics, historical_prices):
    os.makedirs("data", exist_ok=True)

    data = {
        "companies": companies,
        "metrics": metrics,
        "historical_prices": historical_prices
    }

    filepath = "data/stocks_data.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(" All data saved to data/stocks_data.json")


if __name__ == "__main__":
    symbols = ["AAPL", "MSFT", "GOOGL"]

    companies, metrics, historical_prices = fetch_multiple_stocks(symbols)

    save_to_json(companies, metrics, historical_prices)
