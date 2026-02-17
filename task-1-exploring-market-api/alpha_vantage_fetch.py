import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
print("API KEY LOADED:", API_KEY)

BASE_URL = "https://www.alphavantage.co/query"

os.makedirs("data", exist_ok=True)

def fetch_and_save(params, filename):
    print(f"Calling API for {filename}...")
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        print(f"Response received for {filename}")

        with open(f"data/{filename}.json", "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(f"Error while fetching {filename}:", e)

# Company Overview
fetch_and_save({
    "function": "OVERVIEW",
    "symbol": "INFY",
    "apikey": API_KEY
}, "company_overview")

# Fundamental Metrics
fetch_and_save({
    "function": "INCOME_STATEMENT",
    "symbol": "INFY",
    "apikey": API_KEY
}, "fundamentals_income")

# Historical Price Data
fetch_and_save({
    "function": "TIME_SERIES_DAILY",
    "symbol": "INFY",
    "apikey": API_KEY
}, "historical_prices")

print("API data saved successfully.")
