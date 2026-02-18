import requests
import json

API_KEY = "YOUR_API_KEY"

# 1️ Company Overview (Company Info)
overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL&apikey={API_KEY}"
overview_response = requests.get(overview_url)
overview_data = overview_response.json()

print("Company Overview:")
print(json.dumps(overview_data, indent=4))

with open("company_overview.json", "w") as f:
    json.dump(overview_data, f, indent=4)


# 2️ Fundamental Metric (Income Statement)
income_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=AAPL&apikey={API_KEY}"
income_response = requests.get(income_url)
income_data = income_response.json()

print("\nIncome Statement:")
print(json.dumps(income_data, indent=4))

with open("income_statement.json", "w") as f:
    json.dump(income_data, f, indent=4)


# 3️ Historical Daily Prices
price_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={API_KEY}"
price_response = requests.get(price_url)
price_data = price_response.json()

print("\nHistorical Prices:")
print(json.dumps(price_data, indent=4))

with open("historical_prices.json", "w") as f:
    json.dump(price_data, f, indent=4)
