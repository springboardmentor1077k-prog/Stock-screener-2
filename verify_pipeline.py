import requests
import json

API_BASE = "http://127.0.0.1:8000"

# 1. Login to get token
print("--- LOGGING IN ---")
login_res = requests.post(f"{API_BASE}/login", json={"username": "admin", "password": "admin123"})
if login_res.status_code != 200:
    print(f"Login failed: {login_res.text}")
    exit()

token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Run Test Query
query = "Show me companies with PE ratio less than 15"
print(f"\n--- RUNNING QUERY: '{query}' ---")

payload = {
    "query": query,
    "limit": 5,
    "page": 1,
    "sort_by": "pe_ratio",
    "sort_order": "asc"
}

res = requests.post(f"{API_BASE}/ask_ai", json=payload, headers=headers)
if res.status_code != 200:
    print(f"Query failed: {res.text}")
    exit()

data = res.json()

print("\n--- [LAYER: LLM] GENERATED DSL ---")
print(json.dumps(data.get("dsl", {}), indent=2))

# To get the exact SQL, I'll use the dsl to verify what it would produce
# But wait, the backend doesn't return SQL in the response for security.
# However, I can look at the logs if I have access.
# Or, I can run a manual compilation check in the script using the compiler logic.

from backend.compiler import compile_sql_from_dsl

sql, params = compile_sql_from_dsl(data.get("dsl", {}))
print("\n--- [LAYER: COMPILER] GENERATED SQL ---")
print(f"SQL: {sql}")
print(f"PARAMS: {params}")

print("\n--- [LAYER: DB] RESULTS ---")
results = data.get("results", [])
for r in results:
    print(f"- {r['symbol']}: {r['company_name']} | PE: {r['pe_ratio']}")

# Validation
print("\n--- VALIDATION ---")
for r in results:
    if r['pe_ratio'] >= 15:
        print(f"❌ FAIL: {r['symbol']} has PE {r['pe_ratio']} which is >= 15")
    else:
        print(f"✅ PASS: {r['symbol']} PE {r['pe_ratio']} is < 15")

print("\n--- PIPELINE VERIFICATION COMPLETE ---")
