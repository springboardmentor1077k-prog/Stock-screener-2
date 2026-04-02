# frontend/app.py (Updated with loading animations)
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# API URLs
API_BASE = "http://127.0.0.1:8000/api/v1"
API_URL = f"{API_BASE}/query"

# Page config
st.set_page_config(
    page_title="AI Stock Screener",
    page_icon="📈",
    layout="wide"
)

# Initialize session state variables
if 'previous_results' not in st.session_state:
    st.session_state.previous_results = None
    
if 'previous_query' not in st.session_state:
    st.session_state.previous_query = ""
    
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
    
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
    
if 'results_per_page' not in st.session_state:
    st.session_state.results_per_page = 10
    
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
    
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
    
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Screener"
    
if 'loading' not in st.session_state:
    st.session_state.loading = False

# Custom CSS with animations
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .history-item {
        padding: 0.5rem;
        border-radius: 0.25rem;
        background-color: #f8f9fa;
        margin: 0.25rem 0;
        cursor: pointer;
        border-left: 3px solid #007bff;
    }
    .history-item:hover {
        background-color: #e9ecef;
    }
    .profit {
        color: #28a745;
        font-weight: bold;
    }
    .loss {
        color: #dc3545;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Loading overlay animation */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.7);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    
    .loader {
        border: 5px solid #f3f3f3;
        border-top: 5px solid #3498db;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: white;
        margin-top: 20px;
        font-size: 18px;
        font-weight: bold;
    }
    
    .disabled-button {
        opacity: 0.5;
        pointer-events: none;
    }
    
    /* Disabled input styling */
    .stTextInput input:disabled {
        background-color: #f5f5f5;
        cursor: not-allowed;
    }
    
    .stNumberInput input:disabled {
        background-color: #f5f5f5;
        cursor: not-allowed;
    }
    
    /* Progress bar animation */
    @keyframes progress {
        0% { width: 0%; }
        100% { width: 100%; }
    }
    
    .progress-bar {
        height: 4px;
        background: linear-gradient(90deg, #4CAF50, #2196F3, #9C27B0);
        animation: progress 3s ease-in-out;
        width: 100%;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 10000;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to show loading animation
def show_loading(message="AI is analyzing your query...", duration=4):
    """Show loading animation and disable all interactions"""
    
    # Create a placeholder for the loading overlay
    loading_placeholder = st.empty()
    
    # Show loading animation with HTML/CSS
    loading_placeholder.markdown(f"""
    <div class="loading-overlay">
        <div class="loader"></div>
        <div class="loading-text">{message}</div>
        <div class="progress-bar"></div>
        <p style="color: white; margin-top: 20px;">Please wait... {duration} seconds</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Wait for specified duration
    time.sleep(duration)
    
    # Clear the loading overlay
    loading_placeholder.empty()

# Helper function to disable widgets
def disable_widgets():
    """Return CSS to disable all interactive elements"""
    return """
    <style>
        button:not(.st-emotion-cache-1rsyhoq):not(.st-emotion-cache-1v0mbdj) {
            pointer-events: none;
            opacity: 0.5;
        }
        .stTextInput input {
            pointer-events: none;
            background-color: #f5f5f5;
        }
        .stNumberInput input {
            pointer-events: none;
            background-color: #f5f5f5;
        }
        .stSelectbox {
            pointer-events: none;
            opacity: 0.5;
        }
        .stCheckbox {
            pointer-events: none;
            opacity: 0.5;
        }
        .stSlider {
            pointer-events: none;
            opacity: 0.5;
        }
        .stButton button {
            pointer-events: none;
            opacity: 0.5;
        }
        .stForm {
            pointer-events: none;
            opacity: 0.5;
        }
        .stExpander {
            pointer-events: none;
            opacity: 0.5;
        }
    </style>
    """

# Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
with col2:
    st.title("AI Stock Screener")
    st.markdown("*Natural language search for stock market data | Track portfolio | Set alerts*")

# Sidebar for history, settings, and user
with st.sidebar:
    st.header("👤 User Settings")
    user_id = st.number_input("User ID", min_value=1, value=st.session_state.user_id, step=1, disabled=st.session_state.loading)
    st.session_state.user_id = user_id
    st.divider()
    
    st.header("📜 Search History")
    
    if st.session_state.search_history:
        for i, history_item in enumerate(reversed(st.session_state.search_history[-5:])):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"🔍 {history_item['query'][:30]}...", key=f"hist_{i}", disabled=st.session_state.loading):
                    st.session_state.previous_query = history_item['query']
                    st.session_state.previous_results = history_item['results']
                    st.session_state.active_tab = "Screener"
                    st.rerun()
            with col2:
                st.caption(f"{history_item['count']} results")
        st.divider()
    else:
        st.info("No search history yet")
    
    st.header("⚙️ Settings")
    st.session_state.results_per_page = st.slider(
        "Results per page", 
        min_value=5, 
        max_value=50, 
        value=st.session_state.results_per_page,
        step=5,
        disabled=st.session_state.loading
    )
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True, disabled=st.session_state.loading):
        st.session_state.search_history = []
        st.session_state.previous_results = None
        st.session_state.previous_query = ""
        st.rerun()
    
    st.divider()
    st.caption(f"💡 Connected to FastAPI at {API_BASE}")

# Create tabs for different features
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Stock Screener", 
    "📊 Portfolio", 
    "👁️ Watchlist", 
    "🔔 Alerts"
])

# ==================== TAB 1: STOCK SCREENER ====================
with tab1:
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Query input with previous query preserved
        query = st.text_input(
            "🔍 Enter your query:",
            value=st.session_state.previous_query,
            placeholder="e.g., IT companies with PE ratio less than 20",
            key="query_input",
            disabled=st.session_state.loading
        )
    
    with col2:
        st.write("")
        st.write("")
        submit_button = st.button("🚀 Search", type="primary", use_container_width=True, disabled=st.session_state.loading)
    
    # Suggestions
    with st.expander("💡 Example Queries", expanded=True):
        suggestions = [
            "IT companies with PE ratio below 20",
            "Companies with PEG ratio less than 1",
            "Companies with promoter holding above 50",
            "Stocks with debt to FCF less than 0.5",
            "Companies with revenue greater than 10000",
            "Technology sector with PE between 15 and 25"
        ]
        
        cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(f"📌 {suggestion}", key=f"sugg_{i}", use_container_width=True, disabled=st.session_state.loading):
                    st.session_state.previous_query = suggestion
                    st.rerun()
    
    # Display previous results if they exist and no new search is triggered
    if st.session_state.previous_results is not None and not submit_button:
        results = st.session_state.previous_results
        current_query = st.session_state.previous_query
        
        st.success(f"📊 Showing previous results for: **{current_query}**")
        
        # Display results
        if len(results) == 0:
            st.warning("No results found")
        else:
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Results", len(results))
            with col2:
                st.metric("Current Page", st.session_state.current_page)
            with col3:
                st.metric("Results/Page", st.session_state.results_per_page)
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Pagination
            start_idx = (st.session_state.current_page - 1) * st.session_state.results_per_page
            end_idx = start_idx + st.session_state.results_per_page
            paginated_df = df.iloc[start_idx:end_idx]
            
            # Display table
            st.dataframe(
                paginated_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Add to Portfolio section for each result
            st.subheader("➕ Add to Portfolio")
            for idx, row in paginated_df.iterrows():
                with st.expander(f"Add {row.get('symbol', 'N/A')} - {row.get('company_name', 'N/A')[:50]}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        shares = st.number_input(
                            "Shares",
                            min_value=1,
                            value=10,
                            key=f"shares_{row['symbol']}_{idx}",
                            disabled=st.session_state.loading
                        )
                    with col2:
                        price = st.number_input(
                            "Price",
                            min_value=0.01,
                            value=float(row.get('pe_ratio', 100.00) * 10 if row.get('pe_ratio') else 100.00),
                            key=f"price_{row['symbol']}_{idx}",
                            disabled=st.session_state.loading
                        )
                    with col3:
                        if st.button(f"➕ Add {row['symbol']}", key=f"add_{row['symbol']}_{idx}", disabled=st.session_state.loading):
                            # Show loading animation
                            st.session_state.loading = True
                            show_loading(f"Adding {row['symbol']} to portfolio...", 2)
                            
                            add_response = requests.post(
                                f"{API_BASE}/portfolio/add",
                                params={"user_id": st.session_state.user_id},
                                json={
                                    "symbol": row['symbol'],
                                    "quantity": shares,
                                    "price": price,
                                    "notes": f"Added from screener on {datetime.now()}"
                                }
                            )
                            st.session_state.loading = False
                            
                            if add_response.status_code == 200:
                                st.success(f"✅ Added {shares} shares of {row['symbol']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to add")
            
            # Pagination controls
            total_pages = (len(results) + st.session_state.results_per_page - 1) // st.session_state.results_per_page
            
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("◀ First", disabled=st.session_state.current_page == 1 or st.session_state.loading):
                        st.session_state.current_page = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀ Prev", disabled=st.session_state.current_page == 1 or st.session_state.loading):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col3:
                    st.write(f"Page {st.session_state.current_page} of {total_pages}")
                
                with col4:
                    if st.button("Next ▶", disabled=st.session_state.current_page == total_pages or st.session_state.loading):
                        st.session_state.current_page += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ▶", disabled=st.session_state.current_page == total_pages or st.session_state.loading):
                        st.session_state.current_page = total_pages
                        st.rerun()
    
    # Handle new search
    if submit_button and query and not st.session_state.loading:
        # Show loading animation
        st.session_state.loading = True
        show_loading("🤖 AI is analyzing your query...", 4)
        
        with st.spinner(""):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "query": query,
                        "limit": 50,
                        "user_id": st.session_state.user_id
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        results = data.get("data", [])
                        
                        # Save to session state
                        st.session_state.previous_results = results
                        st.session_state.previous_query = query
                        st.session_state.current_page = 1
                        
                        # Add to history
                        st.session_state.search_history.append({
                            "query": query,
                            "count": len(results),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "results": results
                        })
                        
                        st.session_state.loading = False
                        st.rerun()
                    else:
                        st.session_state.loading = False
                        st.error(f"❌ Server error: {data.get('message', 'Unknown error')}")
                else:
                    st.session_state.loading = False
                    st.error(f"❌ API Error: Status code {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.session_state.loading = False
                st.error("❌ Cannot connect to backend. Make sure FastAPI is running!")
            except Exception as e:
                st.session_state.loading = False
                st.error(f"❌ Error: {str(e)}")

# ==================== TAB 2: PORTFOLIO ====================
with tab2:
    st.header("📊 Your Investment Portfolio")
    
    # Refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, disabled=st.session_state.loading):
            st.rerun()
    
    # Fetch portfolio with loading
    if not st.session_state.loading:
        with st.spinner("Loading portfolio..."):
            response = requests.get(
                f"{API_BASE}/portfolio/holdings",
                params={"user_id": st.session_state.user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("holdings"):
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            "Total Investment",
                            f"${data['summary']['total_investment']:,.2f}"
                        )
                    with col2:
                        st.metric(
                            "Current Value",
                            f"${data['summary']['total_current_value']:,.2f}"
                        )
                    with col3:
                        pl = data['summary']['total_profit_loss']
                        pl_pct = data['summary']['total_profit_loss_percentage']
                        st.metric(
                            "Profit/Loss",
                            f"${pl:+,.2f}",
                            delta=f"{pl_pct:+.2f}%",
                            delta_color="normal"
                        )
                    with col4:
                        st.metric(
                            "Holdings",
                            data['summary']['number_of_stocks']
                        )
                    
                    # Holdings table
                    st.subheader("📋 Holdings Details")
                    holdings_df = pd.DataFrame(data['holdings'])
                    display_df = holdings_df[[
                        'symbol', 'company_name', 'quantity', 'average_price',
                        'current_price', 'invested_value', 'current_value',
                        'profit_loss', 'profit_loss_percentage'
                    ]]
                    
                    # Format percentage column
                    display_df['profit_loss_percentage'] = display_df['profit_loss_percentage'].apply(
                        lambda x: f"{x:+.2f}%"
                    )
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Add manual stock
                    st.subheader("➕ Add Stock Manually")
                    with st.expander("Add new stock to portfolio", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            symbol = st.text_input("Symbol", placeholder="AAPL", disabled=st.session_state.loading)
                        with col2:
                            quantity = st.number_input("Quantity", min_value=1, value=10, disabled=st.session_state.loading)
                        with col3:
                            price = st.number_input("Price", min_value=0.01, value=100.00, disabled=st.session_state.loading)
                        with col4:
                            if st.button("➕ Add Stock", type="primary", disabled=st.session_state.loading):
                                if symbol:
                                    st.session_state.loading = True
                                    show_loading(f"Adding {symbol.upper()} to portfolio...", 2)
                                    
                                    add_response = requests.post(
                                        f"{API_BASE}/portfolio/add",
                                        params={"user_id": st.session_state.user_id},
                                        json={
                                            "symbol": symbol.upper(),
                                            "quantity": quantity,
                                            "price": price,
                                            "notes": "Manual addition"
                                        }
                                    )
                                    st.session_state.loading = False
                                    
                                    if add_response.status_code == 200:
                                        st.success(f"✅ Added {quantity} shares of {symbol.upper()}!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to add")
                    
                    # Remove stock
                    st.subheader("🗑️ Remove Stock")
                    with st.expander("Remove stock from portfolio", expanded=False):
                        symbols = [h['symbol'] for h in data['holdings']]
                        if symbols:
                            col1, col2 = st.columns(2)
                            with col1:
                                remove_symbol = st.selectbox("Select stock", options=symbols, disabled=st.session_state.loading)
                            with col2:
                                remove_all = st.checkbox("Remove all shares", value=True, disabled=st.session_state.loading)
                                if not remove_all:
                                    current_qty = next(h['quantity'] for h in data['holdings'] if h['symbol'] == remove_symbol)
                                    qty_to_remove = st.number_input(
                                        "Shares to remove",
                                        min_value=1,
                                        max_value=current_qty,
                                        value=1,
                                        disabled=st.session_state.loading
                                    )
                            if st.button("🗑️ Remove Stock", disabled=st.session_state.loading):
                                st.session_state.loading = True
                                show_loading(f"Removing {remove_symbol} from portfolio...", 2)
                                
                                remove_data = {"symbol": remove_symbol}
                                if not remove_all:
                                    remove_data["quantity"] = qty_to_remove
                                
                                remove_response = requests.post(
                                    f"{API_BASE}/portfolio/remove",
                                    params={"user_id": st.session_state.user_id},
                                    json=remove_data
                                )
                                st.session_state.loading = False
                                
                                if remove_response.status_code == 200:
                                    st.success(f"✅ Removed {remove_symbol} from portfolio")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Failed to remove")
                    
                    # Transaction history
                    st.subheader("📜 Transaction History")
                    tx_response = requests.get(
                        f"{API_BASE}/portfolio/transactions",
                        params={"user_id": st.session_state.user_id, "limit": 20}
                    )
                    
                    if tx_response.status_code == 200:
                        tx_data = tx_response.json()
                        if tx_data.get("transactions"):
                            tx_df = pd.DataFrame(tx_data["transactions"])
                            st.dataframe(tx_df, use_container_width=True)
                        else:
                            st.info("No transactions yet")
                else:
                    st.info("Your portfolio is empty. Search for stocks in the Screener tab to add them!")
            else:
                st.error("Failed to load portfolio")
    else:
        st.info("Please wait, portfolio is loading...")

# ==================== TAB 3: WATCHLIST ====================
with tab3:
    st.header("👁️ Watchlist")
    
    # Add to watchlist
    with st.form("add_to_watchlist"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            watch_symbol = st.text_input("Stock Symbol", placeholder="NVDA", disabled=st.session_state.loading)
        with col2:
            alert_price = st.number_input("Alert Price (optional)", min_value=0.0, value=0.0, disabled=st.session_state.loading)
        with col3:
            submitted = st.form_submit_button("➕ Add to Watchlist", use_container_width=True, disabled=st.session_state.loading)
        
        if submitted and watch_symbol and not st.session_state.loading:
            st.session_state.loading = True
            show_loading(f"Adding {watch_symbol.upper()} to watchlist...", 2)
            
            response = requests.post(
                f"{API_BASE}/portfolio/watchlist/add",
                params={"user_id": st.session_state.user_id},
                json={
                    "symbol": watch_symbol.upper(),
                    "alert_price": alert_price if alert_price > 0 else None,
                    "notes": "Added from UI"
                }
            )
            st.session_state.loading = False
            
            if response.status_code == 200:
                st.success(f"✅ Added {watch_symbol.upper()} to watchlist")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to add")
    
    # Display watchlist
    st.markdown("---")
    if not st.session_state.loading:
        watch_response = requests.get(
            f"{API_BASE}/portfolio/watchlist",
            params={"user_id": st.session_state.user_id}
        )
        
        if watch_response.status_code == 200:
            watch_data = watch_response.json()
            if watch_data.get("watchlist"):
                watch_df = pd.DataFrame(watch_data["watchlist"])
                st.dataframe(watch_df, use_container_width=True)
                
                # Remove from watchlist
                st.subheader("Remove from Watchlist")
                symbols = [w['symbol'] for w in watch_data['watchlist']]
                if symbols:
                    remove_symbol = st.selectbox("Select stock to remove", options=symbols, key="watch_remove", disabled=st.session_state.loading)
                    if st.button("🗑️ Remove from Watchlist", disabled=st.session_state.loading):
                        st.session_state.loading = True
                        show_loading(f"Removing {remove_symbol} from watchlist...", 2)
                        
                        remove_response = requests.delete(
                            f"{API_BASE}/portfolio/watchlist/remove",
                            params={"user_id": st.session_state.user_id, "symbol": remove_symbol}
                        )
                        st.session_state.loading = False
                        
                        if remove_response.status_code == 200:
                            st.success(f"✅ Removed {remove_symbol} from watchlist")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to remove")
            else:
                st.info("Your watchlist is empty. Add stocks to monitor!")
        else:
            st.error("Failed to load watchlist")
    else:
        st.info("Loading watchlist...")

# ==================== TAB 4: ALERTS ====================
with tab4:
    st.header("🔔 Price Alerts")
    
    # Create alert
    with st.form("create_alert"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            alert_symbol = st.text_input("Symbol", placeholder="AAPL", disabled=st.session_state.loading)
        with col2:
            alert_name = st.text_input("Alert Name", placeholder="Price Target", disabled=st.session_state.loading)
        with col3:
            operator = st.selectbox("Condition", options=[">", "<", ">=", "<="], disabled=st.session_state.loading)
        with col4:
            alert_value = st.number_input("Price", min_value=0.01, value=200.00, disabled=st.session_state.loading)
        
        submitted = st.form_submit_button("➕ Create Alert", use_container_width=True, disabled=st.session_state.loading)
        
        if submitted and alert_symbol and not st.session_state.loading:
            st.session_state.loading = True
            show_loading(f"Creating alert for {alert_symbol.upper()}...", 2)
            
            response = requests.post(
                f"{API_BASE}/alerts/price",
                params={"user_id": st.session_state.user_id},
                json={
                    "alert_name": alert_name or f"{alert_symbol} Alert",
                    "symbol": alert_symbol.upper(),
                    "operator": operator,
                    "value": alert_value,
                    "notes": f"Alert when {alert_symbol} {operator} ${alert_value}"
                }
            )
            st.session_state.loading = False
            
            if response.status_code == 200:
                st.success(f"✅ Alert created for {alert_symbol.upper()}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to create alert")
    
    # Display alerts
    st.markdown("---")
    st.subheader("Your Active Alerts")
    
    if not st.session_state.loading:
        alerts_response = requests.get(
            f"{API_BASE}/alerts/",
            params={"user_id": st.session_state.user_id}
        )
        
        if alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
            if alerts_data.get("alerts"):
                for alert in alerts_data["alerts"]:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"**{alert['alert_name']}**")
                        with col2:
                            st.write(f"{alert['symbol']} {alert['condition_operator']} ${alert['condition_value']}")
                        with col3:
                            status = "✅ Active" if alert['is_active'] else "⏸️ Inactive"
                            st.write(status)
                        with col4:
                            if st.button(f"Toggle", key=f"toggle_{alert['id']}", disabled=st.session_state.loading):
                                st.session_state.loading = True
                                show_loading(f"Toggling alert status...", 1)
                                
                                toggle_response = requests.patch(
                                    f"{API_BASE}/alerts/{alert['id']}/toggle",
                                    params={"user_id": st.session_state.user_id, "is_active": not alert['is_active']}
                                )
                                st.session_state.loading = False
                                
                                if toggle_response.status_code == 200:
                                    st.rerun()
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{alert['id']}", disabled=st.session_state.loading):
                            st.session_state.loading = True
                            show_loading(f"Deleting alert...", 1)
                            
                            delete_response = requests.delete(
                                f"{API_BASE}/alerts/{alert['id']}",
                                params={"user_id": st.session_state.user_id}
                            )
                            st.session_state.loading = False
                            
                            if delete_response.status_code == 200:
                                st.success("Alert deleted")
                                time.sleep(1)
                                st.rerun()
                        st.markdown("---")
            else:
                st.info("No alerts created yet")
        else:
            st.error("Failed to load alerts")
    else:
        st.info("Loading alerts...")

# Footer
st.divider()
st.caption("🔄 State is preserved across interactions. Results persist until you perform a new search.")