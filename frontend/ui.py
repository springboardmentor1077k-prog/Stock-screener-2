import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI-Powered Stock Screener", page_icon="📈", layout="wide")

st.markdown("""
<style>
    /* Clean and elegant UI centering */
    .block-container {
        padding-top: 3rem !important;
    }
    
    .main-title {
        font-weight: 800;
        font-size: 3.5rem !important;
        text-align: center;
        color: #0077b6; /* Deep professional blue */
        margin-bottom: -10px;
    }
    
    .sub-title {
        text-align: center;
        color: #555555;
        font-size: 1.2rem;
        letter-spacing: 1px;
        margin-bottom: 40px;
    }
    
    /* Make buttons round and sleek */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Make inputs sleek */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'user' not in st.session_state:
    st.session_state['user'] = None


# ==========================================
# PAGE 1: AUTHENTICATION PORTAL (FULL SCREEN)
# ==========================================
if st.session_state['token'] is None:
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="main-title">🧠 AI-Powered Stock Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Natural Language Enterprise Discovery Engine</div>', unsafe_allow_html=True)
    
    # Elegant central container
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
        
        # LOGIN TAB
        with tab1:
            st.markdown("#### Access Your Dashboard")
            login_user = st.text_input("Username", key="login_user")
            login_pwd = st.text_input("Password", type="password", key="login_pwd")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Login securely", type="primary", use_container_width=True):
                if login_user and login_pwd:
                    with st.spinner("Authenticating over secure network..."):
                        res = requests.post(f"{API_BASE}/login", json={"username": login_user, "password": login_pwd})
                        if res.status_code == 200:
                            st.session_state['token'] = res.json().get("access_token")
                            st.session_state['user'] = login_user
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Login Failed"))
                else:
                    st.warning("Please enter credentials.")

        # REGISTER TAB
        with tab2:
            st.markdown("#### Setup New Analyst Account")
            reg_user = st.text_input("Choose Username", key="reg_user")
            reg_email = st.text_input("Corporate Email", key="reg_email")
            reg_pwd = st.text_input("Choose Password", type="password", key="reg_pwd")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Register Account", type="primary", use_container_width=True):
                if reg_user and reg_email and reg_pwd:
                    with st.spinner("Provisioning Identity..."):
                        res = requests.post(f"{API_BASE}/register", json={"username": reg_user, "email": reg_email, "password": reg_pwd})
                        if res.status_code == 200:
                            st.success("✅ Account successfully created! Please switch to the Login tab.")
                        else:
                            st.error(res.json().get("detail", "Registration Failed"))
                else:
                    st.warning("Please fill out all specific fields!")


# ==========================================
# PAGE 2: MAIN SCREENER DASHBOARD
# ==========================================
else:
    # Sidebar only appears perfectly after Log In
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state['user']}")
        st.success("🟢 Encrypted Internal Session")
        st.markdown("---")
        st.markdown("### System Architecture")
        st.markdown("- **Parser:** Custom NLP Engine")
        st.markdown("- **Compiler:** Python DSL Tracker")
        st.markdown("- **Database:** MySQL Local Core")
        st.markdown("- **Security:** JWT Authentication")
        st.markdown("---")
        if st.button("🚪 Log Out System", use_container_width=True):
            st.session_state['token'] = None
            st.session_state['user'] = None
            st.rerun()

    # Dashboard Header
    st.markdown('<h2 style="color: #0077b6; font-weight: 800;">🧠 AI-Powered Stock Screener Dashboard</h2>', unsafe_allow_html=True)
    st.markdown("Welcome! Type perfectly natural English to search exactly what you want from the global database.")
    st.markdown("---")

    with st.expander("📖 Beginner's Guide to Metrics (Click to open)"):
        st.markdown("""
        * **PE Ratio**: Shows how expensive a stock is compared to its earnings. Lower is often considered cheaper.
        * **Revenue**: The total amount of money brought in by the company's operations.
        * **EBITDA**: A measure of a company's overall financial performance and profitability (earnings before interest, taxes, depreciation, and amortization).
        * **Debt-to-Equity**: Shows how much a company is using borrowed money. Lower means less debt.
        """)

    # Beautiful Search Bar
    user_query = st.text_input("🔍 Neural Command Terminal", placeholder="e.g., Show me tech companies where PE ratio < 20 and revenue > 50000", key="query_box")
    
    # Simple filters (page, sort)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        sort_by = st.selectbox("Sort By", ["pe_ratio", "revenue", "ebitda", "debt_to_equity"])
    with col_f2:
        sort_order = st.selectbox("Sort Order", ["asc", "desc"])
    with col_f3:
        limit = st.number_input("Results per page", min_value=1, max_value=100, value=10)
    with col_f4:
        page = st.number_input("Page Number", min_value=1, value=1)
        
    st.write("<br>", unsafe_allow_html=True)

    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        search_clicked = st.button("🚀 Execute Neural Search", type="primary", use_container_width=True)

    if search_clicked:
        if not user_query:
            st.warning("⚠️ Terminal is completely empty. Enter search parameters first.")
        else:
            with st.spinner("🧠 Connecting AI → Validating JSON → Writing Parameterized SQL → Executing Query..."):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                payload = {
                    "query": user_query,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "limit": limit,
                    "page": page
                }
                response = requests.post(f"{API_BASE}/ask_ai", json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✨ SQL Pipeline Execution Complete! Code generated securely without injections.")
                    
                    if "data" in data and len(data["data"]) > 0:
                        df = pd.DataFrame(data["data"])
                        # The system gracefully handles missing data (nulls) without crashing via Pandas
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.caption("📡 **Data Source:** Local Database (Snapshot). *Note: Different data providers may define metrics like PE differently. Expect possible data lag.*")
                    else:
                        st.info("ℹ️ No corporate equities matched your exact strict parameters.")
                        
                    with st.expander("🛠️ See Raw Compiler Pipeline Proof (Crucial for Internship Demo)", expanded=False):
                        st.write("### 1. The Strict Validated JSON (Intermediate DSL)")
                        st.json(data.get("dsl", {}))
                        
                        st.write("### 2. The Safe Compiled Raw SQL")
                        st.code(data.get("sql", ""), language="sql")
                        
                        st.write("### 3. The Isolated SQL Logic Parameters")
                        st.write(data.get("params", []))
                        
                elif response.status_code == 401:
                    st.error("Authentication Token Invalidated. Please securely log in again.")
                else:
                    try:
                        st.error(f"Error {response.status_code}: {response.json().get('detail')}")
                    except:
                        st.error(f"Fatal Error {response.status_code}: {response.text}")
