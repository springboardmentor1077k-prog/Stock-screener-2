import requests
import json

API_KEY = "Y70WRHDF7C7B3RTG"
SYMBOL = "AAPL"

# 1️⃣ Historical Price Data
def fetch_historical_prices():
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={SYMBOL}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    print("Historical Price Data:")
    print(json.dumps(data, indent=2))

    with open("historical_prices.json", "w") as f:
        json.dump(data, f, indent=2)

# 2️⃣ Company Overview (Fundamentals)
def fetch_company_overview():
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={SYMBOL}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    print("\nCompany Overview:")
    print(json.dumps(data, indent=2))

    with open("company_overview.json", "w") as f:
        json.dump(data, f, indent=2)

# 3️⃣ Income Statement (Fundamental Metric)
def fetch_income_statement():
    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={SYMBOL}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    print("\nIncome Statement:")
    print(json.dumps(data, indent=2))

    with open("income_statement.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    fetch_historical_prices()
    fetch_company_overview()
    fetch_income_statement()




                 