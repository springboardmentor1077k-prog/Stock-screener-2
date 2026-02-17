#Importing necessary libraries
import os
import requests
import json
import time
from dotenv import load_dotenv

# API key is added in env file
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

if not API_KEY:
    raise ValueError("Error")

SYMBOL = "NVDA"   # Fetching nvdia stocks data


def make_api_call(params, filename):
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200: 
        data = response.json()

        # Saving  to local file
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved data to {filename}")

    else:
        print(f"Failed request for {filename}")
        print("Status Code:", response.status_code)


def main():
    # 1️ Company overview calling
    overview_params = {
        "function": "OVERVIEW",
        "symbol": SYMBOL,
        "apikey": API_KEY
    }
    make_api_call(overview_params, "company_overview.json")

    time.sleep(10)  #to avoid rate limit

    # 2 Fundamental Data
    income_params = {
        "function": "INCOME_STATEMENT",
        "symbol": SYMBOL,
        "apikey": API_KEY
    }
    make_api_call(income_params, "fundamentals.json")

    time.sleep(10)

    # 3️ Historical Data
    price_params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": SYMBOL,
        "apikey": API_KEY
    }
    make_api_call(price_params, "historical_prices.json")


if __name__ == "__main__":
    main()
