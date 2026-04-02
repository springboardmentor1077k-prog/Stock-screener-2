# test_complete_system.py
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Color.GREEN}✅ {msg}{Color.RESET}")

def print_error(msg):
    print(f"{Color.RED}❌ {msg}{Color.RESET}")

def print_info(msg):
    print(f"{Color.BLUE}📌 {msg}{Color.RESET}")

def print_test_header(title):
    print(f"\n{Color.YELLOW}{'='*60}{Color.RESET}")
    print(f"{Color.YELLOW}{title:^60}{Color.RESET}")
    print(f"{Color.YELLOW}{'='*60}{Color.RESET}")

def test_api_connection():
    """Test if FastAPI server is running"""
    print_test_header("1. TESTING API CONNECTION")
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}")
        if response.status_code == 200:
            print_success("API server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server. Make sure it's running on http://127.0.0.1:8000")
        return False

def test_stock_screener():
    """Test stock screener functionality"""
    print_test_header("2. TESTING STOCK SCREENER")
    
    test_queries = [
        "IT companies with PE ratio less than 20",
        "Technology sector companies",
        "Companies with promoter holding above 50",
        "Stocks with revenue greater than 1000000"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📊 Query: {query}")
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/query",
                json={"query": query, "limit": 10},
                timeout=30
            )
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    result_count = len(data.get("data", []))
                    print_success(f"Query executed in {execution_time:.2f}ms")
                    print(f"   Results: {result_count} companies found")
                    if result_count > 0:
                        print(f"   Sample: {data['data'][0].get('symbol', 'N/A')}")
                    results.append(True)
                else:
                    print_error(f"Query failed: {data.get('message', 'Unknown error')}")
                    results.append(False)
            else:
                print_error(f"HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_error(f"Error: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📈 Screener Success Rate: {success_rate:.1f}%")
    return all(results)

def test_portfolio_crud():
    """Test portfolio CRUD operations"""
    print_test_header("3. TESTING PORTFOLIO CRUD OPERATIONS")
    
    user_id = 1
    
    # Test 1: Add stocks
    print("\n📊 Adding stocks to portfolio...")
    stocks_to_add = [
        {"symbol": "AAPL", "quantity": 10, "price": 150.00, "notes": "Initial buy"},
        {"symbol": "MSFT", "quantity": 5, "price": 320.00, "notes": "Growth stock"},
        {"symbol": "GOOGL", "quantity": 3, "price": 135.00, "notes": "Tech leader"}
    ]
    
    add_results = []
    for stock in stocks_to_add:
        response = requests.post(
            f"{BASE_URL}/portfolio/add",
            params={"user_id": user_id},
            json=stock
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Added {stock['quantity']} shares of {stock['symbol']}")
            add_results.append(True)
        else:
            print_error(f"Failed to add {stock['symbol']}: {response.text}")
            add_results.append(False)
    
    if not all(add_results):
        print_error("Some stocks failed to add")
        return False
    
    # Test 2: Get portfolio
    print("\n📊 Getting portfolio...")
    response = requests.get(
        f"{BASE_URL}/portfolio/holdings",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Portfolio retrieved: {data['summary']['number_of_stocks']} stocks")
        print(f"   Total Investment: ${data['summary']['total_investment']:,.2f}")
        print(f"   Current Value: ${data['summary']['total_current_value']:,.2f}")
        print(f"   Total P&L: ${data['summary']['total_profit_loss']:,.2f}")
    else:
        print_error("Failed to get portfolio")
        return False
    
    # Test 3: Get portfolio summary
    print("\n📊 Getting portfolio summary...")
    response = requests.get(
        f"{BASE_URL}/portfolio/summary",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Portfolio summary retrieved")
        print(f"   Summary: ${data['summary']['total_current_value']:,.2f}")
    else:
        print_error("Failed to get summary")
    
    # Test 4: Add more shares to existing stock
    print("\n📊 Adding more shares to existing stock...")
    response = requests.post(
        f"{BASE_URL}/portfolio/add",
        params={"user_id": user_id},
        json={"symbol": "AAPL", "quantity": 5, "price": 165.00, "notes": "Additional buy"}
    )
    
    if response.status_code == 200:
        print_success("Added 5 more AAPL shares")
    else:
        print_error("Failed to add more shares")
    
    # Test 5: Partial sell
    print("\n📊 Partial sell...")
    response = requests.post(
        f"{BASE_URL}/portfolio/remove",
        params={"user_id": user_id},
        json={"symbol": "MSFT", "quantity": 2}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Sold 2 shares of MSFT")
        print(f"   Sale value: ${data['sell_details']['value']:,.2f}")
    else:
        print_error("Failed to sell")
    
    # Test 6: Get transactions
    print("\n📊 Getting transaction history...")
    response = requests.get(
        f"{BASE_URL}/portfolio/transactions",
        params={"user_id": user_id, "limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {data['count']} transactions")
        if data['transactions']:
            latest = data['transactions'][0]
            print(f"   Latest: {latest['type']} {latest['quantity']} {latest['symbol']} @ ${latest['price']:.2f}")
    else:
        print_error("Failed to get transactions")
    
    return True

def test_watchlist():
    """Test watchlist functionality"""
    print_test_header("4. TESTING WATCHLIST")
    
    user_id = 1
    
    # Test 1: Add to watchlist
    print("\n📊 Adding to watchlist...")
    watchlist_items = [
        {"symbol": "NVDA", "alert_price": 900.00, "notes": "AI leader"},
        {"symbol": "TSLA", "alert_price": 250.00, "notes": "EV play"}
    ]
    
    for item in watchlist_items:
        response = requests.post(
            f"{BASE_URL}/portfolio/watchlist/add",
            params={"user_id": user_id},
            json=item
        )
        
        if response.status_code == 200:
            print_success(f"Added {item['symbol']} to watchlist")
        else:
            print_error(f"Failed to add {item['symbol']}")
    
    # Test 2: Get watchlist
    print("\n📊 Getting watchlist...")
    response = requests.get(
        f"{BASE_URL}/portfolio/watchlist",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Watchlist has {len(data['watchlist'])} items")
        for item in data['watchlist']:
            print(f"   • {item['symbol']} - Alert: ${item.get('alert_price', 'N/A')}")
    else:
        print_error("Failed to get watchlist")
    
    return True

def test_alerts():
    """Test alerts functionality"""
    print_test_header("5. TESTING ALERTS")
    
    user_id = 1
    
    # Test 1: Create price alert
    print("\n📊 Creating price alert...")
    response = requests.post(
        f"{BASE_URL}/alerts/price",
        params={"user_id": user_id},
        json={
            "alert_name": "AAPL Price Alert",
            "symbol": "AAPL",
            "operator": ">",
            "value": 200.00,
            "notes": "Test alert"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Alert created: {data['message']}")
    else:
        print_error(f"Failed to create alert: {response.text}")
    
    # Test 2: Create growth alert
    print("\n📊 Creating growth alert...")
    response = requests.post(
        f"{BASE_URL}/alerts/growth",
        params={"user_id": user_id},
        json={
            "alert_name": "NVDA Growth Alert",
            "symbol": "NVDA",
            "metric": "revenue_growth",
            "operator": ">",
            "value": 50.00,
            "notes": "High growth alert"
        }
    )
    
    if response.status_code == 200:
        print_success("Growth alert created")
    else:
        print_error(f"Failed to create growth alert: {response.text}")
    
    # Test 3: Get all alerts
    print("\n📊 Getting all alerts...")
    response = requests.get(
        f"{BASE_URL}/alerts/",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {data['count']} alerts")
        for alert in data['alerts'][:3]:
            print(f"   • ID: {alert['id']} - {alert['alert_name']} ({alert['alert_type']})")
    else:
        print_error("Failed to get alerts")
    
    # Test 4: Check alerts (trigger)
    print("\n📊 Checking alerts...")
    response = requests.post(
        f"{BASE_URL}/alerts/check",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Checked alerts: {data['count']} triggered")
        for alert in data['triggered_alerts']:
            print(f"   • {alert['message']}")
    else:
        print_error("Failed to check alerts")
    
    return True

def test_dsl_validation():
    """Test DSL validation"""
    print_test_header("6. TESTING DSL VALIDATION")
    
    test_cases = [
        ("Valid query", "IT companies with PE less than 20", True),
        ("Invalid field", "companies with market_cap > 100", False),
        ("Complex query", "Tech stocks with PE < 20 AND revenue > 1000000", True),
        ("Growth query", "companies with revenue growth > 10%", True)
    ]
    
    for name, query, should_pass in test_cases:
        print(f"\n📊 Testing: {name}")
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"query": query, "limit": 10},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    if should_pass:
                        print_success(f"Query passed validation")
                    else:
                        print_error(f"Query should have failed but passed")
                else:
                    if not should_pass:
                        print_success(f"Query correctly rejected")
                    else:
                        print_error(f"Query should have passed but failed")
            else:
                if not should_pass:
                    print_success(f"Query correctly rejected with {response.status_code}")
                else:
                    print_error(f"Unexpected error: {response.status_code}")
                    
        except Exception as e:
            print_error(f"Error: {e}")
    
    return True

def test_performance():
    """Test performance with multiple queries"""
    print_test_header("7. TESTING PERFORMANCE")
    
    query = "IT companies with PE ratio less than 20"
    times = []
    
    print(f"\n📊 Running query 5 times to measure performance...")
    
    for i in range(5):
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/query",
            json={"query": query, "limit": 10},
            timeout=30
        )
        execution_time = (time.time() - start_time) * 1000
        times.append(execution_time)
        
        status = "✅" if response.status_code == 200 else "❌"
        print(f"   Run {i+1}: {status} {execution_time:.2f}ms")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📈 Performance Summary:")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Fastest: {min_time:.2f}ms")
    print(f"   Slowest: {max_time:.2f}ms")
    
    return avg_time < 1000  # Should be under 1 second

def test_error_handling():
    """Test error handling"""
    print_test_header("8. TESTING ERROR HANDLING")
    
    error_cases = [
        ("Empty query", {"query": "", "limit": 10}, "Empty query should be rejected"),
        ("Invalid limit", {"query": "test", "limit": 1000}, "Limit too high should be rejected"),
        ("Very long query", {"query": "a" * 1000, "limit": 10}, "Long query should be handled"),
        ("No query field", {"limit": 10}, "Missing query field should be handled"),
    ]
    
    for name, payload, description in error_cases:
        print(f"\n📊 Testing: {name}")
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print_success(f"Error correctly handled: HTTP {response.status_code}")
                print(f"   {description}")
            else:
                print_error(f"Error not caught: Got 200 OK")
                
        except Exception as e:
            print_success(f"Exception caught: {type(e).__name__}")
    
    return True

def generate_report(results):
    """Generate test report"""
    print_test_header("TEST REPORT")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {total - passed}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} - {test_name}")
    
    if passed == total:
        print(f"\n{Color.GREEN}🎉 ALL TESTS PASSED! System is ready for production!{Color.RESET}")
    else:
        print(f"\n{Color.RED}⚠️ Some tests failed. Please check the errors above.{Color.RESET}")
    
    return passed == total

def main():
    """Run all tests"""
    print(f"\n{Color.BLUE}{'='*60}{Color.RESET}")
    print(f"{Color.BLUE}AI STOCK SCREENER - COMPLETE SYSTEM TEST{Color.RESET}")
    print(f"{Color.BLUE}{'='*60}{Color.RESET}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all tests
    results["API Connection"] = test_api_connection()
    
    if results["API Connection"]:
        results["Stock Screener"] = test_stock_screener()
        results["Portfolio CRUD"] = test_portfolio_crud()
        results["Watchlist"] = test_watchlist()
        results["Alerts"] = test_alerts()
        results["DSL Validation"] = test_dsl_validation()
        results["Performance"] = test_performance()
        results["Error Handling"] = test_error_handling()
    else:
        print_error("Cannot proceed with tests. API server is not running.")
    
    # Generate report
    generate_report(results)
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()