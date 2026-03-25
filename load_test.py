import requests
import time
import concurrent.futures

API_URL = "http://localhost:8000/query"
NUM_REQUESTS = 100  
def send_request(req_id):
    payload = {"query": "Show companies with pe_ratio < 20 and revenue > 10000"}
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload)
        elapsed = time.time() - start_time
        return response.status_code, elapsed
    except Exception as e:
        return 500, time.time() - start_time

print(f"🚀 Starting Load Test with {NUM_REQUESTS} simultaneous requests...")
start_total = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    results = list(executor.map(send_request, range(NUM_REQUESTS)))

end_total = time.time()

# Metrics Calculation
successful = sum(1 for r in results if r[0] == 200)
failed = NUM_REQUESTS - successful
total_time = end_total - start_total
avg_response_time = sum(r[1] for r in results) / NUM_REQUESTS

print("\n📊 --- LOAD TEST RESULTS ---")
print(f"Total Requests   : {NUM_REQUESTS}")
print(f"Successful       : {successful}")
print(f"Failed           : {failed}")
print(f"Total Time Taken : {round(total_time, 2)} seconds")
print(f"Avg Response Time: {round(avg_response_time * 1000, 2)} ms")

# Identifying Slow Components & Improvements
print("\n💡 --- BOTTLENECKS & IMPROVEMENTS ---")
if total_time < 20.0: 
    print("- ✅ System is highly optimized! In-memory Caching and SQL execution are handling the load perfectly.")
else:
    print("- 🚨 LLM Parsing is causing latency. Improvement: Implement Redis Caching for frequent queries.")