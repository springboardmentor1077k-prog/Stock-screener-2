import streamlit as st
import requests
import pandas as pd
import time

API_BASE = "http://127.0.0.1:8000"

# Bottleneck 4: Persistent Requests Session
@st.cache_resource
def get_session():
    return requests.Session()

# Bottleneck 4: Fragment decorator to prevent whole page re-run
@st.fragment
def render_results_table(data_list):
    if data_list and len(data_list) > 0:
        df = pd.DataFrame(data_list)
        # Dynamic theme-aware dataframe styling
        df_bg = "#111622" if st.session_state.get('theme') == 'dark' else "#F8FAFC"
        df_text = "#F8FAFC" if st.session_state.get('theme') == 'dark' else "#1E293B"
        styled_df = df.style.set_properties(**{'background-color': df_bg, 'color': df_text, 'border-color': 'rgba(128,128,128,0.1)'})
        st.dataframe(styled_df, width='stretch', hide_index=True)
    else:
        st.info("ℹ️ Your strict logic criteria evaluated to an empty local dataset.")

# Bottleneck 4: Memoize heavy requests automatically 
def fetch_screener_data(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    sess = get_session()
    
    max_retries = 3
    retry_delays = [0.5, 1.0, 2.0] # Exponential backoff
    
    for attempt in range(max_retries):
        try:
            # Task 2 & 3: Handle Timeout and Retry
            res = sess.post(f"{API_BASE}/ask_ai", json=payload, headers=headers, timeout=12)
            
            # Task 2: Handle Server Error (500)
            if res.status_code == 500:
                return 500, "SERVER_ERROR", None
            
            # Task 2: Handle Invalid Input (400)
            if res.status_code == 400:
                return 400, "INVALID_INPUT", res.json()
                
            # Attempt to parse JSON - Task 2: Handle JSON Decode Error
            try:
                data = res.json()
                return res.status_code, "SUCCESS", data
            except ValueError:
                return res.status_code, "JSON_ERROR", None
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                # Task 3: Visible retry indicator
                st.warning(f"⏱️ Request timed out. Retrying... attempt {attempt + 1} of {max_retries}")
                time.sleep(retry_delays[attempt])
                continue
            return 408, "TIMEOUT", None
            
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                # Task 3: Visible retry indicator
                st.warning(f"🔄 Network issue. Retrying... attempt {attempt + 1} of {max_retries}")
                time.sleep(retry_delays[attempt])
                continue
            return 503, "NETWORK_ERROR", None
            
        except Exception as e:
            # Task 2: Handle Unexpected Error
            return 0, "UNEXPECTED", str(e)
            
    return 0, "FAILED_ALL_RETRIES", None

st.set_page_config(page_title="AI Powered Stock Screener", page_icon="🏦", layout="wide")

# ==========================================
# GLOBAL STATE & THEME CONFIGURATION
# ==========================================
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'user' not in st.session_state:
    st.session_state['user'] = None

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- THEME TOKENS ---
if st.session_state['theme'] == 'dark':
    BG_COLOR = "#0D1117"
    TEXT_COLOR = "#F8FAFC"
    SUBTEXT_COLOR = "#94A3B8"
    SIDEBAR_BG = "#0D1117"
    INPUT_BG = "#111622"
    BORDER_COLOR = "#1C2333"
    CARD_BG = "#161B22"
    ACCENT_COLOR = "#3B82F6"
else:
    BG_COLOR = "#FFFFFF"
    TEXT_COLOR = "#1E293B"
    SUBTEXT_COLOR = "#64748B"
    SIDEBAR_BG = "#F8FAFC"
    INPUT_BG = "#F1F5F9"
    BORDER_COLOR = "#E2E8F0"
    CARD_BG = "#F8FAFC"
    ACCENT_COLOR = "#2563EB"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global App Background */
    .stApp {{
        background-color: {BG_COLOR};
        color: {TEXT_COLOR};
        font-family: 'Inter', system-ui, sans-serif;
    }}
    
    /* Hero Title / Fonts */
    .hero-title {{
        font-weight: 800;
        font-size: 2.8rem !important;
        background: linear-gradient(135deg, {TEXT_COLOR} 0%, {SUBTEXT_COLOR} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: left;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }}
    
    .hero-subtitle {{
        color: {SUBTEXT_COLOR} !important;
        font-size: 1.10rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        margin-bottom: 30px;
        text-align: left;
    }}
    
    /* Sidebar Alignment */
    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG} !important;
        border-right: 1px solid {BORDER_COLOR} !important;
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {{
        background-color: {INPUT_BG} !important;
        color: {TEXT_COLOR} !important;
        border: 1px solid {BORDER_COLOR} !important;
        border-radius: 8px !important;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}
    
    /* Horizontal lines */
    hr {{
        border-color: {BORDER_COLOR} !important;
    }}

    /* Metrics and cards */
    [data-testid="stMetricValue"] {{
        color: {TEXT_COLOR} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ==========================================
# PAGE 1: AUTHENTICATION PORTAL 
# ==========================================
if st.session_state['token'] is None:
    st.markdown('<div class="hero-title">AI Powered Stock Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Intelligent Capital Allocation & Discovery</div>', unsafe_allow_html=True)
    
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
        # Task 2: Light/Dark Mode Toggle
        if st.session_state['theme'] == 'dark':
            if st.button("☀️ Light Mode", use_container_width=True):
                st.session_state['theme'] = 'light'
                st.rerun()
        else:
            if st.button("🌙 Dark Mode", use_container_width=True):
                st.session_state['theme'] = 'dark'
                st.rerun()
        
        st.markdown("---") # Simple divider line
        
        # Task 1 & 3: Minimalist Sidebar content
        st.markdown("**Navigation Menu**")
        nav_choice = st.radio(
            "Navigation Selection", 
            ["🔍 Market Screener", "💼 My Portfolio", "🔔 Alerts"],
            label_visibility="collapsed",
            index=0
        )
    
    # Task 3: Sidebar logic is complete, now for rendering
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🔌 Log Out", use_container_width=True):
         st.session_state['token'] = None
         st.rerun()
    
    # Render logic
    if nav_choice == "💼 My Portfolio":
        from portfolio_ui import render_portfolio
        render_portfolio(st.session_state['token'], API_BASE, st.session_state['user_id'])
        st.stop()
    elif nav_choice == "🔔 Alerts":
        from alerts_ui import render_alerts
        render_alerts(st.session_state['token'], API_BASE, st.session_state['user_id'])
        st.stop()
    
    # Default: Continue rendering Market Screener content below
        
    # --- HERO SECTION ---
    st.markdown(f'<div class="hero-title" style="text-align:left; font-size:2.8rem !important; padding-top:0; color:{TEXT_COLOR};">AI Powered Stock Screener</div>', unsafe_allow_html=True)
    st.markdown(f"<p style='color: {SUBTEXT_COLOR}; font-size: 1.05rem; margin-top: -10px; margin-bottom: 30px;'>AI-driven capital discovery and parametric stock screening translated from natural language intents.</p>", unsafe_allow_html=True)

    # --- MARKET SNAPSHOT (Task: Add project-related content) ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Tracked Nodes", "1,240", delta="+12")
    with m_col2:
        st.metric("Avg PE Ratio", "24.2", delta="-1.1")
    with m_col3:
        st.metric("Volatility (VIX)", "18.4", delta="0.5")
    with m_col4:
        st.metric("System Health", "99.9%", delta="Stable")

    st.write("---")

    # --- SAMPLE QUERIES SECTION ---
    st.markdown(f"<h5 style='color: {TEXT_COLOR};'>💡 Institutional Sample Queries</h5>", unsafe_allow_html=True)
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        st.info("Find healthcare companies with PE less than 20 and revenue above 50,000")
    with q_col2:
        st.info("Show me tech stocks with debt to equity ratio below 0.5")
    with q_col3:
        st.info("List energy symbols with EBITDA growth over 15% last quarter")

    st.write("<br>", unsafe_allow_html=True)

    # Search Bar Section
    st.markdown(f"<h4 style='color: {TEXT_COLOR}; margin-bottom: -15px;'>💻 AI Query Console</h4>", unsafe_allow_html=True)
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
                status_code, err_type, data = fetch_screener_data(payload, st.session_state['token'])
                
                if status_code == 200:
                    results = data.get("results", [])
                    if results and len(results) > 0:
                        st.success("✅ Deterministic compilation complete. Results strictly parameterized & fetched.")
                        # Renders ONLY the dataframe natively without reloading entire sidebar/UI tree
                        render_results_table(results)
                    else:
                        # Task 1: Handle empty results with a friendly message
                        st.info("🔍 No companies found for your query. Try adjusting your filters.")
                        
                    if data.get("dsl"):
                        with st.expander("🛠️ Advanced Compiler Provenance Logs"):
                            st.write("### 📜 Intermediate Validated Node AST (JSON DSL)")
                            st.json(data.get("dsl", {}))
                            
                elif status_code == 401:
                    st.error("Authentication expired. Terminated session. Re-authenticate.")
                elif err_type == "NETWORK_ERROR":
                    st.error("⚠️ Unable to connect to the server. Please check if the backend is running.")
                elif status_code == 500:
                    st.error("⚠️ Something went wrong on our end. Please try again in a moment.")
                elif status_code == 400 or err_type == "INVALID_INPUT":
                    st.error("⚠️ We could not understand your query. Please try rephrasing it.")
                elif err_type == "TIMEOUT":
                    st.error("⏱️ Request timed out. Please try a simpler query.")
                elif err_type == "JSON_ERROR":
                    st.error("⚠️ Received an unexpected response. Please try again.")
                else:
                    st.error(f"Execution Halt: Code {status_code} - {err_type}")

# ==========================================
# FINAL TASK: SECURE DEBUG PERFORMANCE SUMMARY
# ==========================================
# URL condition: ?debug=true
# Since st.experimental_get_query_params is deprecated, using modern st.query_params
if "debug" in st.query_params and st.query_params["debug"].lower() == "true":
    st.write("---")
    st.markdown("## ⚙️ Engineering Telemetry Dashboard")
    st.caption("Active connection to `/performance/dashboard` background task runner")
    
    try:
        sess = get_session()
        p_res = sess.get(f"{API_BASE}/performance/dashboard?debug=true")
        if p_res.status_code == 200:
            p_data = p_res.json()
            m_c1, m_c2, m_c3 = st.columns(3)
            m_c1.metric("10-Query Avg Latency", f"{p_data.get('avg_response_time_ms', 0)} ms")
            m_c2.metric("Cache Hit Rate", f"{p_data.get('cache_hit_rate_pct', 0)} %")
            m_c3.metric("Live Postgres Connections", f"{p_data.get('active_db_connections', 0)}")
            
            st.write("### 🐢 Last 5 Detected Slow Queries")
            slow_q = p_data.get("slow_queries", [])
            if slow_q:
                st.table(slow_q)
            else:
                st.success("No slow queries (> 1000ms) detected!")
        else:
            st.error(p_res.json().get("detail", "Not available"))
    except Exception as e:
        st.error("Dashboard backend unavailable.")

st.write("---")
st.markdown("<p style='color: #64748B; font-size: 0.80rem; text-align: center; margin-top: 10px; font-weight: 500;'>AI Powered Stock Screener v1.0 | Springboard Mentorship Program 2026</p>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 0.8rem; text-align: center;'>⚠️ Disclaimer: Results are for informational purposes only. This is not financial advice. Always consult a qualified financial advisor before making investment decisions.</p>", unsafe_allow_html=True)
