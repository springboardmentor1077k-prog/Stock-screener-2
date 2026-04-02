# test_portfolio.py
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/portfolio"
USER_ID = 1  # Using demo user

def test_portfolio():
    print("=" * 60)
    print("TESTING PORTFOLIO API")
    print("=" * 60)
    
    # 1. Add stocks
    print("\n1. Adding stocks to portfolio...")
    stocks = [
        {"symbol": "AAPL", "quantity": 10, "price": 150.00, "notes": "Initial buy"},
        {"symbol": "MSFT", "quantity": 5, "price": 320.00, "notes": "Growth stock"},
        {"symbol": "GOOGL", "quantity": 3, "price": 135.00, "notes": "Tech leader"}
    ]
    
    for stock in stocks:
        response = requests.post(
            f"{BASE_URL}/add",
            params={"user_id": USER_ID},
            json=stock
        )
        if response.status_code == 200:
            print(f"  ✅ Added {stock['quantity']} shares of {stock['symbol']}")
        else:
            print(f"  ❌ Failed: {response.text}")
    
    # 2. Get portfolio
    print("\n2. Fetching portfolio...")
    response = requests.get(f"{BASE_URL}/holdings", params={"user_id": USER_ID})
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n  📊 Portfolio Summary:")
        print(f"     Total Investment: ${data['summary']['total_investment']:,.2f}")
        print(f"     Current Value: ${data['summary']['total_current_value']:,.2f}")
        print(f"     Profit/Loss: ${data['summary']['total_profit_loss']:,.2f}")
        print(f"     P&L %: {data['summary']['total_profit_loss_percentage']:.2f}%")
        
        print(f"\n  📈 Holdings:")
        for h in data['holdings']:
            print(f"     {h['symbol']}: {h['quantity']} shares @ ${h['average_price']:.2f}")
            print(f"     Current: ${h['current_price']:.2f} → P&L: ${h['profit_loss']:+.2f}")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    # 3. Add more shares
    print("\n3. Adding more AAPL shares...")
    response = requests.post(
        f"{BASE_URL}/add",
        params={"user_id": USER_ID},
        json={"symbol": "AAPL", "quantity": 5, "price": 165.00, "notes": "Additional buy"}
    )
    
    if response.status_code == 200:
        print("  ✅ Added 5 more AAPL shares")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    # 4. Partial sell
    print("\n4. Selling 2 MSFT shares...")
    response = requests.post(
        f"{BASE_URL}/remove",
        params={"user_id": USER_ID},
        json={"symbol": "MSFT", "quantity": 2}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ {data['message']}")
        print(f"     Sold at ${data['sell_details']['price']:.2f} for ${data['sell_details']['value']:.2f}")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    # 5. Get transaction history
    print("\n5. Transaction history...")
    response = requests.get(f"{BASE_URL}/transactions", params={"user_id": USER_ID, "limit": 10})
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {data['count']} transactions:")
        for tx in data['transactions'][:5]:
            print(f"     {tx['date'][:10]} - {tx['type']} {tx['quantity']} {tx['symbol']} @ ${tx['price']:.2f}")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    # 6. Add to watchlist
    print("\n6. Adding to watchlist...")
    response = requests.post(
        f"{BASE_URL}/watchlist/add",
        params={"user_id": USER_ID},
        json={"symbol": "NVDA", "alert_price": 900.00, "notes": "AI leader"}
    )
    
    if response.status_code == 200:
        print("  ✅ Added NVDA to watchlist")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    # 7. Get watchlist
    print("\n7. Watchlist...")
    response = requests.get(f"{BASE_URL}/watchlist", params={"user_id": USER_ID})
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Watchlist items:")
        for item in data['watchlist']:
            print(f"     {item['symbol']} - Alert: ${item['alert_price']}")
    else:
        print(f"  ❌ Failed: {response.text}")
    
    print("\n" + "=" * 60)
    print("✅ Portfolio testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_portfolio()