# test.py
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_query(query_text):
    """Test a single query"""
    print("=" * 60)
    print(f"Query: {query_text}")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "query": query_text,
                "limit": 10,
                "user_id": 1
            }
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Results Count: {len(data.get('data', []))}")
            
            if data.get('data'):
                print("\nFirst 3 results:")
                for i, item in enumerate(data['data'][:3], 1):
                    print(f"  {i}. {item.get('symbol')} - {item.get('company_name', 'N/A')[:40]}")
                    print(f"     Sector: {item.get('sector', 'N/A')} | PE: {item.get('pe_ratio', 'N/A')}")
            else:
                print("\n⚠️ No results found")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Start with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test different queries
    queries = [
        "Technology companies",
        "Healthcare stocks with PE ratio less than 20",
        "Companies with PE ratio less than 20"
    ]
    
    for query in queries:
        test_query(query)
        print("\n" + "-" * 60 + "\n")