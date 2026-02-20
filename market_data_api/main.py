import time
from apis.alpha_client import AlphaVantageClient
from apis.yahoo_client import YahooFinanceClient


API_KEY = "Use your original api key"
STOCKS = ["AAPL", "MSFT"]


def run():
    alpha = AlphaVantageClient(API_KEY)
    yahoo = YahooFinanceClient()

    for symbol in STOCKS:
        print(f"\nFetching data for {symbol}...")

        # Alpha Vantage
        overview = alpha.get_company_overview(symbol)
        alpha.save_json(
            overview,
            f"data/alpha_vantage/{symbol}_overview.json"
        )

        historical = alpha.get_historical_daily(symbol)
        alpha.save_json(
            historical,
            f"data/alpha_vantage/{symbol}_historical.json"
        )

        time.sleep(12)  # avoid rate limit

        # Yahoo Finance
        info = yahoo.get_company_info(symbol)
        yahoo.save_json(
            info,
            f"data/yahoo_finance/{symbol}_info.json"
        )

        history = yahoo.get_historical_data(symbol)
        yahoo.save_json(
            history,
            f"data/yahoo_finance/{symbol}_history.json"
        )

    print("\n✅ All data fetched successfully.")


if __name__ == "__main__":
    run()
