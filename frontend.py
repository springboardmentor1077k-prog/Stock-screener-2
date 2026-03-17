import streamlit as st
import requests
import pandas as pd

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Aura AI - Pro Screener", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# 2. PRO-LEVEL CSS (Glassmorphism, Background, Top Nav)
st.markdown("""
    <style>
    /* Hide the default Streamlit Sidebar and Top Bar to look like a real web app */
    [data-testid="collapsedControl"] { display: none; }
    header { visibility: hidden; }

    /* Custom Background Image with Dark Overlay */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    
    /* Deep dark overlay so text is highly readable */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(10, 15, 30, 0.85); 
        z-index: 0;
    }

    /* Elevate the main content */
    .main {
        z-index: 1;
    }
    
    /* Glassmorphism Effect for the Main Container */
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

    /* Top Navigation Buttons (FB/Insta Style) */
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
    
    /* Primary search button glowing effect */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        border: none;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    }

    /* Search Input Box */
    .stTextInput>div>div>input {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.15);
        background-color: rgba(0, 0, 0, 0.5);
        color: white;
        font-size: 16px;
        padding: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. STATE MANAGEMENT
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Screener"

def set_query(text):
    st.session_state.query_text = text

# ---------------------------------------------------------
# TOP NAVIGATION BAR (Like Facebook / Insta Tabs)
# ---------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: white; font-weight: 800; letter-spacing: 2px;'>AURA<span style='color: #00C6FF;'>.AI</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A0AEC0; margin-top: -15px; margin-bottom: 25px;'>Next-Gen Financial Intelligence</p>", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    if st.button("🔍 Smart Screener", use_container_width=True): st.session_state.current_page = "Screener"
with nav2:
    if st.button("📊 Portfolio", use_container_width=True): st.session_state.current_page = "Portfolio"
with nav3:
    if st.button("⭐ Watchlist", use_container_width=True): st.session_state.current_page = "Watchlist"
with nav4:
    if st.button("🔔 Alerts", use_container_width=True): st.session_state.current_page = "Alerts"

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE LOGIC
# ---------------------------------------------------------
if st.session_state.current_page == "Screener":
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        query = st.text_input("Search", placeholder="e.g., Show me high growth IT stocks with zero debt...", 
                              value=st.session_state.query_text, label_visibility="collapsed")
    with col_btn:
        search_clicked = st.button("🚀 Search", type="primary", use_container_width=True)

    # Dynamic Tags
    tag1, tag2, tag3, tag4 = st.columns([1, 1, 1, 1])
    with tag1:
        if st.button("🔥 PE < 15", use_container_width=True): set_query("Show companies with pe_ratio < 15"); st.rerun()
    with tag2:
        if st.button("💎 Zero Debt", use_container_width=True): set_query("Show companies with debt = 0"); st.rerun()
    with tag3:
        if st.button("🚀 High Revenue", use_container_width=True): set_query("Show companies with revenue > 20000"); st.rerun()
    with tag4:
        if st.button("👑 Top Promoters", use_container_width=True): set_query("Show companies with promoter_holding > 50"); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # API Call & Logic
    if search_clicked:
        if query:
            with st.spinner("🧠 AI is analyzing your query..."):
                try:
                    response = requests.post("http://localhost:8000/query", json={"query": query})
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("data", data.get("results", []))
                        
                        if results:
                            st.session_state.results_df = pd.DataFrame(results)
                        else:
                            st.session_state.results_df = pd.DataFrame()
                            st.warning("⚠️ No stocks matched your exact criteria. Try adjusting the filters.")
                    
                    # 🔥 KOTHA ERROR HANDLING LOGIC 🔥
                    else:
                        error_response = response.json()
                        # Backend nunchi vache exact error ento laguthunnam
                        raw_error = str(error_response.get('detail', error_response.get('message', 'Unknown Error')))
                        
                        # Validation errors leda garbage input errors vasthe
                        if "validation" in raw_error.lower() or "least 1 item" in raw_error.lower() or response.status_code == 422:
                            st.warning("⚠️ I couldn't understand that query. Please try asking about stocks or financials (e.g., 'Show me IT companies').")
                            st.session_state.results_df = pd.DataFrame() # Clear the old table
                        else:
                            st.error("❌ Something went wrong while processing your query. Please try again.")
                            
                except Exception as e:
                    st.error("🚨 Connection Refused: Please check if your FastAPI server is running.")
        else:
            st.info("💡 Please type a query to start screening.")

    # Display Results
    df = st.session_state.results_df
    if not df.empty:
        st.markdown("<h3 style='color: white;'>📊 Market Insights</h3>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Stocks Found", f"{len(df)} Matches")
        if 'pe_ratio' in df.columns:
            m2.metric("Average PE", f"{df['pe_ratio'].mean():.1f}")
        if 'market_cap' in df.columns:
            m3.metric("Highest Market Cap", f"₹{df['market_cap'].max() / 1000:.1f}K")
        
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 Data Table", "📈 Statistical Summary"])
        
        with tab1:
            st.dataframe(df, use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(df.describe(), use_container_width=True)

else:
    # Logic for other pages (Portfolio, Watchlist, etc.)
    st.markdown(f"<h2 style='text-align: center; color: white; margin-top: 50px;'>🚧 {st.session_state.current_page}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00C6FF;'>Syncing your data... Advanced features coming in the next update!</p>", unsafe_allow_html=True)