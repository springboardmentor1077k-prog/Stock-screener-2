import yfinance as yf
import json
import os


class YahooFinanceClient:

    def get_company_info(self, symbol):
        ticker = yf.Ticker(symbol)
        return ticker.info

    def get_historical_data(self, symbol):
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")

        # Reset index so date becomes a normal column
        df.reset_index(inplace=True)

    # Convert datetime to string
        df["Date"] = df["Date"].astype(str)

        return df.to_dict(orient="records")


    def save_json(self, data, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
