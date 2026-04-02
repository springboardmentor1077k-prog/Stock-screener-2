import requests

API_URL = "http://127.0.0.1:8000/query"

def run_query(query):
    try:
        params = {"user_query": query}

        response = requests.post(API_URL, params=params)

        data = response.json()
        print("API RESPONSE:", data)  # 👈 DEBUG

        return data

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }