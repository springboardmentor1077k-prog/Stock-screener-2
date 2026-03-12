import requests
import json
import os
import time
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

BASE_URL = "https://www.alphavantage.co/query"

# Create folder for storing API responses
os.makedirs("data", exist_ok=True)

# Day 1 companies (8 companies = 24 API calls)
SYMBOLS = [
    "INFY",
    "TCS",
    "WIPRO",
    "HCLTECH",
    "TECHM",
    "LTIM",
    "HDFCBANK",
    "ICICIBANK"
]


def fetch_and_save(symbol, function_name, filename_suffix):

    params = {
        "function": function_name,
        "symbol": symbol,
        "apikey": API_KEY
    }

    print(f"Fetching {function_name} for {symbol}...")

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        file_path = f"data/{symbol}_{filename_suffix}.json"

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Saved → {file_path}")

    except Exception as e:
        print(f"Error fetching {symbol} ({function_name}): {e}")


# Fetch data for each company
for symbol in SYMBOLS:

    fetch_and_save(symbol, "OVERVIEW", "company_overview")
    time.sleep(12)

    fetch_and_save(symbol, "INCOME_STATEMENT", "fundamentals_income")
    time.sleep(12)

    fetch_and_save(symbol, "TIME_SERIES_DAILY", "historical_prices")
    time.sleep(12)

print("Day 1 API data fetched successfully.")