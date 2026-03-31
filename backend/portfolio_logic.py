import logging
import time

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance is not installed. Live prices will not be available.")

# Simple in-memory cache: { "SYMBOL": {"price": 150.5, "timestamp": 1690000000} }
PRICE_CACHE = {}
CACHE_EXPIRY_SECONDS = 60

def clear_price_cache():
    """Clears all cached prices when user requests a refresh."""
    global PRICE_CACHE
    PRICE_CACHE.clear()

def format_symbol_for_yfinance(symbol: str) -> str:
    """
    Format symbol for yfinance. Adds .NS for Indian stocks if not present.
    In future, this can be extended for BSE (.BO) or other exchanges.
    """
    symbol = symbol.upper().strip()
    if "." not in symbol:
        return f"{symbol}.NS"
    return symbol

def get_current_price(symbol: str) -> float:
    """
    Fetches the latest market price for a given stock symbol using Yahoo Finance.
    
    [SWAP_API_HERE] Future: To swap in a different API like Alpha Vantage or NSE API,
    simply replace the yfinance logic below with the new API integration.
    """
    if not YFINANCE_AVAILABLE or not symbol:
        return 0.0
        
    original_symbol = symbol.upper().strip()
    formatted_symbol = format_symbol_for_yfinance(original_symbol)
    
    now = time.time()
    if original_symbol in PRICE_CACHE:
        cache_entry = PRICE_CACHE[original_symbol]
        if now - cache_entry["timestamp"] < CACHE_EXPIRY_SECONDS:
            return cache_entry["price"]
            
    try:
        ticker = yf.Ticker(formatted_symbol)
        last_price = None
        
        # 1. Try fast_info
        try:
            last_price = ticker.fast_info.last_price
        except Exception:
            pass
            
        # 2. Fallback to download
        if last_price is None or last_price == 0.0:
            df = yf.download(formatted_symbol, period='1d', progress=False)
            if not df.empty and 'Close' in df:
                last_price = float(df['Close'].iloc[-1])
                
        if last_price and last_price > 0.0:
            last_price = round(float(last_price), 2)
            PRICE_CACHE[original_symbol] = {"price": last_price, "timestamp": now}
            return last_price
            
        print(f"Error: Price fetch failed for {formatted_symbol}. No valid data returned.")
        return 0.0
    except Exception as e:
        print(f"Error fetching market price for {formatted_symbol}: {str(e)}")
        # Rate limit handling simple fallback delay
        time.sleep(0.5) 
        return 0.0

def get_multiple_prices(symbols: list) -> dict:
    """
    Batch price fetching: fetch all symbols in one single yfinance call to optimize performance.
    """
    if not YFINANCE_AVAILABLE or not symbols:
        return {s.upper(): 0.0 for s in symbols}
        
    now = time.time()
    results = {}
    symbols_to_fetch = []
    
    # 1. Check cache first
    for sym in symbols:
        sym_upper = sym.upper().strip()
        if sym_upper in PRICE_CACHE and (now - PRICE_CACHE[sym_upper]["timestamp"] < CACHE_EXPIRY_SECONDS):
            results[sym_upper] = PRICE_CACHE[sym_upper]["price"]
        else:
            symbols_to_fetch.append(sym_upper)
            
    if not symbols_to_fetch:
        return results
        
    formatted_to_orig = {format_symbol_for_yfinance(s): s for s in symbols_to_fetch}
    formatted_symbols = list(formatted_to_orig.keys())
    
    try:
        # 2. Batch fetch via download
        df = yf.download(formatted_symbols, period='1d', progress=False)
        time.sleep(0.1) # small delay to be safe with yfinance
        
        for sym in formatted_symbols:
            orig = formatted_to_orig[sym]
            try:
                p = None
                if len(formatted_symbols) == 1:
                    if not df.empty and 'Close' in df:
                        val = df['Close'].iloc[-1]
                        if str(val).lower() != 'nan':
                            p = float(val)
                else:
                    if not df.empty and 'Close' in df and sym in df['Close']:
                        val = df['Close'][sym].dropna().iloc[-1]
                        if str(val).lower() != 'nan':
                            p = float(val)
                            
                if p is not None and p > 0.0:
                    p = round(p, 2)
                    results[orig] = p
                    PRICE_CACHE[orig] = {"price": p, "timestamp": time.time()}
                else:
                    raise ValueError("No data")
            except Exception:
                # 3. Fallback to individual fetch
                print(f"Batch fetch failed for {sym}. Falling back to individual.")
                results[orig] = get_current_price(orig)
    except Exception as e:
        print(f"Batch fetch entirely failed: {e}. Falling back to individual fetching.")
        for orig in symbols_to_fetch:
            results[orig] = get_current_price(orig)
            
    return results

def calculate_unrealized_pnl(buy_price: float, current_price: float, quantity: int) -> dict:
    """
    Calculates the unrealized profit or loss components for a single stock holding.
    
    Formulas: 
        profit_or_loss = (current_price - buy_price) * quantity
        percentage_change = ((current_price - buy_price) / buy_price) * 100
        total_invested = buy_price * quantity
        current_value = current_price * quantity
        
    Args:
        buy_price (float): Original average purchase price.
        current_price (float): Latest market price.
        quantity (int): Number of shares held.
        
    Returns:
        dict: Performance metrics for the holding.
    """
    if quantity <= 0:
        return {"profit_or_loss": 0.0, "percentage_change": 0.0, "total_invested": 0.0, "current_value": 0.0}
    
    total_invested = buy_price * quantity
    current_value = current_price * quantity
    profit_or_loss = current_value - total_invested
    
    percentage_change = 0.0
    if buy_price > 0:
        percentage_change = ((current_price - buy_price) / buy_price) * 100
        
    return {
        "profit_or_loss": round(profit_or_loss, 2),
        "percentage_change": round(percentage_change, 2),
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2)
    }

def calculate_average_buy_price(old_quantity: int, old_buy_price: float, new_quantity: int, new_buy_price: float) -> float:
    """
    Calculates the new weighted average cost basis after an additional purchase.
    
    Formula: ((old_quantity * old_buy_price) + (new_quantity * new_buy_price)) / (old_quantity + new_quantity)
    
    Args:
        old_quantity (int): Shares held before the new trade.
        old_buy_price (float): Previous cost basis per share.
        new_quantity (int): Shares being added.
        new_buy_price (float): Price of the additional purchase.
        
    Returns:
        float: Updated average buy price per share.
    """
    total_combined_qty = old_quantity + new_quantity
    if total_combined_qty == 0:
        return 0.0
        
    total_old_cost = old_quantity * old_buy_price
    total_new_cost = new_quantity * new_buy_price
    
    new_avg_price = (total_old_cost + total_new_cost) / total_combined_qty
    return round(new_avg_price, 2)

def calculate_realized_pnl(buy_price: float, sell_price: float, quantity_sold: int) -> float:
    """
    Calculates the actual profit or loss made when a position is liquidated.
    
    Formula: (sell_price - buy_price) * quantity_sold
    
    Args:
        buy_price (float): Original average purchase price.
        sell_price (float): Price at which the shares were sold.
        quantity_sold (int): Number of shares liquidated.
        
    Returns:
        float: The realized profit or loss amount.
    """
    realized_val = (sell_price - buy_price) * quantity_sold
    return round(realized_val, 2)

def handle_partial_sell(current_quantity: int, sell_quantity: int, buy_price: float, sell_price: float) -> dict:
    """
    Validates a sell-off and calculates remaining state + realized gains.
    
    Args:
        current_quantity (int): Number of shares currently held.
        sell_quantity (int): Number of shares requested to sell.
        buy_price (float): Current average purchase price.
        sell_price (float): Price of the sell execution.
        
    Returns:
        dict: Summary of the sell operation.
    """
    if sell_quantity > current_quantity:
        raise ValueError("Cannot sell more shares than currently held.")
        
    remaining_quantity = current_quantity - sell_quantity
    realized_pnl = calculate_realized_pnl(buy_price, sell_price, sell_quantity)
    
    return {
        "remaining_quantity": remaining_quantity,
        "realized_pnl": realized_pnl,
        "is_position_closed": remaining_quantity == 0
    }

def calculate_portfolio_summary(holdings: list) -> dict:
    """
    Aggregates metrics across the entire user portfolio to provide overall health.
    
    Args:
        holdings (list): List of holdings, each containing pre-calculated current/buy prices & quantities.
        
    Returns:
        dict: Total portfolio summary statistics.
    """
    if not holdings:
        return {
            "total_invested": 0.0, "total_current_value": 0.0, "total_pnl": 0.0,
            "overall_percentage_change": 0.0, "total_holdings": 0,
            "profitable_holdings": 0, "loss_holdings": 0
        }
        
    total_invested = sum(h.get('total_invested', 0.0) for h in holdings)
    total_current_value = sum(h.get('current_value', 0.0) for h in holdings)
    total_pnl = total_current_value - total_invested
    
    overall_percentage_change = 0.0
    if total_invested > 0:
        overall_percentage_change = (total_pnl / total_invested) * 100
        
    total_holdings = len(holdings)
    # profit_or_loss > 0 is profitable. (profit_or_loss < 0 is loss)
    # profit_or_loss == 0 is break-even.
    profitable_count = sum(1 for h in holdings if h.get('profit_or_loss', 0.0) > 0)
    loss_count = sum(1 for h in holdings if h.get('profit_or_loss', 0.0) < 0)
    
    return {
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current_value, 2),
        "total_pnl": round(total_pnl, 2),
        "overall_percentage_change": round(overall_percentage_change, 2),
        "total_holdings": total_holdings,
        "profitable_holdings": profitable_count,
        "loss_holdings": loss_count
    }
