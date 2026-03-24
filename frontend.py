import streamlit as st
import requests
import pandas as pd

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="AI - Pro Stock Screener", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# 2.CSS
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    header { visibility: hidden; }
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(10, 15, 30, 0.85); 
        z-index: 0;
    }
    .main { z-index: 1; }
    .block-container {
        background: rgba(25, 30, 45, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        margin-top: 2rem;
    }
    div.stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
        background: rgba(255,255,255,0.05);
        color: #A0AEC0;
        font-weight: 600;
        transition: all 0.3s ease;
        height: 45px;
    }
    div.stButton > button:hover {
        background: rgba(0, 198, 255, 0.15);
        border-color: #00C6FF;
        color: white;
        transform: translateY(-2px);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        border: none;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.15);
        background-color: rgba(0, 0, 0, 0.5);
        color: white;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. STATE MANAGEMENT
if "query_text" not in st.session_state: st.session_state.query_text = ""
if "results_df" not in st.session_state: st.session_state.results_df = pd.DataFrame()
if "current_page" not in st.session_state: st.session_state.current_page = "Screener"

def set_query(text): st.session_state.query_text = text

# ---------------------------------------------------------
# TOP NAVIGATION BAR
# ---------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: white; font-weight: 800; letter-spacing: 2px;'>AURA<span style='color: #00C6FF;'>.AI</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A0AEC0; margin-top: -15px; margin-bottom: 25px;'>Next-Gen Financial Intelligence</p>", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    if st.button("🔍 Smart Screener", use_container_width=True): st.session_state.current_page = "Screener"; st.rerun()
with nav2:
    if st.button("📊 Portfolio", use_container_width=True): st.session_state.current_page = "Portfolio"; st.rerun()
with nav3:
    if st.button("⭐ Watchlist", use_container_width=True): st.session_state.current_page = "Watchlist"; st.rerun()
with nav4:
    if st.button("🔔 Alerts", use_container_width=True): st.session_state.current_page = "Alerts"; st.rerun()

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# =========================================================
# PAGE 1: SMART SCREENER
# =========================================================
if st.session_state.current_page == "Screener":
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        query = st.text_input("Search", placeholder="e.g., Show me high growth IT stocks with zero debt...", 
                              value=st.session_state.query_text, label_visibility="collapsed")
    with col_btn:
        search_clicked = st.button("🚀 Search", type="primary", use_container_width=True)

    tag1, tag2, tag3, tag4 = st.columns([1, 1, 1, 1])
    with tag1:
        if st.button("🔥 PE < 15", use_container_width=True): set_query("Show companies with pe_ratio < 15"); st.rerun()
    with tag2:
        if st.button("💎 Zero Debt", use_container_width=True): set_query("Show companies with debt = 0"); st.rerun()
    with tag3:
        if st.button("🚀 High Revenue", use_container_width=True): set_query("Show companies with revenue > 20000"); st.rerun()
    with tag4:
        if st.button("👑 Top Promoters", use_container_width=True): set_query("Show companies with promoter_holding > 50"); st.rerun()

    if search_clicked:
        if query:
            with st.spinner("🧠 AI is analyzing your query..."):
                try:
                    response = requests.post("http://localhost:8000/query", json={"query": query})
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("data", data.get("results", []))
                        st.session_state.results_df = pd.DataFrame(results) if results else pd.DataFrame()
                        if not results: st.warning("⚠️ No stocks matched your exact criteria.")
                    else:
                        st.error("❌ Something went wrong while processing your query. Please try again.")
                except Exception as e:
                    st.error("🚨 Connection Refused: Please check if your FastAPI server is running.")

    df = st.session_state.results_df
    if not df.empty:
        st.markdown("<br><h3 style='color: white;'>📊 Market Insights</h3>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 🔥 ADD TO PORTFOLIO SECTION
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #00C6FF;'>💼 Add to Portfolio</h4>", unsafe_allow_html=True)
        
        p_col1, p_col2, p_col3, p_col4 = st.columns([2, 1, 1, 1])
        with p_col1:
            selected_symbol = st.selectbox("Select Stock", options=df['symbol'].tolist(), label_visibility="collapsed")
        with p_col2:
            quantity = st.number_input("Quantity", min_value=1, value=10, step=1, label_visibility="collapsed")
        with p_col3:
            default_price = float(df[df['symbol'] == selected_symbol]['pe_ratio'].values[0] * 100) if 'pe_ratio' in df.columns else 1000.0
            buy_price = st.number_input("Buy Price (₹)", min_value=1.0, value=default_price, step=10.0, label_visibility="collapsed")
        with p_col4:
            if st.button("➕ Add Stock", type="primary", use_container_width=True):
                payload = {"user_id": "user1", "symbol": selected_symbol, "quantity": quantity, "buy_price": buy_price}
                res = requests.post("http://localhost:8000/portfolio/add", json=payload)
                if res.status_code == 200:
                    st.success(res.json().get("message", "Added successfully!"))
                else:
                    st.error("Failed to add to portfolio.")

# =========================================================
# PAGE 2: PORTFOLIO
# =========================================================
elif st.session_state.current_page == "Portfolio":
    st.markdown("<h2 style='color: white;'>📈 Your Investment Portfolio</h2>", unsafe_allow_html=True)
    
    with st.spinner("Fetching your portfolio..."):
        try:
            response = requests.get("http://localhost:8000/portfolio/user1")
            if response.status_code == 200:
                port_data = response.json().get("data", [])
                
                if port_data:
                    port_df = pd.DataFrame(port_data)
                    
                    def color_profit(val):
                        color = '#00FF00' if val > 0 else '#FF4B4B' if val < 0 else 'white'
                        return f'color: {color}'
                    
                    styled_df = port_df.style.map(color_profit, subset=['profit_loss', 'profit_percentage'])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("<br><h5>🗑️ Remove Stock</h5>", unsafe_allow_html=True)
                    del_col1, del_col2 = st.columns([2, 1])
                    with del_col1:
                        del_id = st.selectbox("Select Portfolio ID to remove", options=port_df['id'].tolist())
                    with del_col2:
                        if st.button("Remove from Portfolio", type="primary"):
                            del_res = requests.delete(f"http://localhost:8000/portfolio/{del_id}")
                            if del_res.status_code == 200:
                                st.success("Deleted successfully!")
                                st.rerun()
                else:
                    st.info("💼 Your portfolio is empty. Go to Smart Screener to add some stocks!")
        except Exception as e:
            st.error("🚨 Failed to connect to the backend API.")

# =========================================================
# PAGE 3: ALERTS 
# =========================================================
elif st.session_state.current_page == "Alerts":
    st.markdown("<h2 style='color: white;'>🔔 Intelligent Market Alerts</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A0AEC0;'>Set conditions and let our AI monitor the market for you.</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Create Alert", "📋 Manage & System Check"])
    
    # --- TAB 1: CREATE ALERT ---
    with tab1:
        st.markdown("<br><h4 style='color: #00C6FF;'>Define your trigger condition</h4>", unsafe_allow_html=True)
        with st.form("alert_form"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                a_symbol = st.text_input("Symbol", placeholder="e.g., INFY")
            with col2:
                a_field = st.selectbox("Metric", ["pe_ratio", "revenue", "debt", "market_cap", "ebitda", "promoter_holding"])
            with col3:
                a_op = st.selectbox("Condition", ["<", "<=", ">", ">=", "="])
            with col4:
                a_val = st.number_input("Target Value", value=15.0)
            
            submit_alert = st.form_submit_button("🔔 Set Active Alert", type="primary")
            
            if submit_alert and a_symbol:
                payload = {
                    "user_id": "user1",
                    "symbol": a_symbol.upper(),
                    "field": a_field,
                    "operator": a_op,
                    "value": a_val,
                    "alert_type": "metric"
                }
                res = requests.post("http://localhost:8000/alert/add", json=payload)
                if res.status_code == 200:
                    st.success(f"✅ Alert successfully created for {a_symbol.upper()}!")
                else:
                    st.error("❌ Failed to create alert.")

    # --- TAB 2: MANAGE & EVALUATE ---
    with tab2:
        st.markdown("<br><h4>Your Active Alerts</h4>", unsafe_allow_html=True)
        
        try:
            res = requests.get("http://localhost:8000/alerts/user1")
            if res.status_code == 200:
                alerts_data = res.json().get("data", [])
                if alerts_data:
                    st.dataframe(pd.DataFrame(alerts_data), use_container_width=True, hide_index=True)
                    
                    del_col1, del_col2 = st.columns([2, 1])
                    with del_col1:
                        del_id = st.selectbox("Select Alert ID to Delete", options=[a['id'] for a in alerts_data])
                    with del_col2:
                        if st.button("🗑️ Delete Alert"):
                            del_res = requests.delete(f"http://localhost:8000/alert/{del_id}")
                            if del_res.status_code == 200:
                                st.success("Alert Deleted!")
                                st.rerun()
                else:
                    st.info("No active alerts at the moment.")
            
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            
            st.markdown("<h4>🧠 Run System Evaluation</h4>", unsafe_allow_html=True)
            st.caption("In production, this runs automatically via cron jobs. For this demo, we trigger it manually.")
            
            if st.button("🚀 Check Market Conditions Now", type="primary", use_container_width=True):
                with st.spinner("Analyzing market data against your alert conditions..."):
                    eval_res = requests.get("http://localhost:8000/alerts/check/user1")
                    if eval_res.status_code == 200:
                        triggered = eval_res.json().get("triggered", [])
                        if triggered:
                            for t in triggered:
                                st.error(t["message"], icon="🚨")
                            st.success("✅ Check complete. Triggered alerts have been logged and deactivated.")
                        else:
                            st.success("✅ Check complete. All metrics are within your safe limits. No alerts triggered.")
        except Exception as e:
            st.error("🚨 Failed to connect to the backend API.")

# =========================================================
# PAGE 4: FALLBACK / OTHERS
# =========================================================
else:
    st.markdown(f"<h2 style='text-align: center; color: white; margin-top: 50px;'>🚧 {st.session_state.current_page}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00C6FF;'>Syncing your data... Advanced features coming soon!</p>", unsafe_allow_html=True)