import requests
import time

URL = "http://127.0.0.1:8000/query"

headers = {
    "Authorization": "Bearer testtoken"
}

payload = {
    "query": "pe ratio less than 20",
    "page": 1,
    "page_size": 5
}

times = []

for i in range(100):
    start = time.time()
    r = requests.post(URL, json=payload, headers=headers)
    end = time.time()

    t = end - start
    times.append(t)
    print(f"Request {i+1}: {t:.3f}s")

print("\nAverage:", sum(times)/len(times))
print("Max:", max(times))
print("Min:", min(times))