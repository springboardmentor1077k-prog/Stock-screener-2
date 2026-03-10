import yfinance as yf
import json
import os

# Create output folder
if not os.path.exists("output"):
    os.makedirs("output")

symbol = "AAPL"

print("API Exploration using Yahoo Finance (yfinance library)")
print("Base Endpoint used internally:")
print("https://query1.finance.yahoo.com\n")

ticker = yf.Ticker(symbol)

# ==============================
# API CALL 1 — Company Information
# ==============================

print("API Call 1: Company Information Endpoint")
print("Endpoint: https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}\n")

company_info = ticker.info

print("Company Info JSON:")
print(json.dumps(company_info, indent=4))

with open("output/company_info.json", "w") as f:
    json.dump(company_info, f, indent=4)

print("Company info saved to output/company_info.json\n")


# ==============================
# API CALL 2 — Historical Data
# ==============================

print("API Call 2: Historical Stock Data Endpoint")
print("Endpoint: https://query1.finance.yahoo.com/v8/finance/chart/{symbol}\n")

history = ticker.history(period="1mo")

# Convert DataFrame safely to JSON
history_json_string = history.reset_index().to_json(orient="records")
history_json = json.loads(history_json_string)

print("Historical Data JSON:")
print(json.dumps(history_json, indent=4))

with open("output/historical_data.json", "w") as f:
    json.dump(history_json, f, indent=4)

print("Historical data saved to output/historical_data.json\n")


# ==============================
# API CALL 3 — Financial Metrics
# ==============================

print("API Call 3: Financial Metrics Endpoint")
print("Endpoint: https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}/financialData\n")

financials = ticker.financials

# Convert financial DataFrame safely
financials_json_string = financials.to_json()
financials_json = json.loads(financials_json_string)

print("Financial Metrics JSON:")
print(json.dumps(financials_json, indent=4))

with open("output/financial_metrics.json", "w") as f:
    json.dump(financials_json, f, indent=4)

print("Financial metrics saved to output/financial_metrics.json\n")

print("All API calls completed successfully.")