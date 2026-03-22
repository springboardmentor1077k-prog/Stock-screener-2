import requests

API_URL = "http://127.0.0.1:8000/query"

def run_query(query):

    params = {"user_query": query}

    response = requests.post(API_URL, params=params)

    return response.json()