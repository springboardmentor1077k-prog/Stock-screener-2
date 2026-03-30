import yfinance as yf

def calculate_new_average_price(old_qty: int, old_avg_price: float, new_qty: int, new_buy_price: float) -> float:
    """Computes the new cost basis using the weighted average cost method."""
    if old_qty == 0:
        return float(new_buy_price)
        
    total_old_cost = old_qty * float(old_avg_price)
    total_new_cost = new_qty * float(new_buy_price)
    
    total_cumulative_qty = old_qty + new_qty
    total_cumulative_cost = total_old_cost + total_new_cost
    
    return round(float(total_cumulative_cost) / total_cumulative_qty, 2)

def fetch_live_price(symbol: str) -> float:
    """
    Connects to the Yahoo Finance API dynamically. 
    Never store this in the Database! Always fetch on-demand.
    """
    try:
        ticker = yf.Ticker(symbol)
        # Fast extraction of current price
        todays_data = ticker.history(period='1d')
        if not todays_data.empty:
            return round(float(todays_data['Close'].iloc[-1]), 2)
        return 0.0
    except Exception:
        # Fallback if API fails to prevent the app from crashing entirely
        return 0.0
