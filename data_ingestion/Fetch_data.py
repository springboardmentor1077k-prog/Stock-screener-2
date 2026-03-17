import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

if not API_KEY:
    raise ValueError("API key missing")


SYMBOLS = [
"AAPL","MSFT","GOOGL","AMZN","META","TSLA",
"AMD","INTC","QCOM","TXN","AVGO",
"CRM","NOW","ADBE","ORCL","SAP",
"UBER","LYFT","SNAP","SHOP",
"IBM","CSCO","DELL","HPQ"
]


DATA_FOLDER = "raw"

os.makedirs(DATA_FOLDER, exist_ok=True)


def fetch_overview(symbol):

    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:

        data = response.json()

        with open(f"{DATA_FOLDER}/{symbol}_overview.json", "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved {symbol} overview")

    else:
        print("Error fetching", symbol)


def main():

    for symbol in SYMBOLS:

        fetch_overview(symbol)

        # Alpha Vantage rate limit protection
        time.sleep(12)


if __name__ == "__main__":
    main()