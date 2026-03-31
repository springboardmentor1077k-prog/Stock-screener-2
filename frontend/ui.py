import streamlit as st
import requests
import pandas as pd
import time

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Vault Engine Pro", page_icon="🏦", layout="wide")

# ==========================================
# REFINED, ELEGANT CSS (ONLY ESSENTIALS)
# Native Streamlit theming handles the rest beautifully!
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global App Background */
    .stApp {
        background-color: #0A0D14;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, sans-serif;
    }
    
    /* Hero Title / Fonts */
    .hero-title {
        font-weight: 800;
        font-size: 2.8rem !important;
        background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: left;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        color: #94A3B8 !important;
        font-size: 1.10rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        margin-bottom: 30px;
        text-align: left;
    }
    
    /* Elegant Tab Styling mimicking top brokers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #1C2333;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #94A3B8;
        font-weight: 600;
        font-size: 14px;
        padding-bottom: 12px;
        padding-top: 12px;
    }
    .stTabs [aria-selected="true"] {
        color: #3B82F6 !important;
        border-bottom: 2px solid #3B82F6 !important;
    }
    
    /* Streamlit DataFrame Borders & background */
    [data-testid="stDataFrame"] {
        border-radius: 8px !important;
        overflow: hidden;
        border: 1px solid #1C2333 !important;
        background-color: #111622;
    }
    
    /* Primary Buttons (Compute, Execute, etc) */
    .stButton > button {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
        transform: scale(0.98) !important;
    }
    .stButton > button:active {
        transform: scale(0.95) !important;
    }

    /* Secondary / Form Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #111622 !important;
        color: #F8FAFC !important;
        border: 1px solid #1C2333 !important;
        border-radius: 8px !important;
    }
    
    /* Focus states */
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.5) !important;
    }

    /* Top Padding Management */
    .block-container {
        padding-top: 2.5rem !important;
        max-width: 1200px !important;
    }

    /* Sidebar Alignment */
    [data-testid="stSidebar"] {
        background-color: #0A0D14 !important;
        border-right: 1px solid #1C2333 !important;
    }
</style>
""", unsafe_allow_html=True)

if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None


# ==========================================
# PAGE 1: AUTHENTICATION PORTAL 
# ==========================================
if st.session_state['token'] is None:
    st.markdown('<div class="hero-title">Vault Engine Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Deterministic Financial Discovery</div>', unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔒 Secure Authenticate", "👤 Create Data Identity"])
        
        with tab1:
            st.markdown("<h4 style='text-align:center; color:#E2E8F0; margin-bottom: 20px;'>Welcome Back.</h4>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=True):
                login_user = st.text_input("Username")
                login_pwd = st.text_input("Password", type="password")
                st.write("<br>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("Authenticate Query Identity", type="primary", width='stretch')
                
            if submit_login:
                if login_user and login_pwd:
                    res = requests.post(f"{API_BASE}/login", json={"username": login_user, "password": login_pwd})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state['token'] = data.get("access_token")
                        st.session_state['user'] = login_user
                        st.session_state['user_id'] = data.get("user_id")
                        st.rerun()
                    else:
                        st.error(f"❌ {res.json().get('detail', 'Login Failed')}")
                else:
                    st.warning("Please enter credentials.")

        with tab2:
            st.markdown("<h4 style='text-align:center; color:#E2E8F0; margin-bottom: 20px;'>Deploy New Identity</h4>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=True):
                reg_user = st.text_input("Choose Username")
                reg_email = st.text_input("Corporate Email Address")
                reg_pwd = st.text_input("Strong Master Key", type="password")
                st.write("<br>", unsafe_allow_html=True)
                submit_register = st.form_submit_button("Initialize Account Node", type="primary", width='stretch')
                
            if submit_register:
                if reg_user and reg_email and reg_pwd:
                    with st.spinner("Provisioning Database Node Identifiers..."):
                        time.sleep(0.5)
                        res = requests.post(f"{API_BASE}/register", json={"username": reg_user, "email": reg_email, "password": reg_pwd})
                        if res.status_code == 200:
                            st.success("✅ Account successfully initialized. You may now authenticate.")
                        else:
                            st.error(res.json().get("detail", "Registration Failed"))
                else:
                    st.warning("All cryptographic parameters (fields) are required.")


# ==========================================
# PAGE 2: MAIN SCREENER DASHBOARD
# ==========================================
else:
    with st.sidebar:
        st.markdown(f"### 👤 Analyst: `{st.session_state['user']}`")
        st.markdown("<div style='color: #10B981; font-weight: 600; font-size: 0.9rem;'>🟢 Secure Subnet Active</div>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        
        st.markdown("<p style='color: #8B5CF6; font-weight: 600; margin-bottom: 5px;'>🔐 Backend Architecture</p>", unsafe_allow_html=True)
        st.caption("• **Parser:** OpenAI NLP Engine")
        st.caption("• **Engine:** Parametric DSL Compiler")
        st.caption("• **Database:** PostgreSQL Encrypted")
        st.caption("• **Defense:** JWT + Anti-Injection Layer")
        
        st.write("<br>", unsafe_allow_html=True)
        view_selection = st.radio("Navigation Menu", ["🔍 Market Screener", "📊 My Portfolio"])
        st.write("<br>", unsafe_allow_html=True)

        if st.button("🔌 Terminate Session", width='stretch'):
            st.session_state['token'] = None
            st.session_state['user'] = None
            st.rerun()

    if view_selection == "📊 My Portfolio":
        from portfolio_ui import render_portfolio
        render_portfolio(st.session_state['token'], API_BASE, st.session_state['user_id'])
        st.stop() # Halts rendering of the screener code when in portfolio mode
        
    st.markdown('<div class="hero-title" style="text-align:left; font-size:2.8rem !important; padding-top:0;">Natural Language DSL Engine</div>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -10px; margin-bottom: 30px;'>Run advanced corporate equity screens translated strictly from linguistic intents via our secure parametric compiler.</p>", unsafe_allow_html=True)

    # Search Bar Section
    st.markdown("<h4 style='color: #E2E8F0; margin-bottom: -15px;'>💻 AI Query Console</h4>", unsafe_allow_html=True)
    user_query = st.text_input("Console Input", placeholder="e.g. Find me healthcare companies with PE less than 20 and revenue above 50000", help="Type natural English.", label_visibility="collapsed")
    
    # Elegant Filter Columns
    st.write("<br>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    with col_f1:
        sort_by = st.selectbox("Sort Variable", ["pe_ratio", "revenue", "ebitda", "debt_to_equity", "company_name", "sector", "symbol"])
    with col_f2:
        sort_order = st.selectbox("Trajectory", ["asc", "desc"])
    with col_f3:
        limit = st.number_input("Node Pool Limit", min_value=1, max_value=100, value=15)
    with col_f4:
        page = st.number_input("Network Page", min_value=1, value=1)
    with col_f5:
        time_options = {
            "No Time Filter": None,
            "Last 1 Quarter": 1,
            "Last 2 Quarters": 2,
            "Last 4 Quarters": 4,
            "Last 8 Quarters": 8,
            "Last 12 Quarters": 12
        }
        time_sel = st.selectbox("Time Horizon", list(time_options.keys()))
        selected_time_filter = time_options[time_sel]
        
    st.write("<br>", unsafe_allow_html=True)

    # Big compute button centered
    _, center_btn, _ = st.columns([1, 2, 1])
    with center_btn:
        search_clicked = st.button("☄️ Compute Distributed Search", type="primary", width='stretch')

    if search_clicked:
        if not user_query:
            st.error("⚠️ Command Console is empty. Input required.")
        else:
            with st.spinner("Initializing NLP ➡ Compiling DSL ➡ Parameterizing SQL Arrays ➡ Fetching Node Cache"):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                payload = {
                    "query": user_query,
                    "sort_by": sort_by.strip(),
                    "sort_order": sort_order.strip(),
                    "limit": limit,
                    "page": page,
                    "time_filter": selected_time_filter
                }
                res = requests.post(f"{API_BASE}/ask_ai", json=payload, headers=headers)
                
                if res.status_code == 200:
                    data = res.json()
                    st.success("✅ Deterministic compilation complete. Results strictly parameterized & fetched.")
                    
                    if "data" in data and len(data["data"]) > 0:
                        df = pd.DataFrame(data["data"])
                        # Apply some styling to dataframe
                        styled_df = df.style.set_properties(**{'background-color': '#1E293B', 'color': '#E2E8F0', 'border-color': 'rgba(255,255,255,0.05)'})
                        st.dataframe(styled_df, width='stretch', hide_index=True)
                    else:
                        st.info("ℹ️ Your strict logic criteria evaluated to an empty local dataset.")
                        
                    with st.expander("🛠️ Advanced Compiler Provenance Logs"):
                        st.write("### 📜 Intermediate Validated Node AST (JSON DSL)")
                        st.json(data.get("dsl", {}))
                        
                elif res.status_code == 401:
                    st.error("Authentication expired. Terminate session and re-authenticate.")
                else:
                    try:
                        st.error(f"Execution Halt: Code {res.status_code} - {res.json().get('detail')}")
                    except:
                        st.error(f"Fatal Compiler Interruption Code {res.status_code}")
