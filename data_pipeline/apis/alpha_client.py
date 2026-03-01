import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def _make_request(params: dict):
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Rate limit check
        if "Note" in data or "Information" in data:
            print("Alpha Vantage rate limit or throttling message received.")
            return None

        # API error check
        if "Error Message" in data:
            print("Alpha Vantage error:", data["Error Message"])
            return None

        return data

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None


def fetch_company_overview(symbol: str):
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": API_KEY
    }
    return _make_request(params)


def fetch_daily_time_series(symbol: str):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    return _make_request(params)