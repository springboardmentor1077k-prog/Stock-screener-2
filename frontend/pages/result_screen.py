import streamlit as st
import pandas as pd
import requests
import math

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="StockSense AI Results", layout="wide")

# ---------- WATCHLIST STATE ----------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = set()

# ---------- GLOBAL STYLE ----------
st.markdown("""
<style>

header {visibility:hidden;}
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
[data-testid="collapsedControl"] {display:none;}

.block-container{
padding-top:0rem;
padding-bottom:1rem;
}

@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@300;400;500&display=swap');

html, body{
font-family:'Inter', sans-serif;
}

.stApp{
background:
radial-gradient(circle at 20% 20%, rgba(59,130,246,0.12), transparent 40%),
radial-gradient(circle at 80% 30%, rgba(37,99,235,0.12), transparent 40%),
linear-gradient(180deg,#020712,#081424);
}

.brand{
font-family:'Orbitron', sans-serif;
font-size:40px;
font-weight:700;
letter-spacing:1px;
color:#eaf2ff;
text-shadow:0 0 10px rgba(59,130,246,0.35);
}

div[data-testid="stButton"] button{
font-size:15px;
font-weight:500;
padding:10px 14px;
border-radius:10px;
border:1px solid rgba(59,130,246,0.45);
background:rgba(37,99,235,0.06);
color:#dbeafe;
transition:all .25s;
}

div[data-testid="stButton"] button:hover{
background:rgba(59,130,246,0.12);
transform:translateY(-1px);
}

.result-title{
text-align:center;
font-size:32px;
font-weight:600;
margin-top:20px;
margin-bottom:20px;
color:#e5e7eb;
}

.company-name{
font-size:18px;
font-weight:600;
color:white;
}

.company-sub{
color:#9ca3af;
font-size:13px;
}

.metric-title{
font-size:12px;
color:#cbd5e1;
margin-bottom:2px;
}

.metric-value{
font-size:15px;
font-weight:500;
color:#e5e7eb;
}

.result-count{
color:#9ca3af;
font-size:14px;
}

div[data-testid="stVerticalBlockBorderWrapper"]{
border:1px solid rgba(59,130,246,0.35) !important;
border-radius:12px !important;
background:rgba(9,17,35,0.55) !important;
transition:all .25s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover{
border-color:#3b82f6 !important;
box-shadow:0 0 12px rgba(59,130,246,0.25);
transform:translateY(-2px);
}

div[data-baseweb="select"]{
background:#0b1629 !important;
border-radius:10px !important;
border:1px solid rgba(59,130,246,0.35) !important;
box-shadow:none !important;
outline:none !important;
}

div[data-baseweb="select"] *{
box-shadow:none !important;
outline:none !important;
}

div[data-baseweb="select"] span{
color:#e5e7eb !important;
}

</style>
""", unsafe_allow_html=True)

# ---------- AUTH ----------
if "token" not in st.session_state:
    st.warning("Please login first")
    st.stop()

if "last_query" not in st.session_state:
    st.warning("No query available")
    st.stop()

# ---------- PAGE STATE ----------
if "results_page" not in st.session_state:
    st.session_state.results_page = 1

page = st.session_state.results_page
page_size = 5

# ---------- SORT STATE ----------
if "sort_by" not in st.session_state:
    st.session_state.sort_by = "pe_ratio"

if "sort_order" not in st.session_state:
    st.session_state.sort_order = "descending"

# ---------- NAVBAR ----------
nav1, nav2, nav3, nav4, nav5, nav6, nav7 = st.columns([4,1,1,1,1,0.6,1])

with nav1:
    c1, c2 = st.columns([1.3,8])
    with c1:
        st.image("frontend/assets/stock_icon.png", width=64)
    with c2:
        st.markdown("<span class='brand'>StockSense <span style='color:#3b82f6'>AI</span></span>", unsafe_allow_html=True)

with nav2:
    if st.button("Discover", use_container_width=True):
        st.switch_page("pages/query_screen.py")

with nav3:
    st.button("Markets", use_container_width=True)

with nav4:
    if st.button("Portfolio", use_container_width=True):
        st.switch_page("pages/portfolio_screen.py")

with nav5:
    if st.button("Watchlist", use_container_width=True):
        st.switch_page("pages/watchlist_screen.py")

with nav6:
    if st.button("🔔", use_container_width=True):
        st.switch_page("pages/alert_screen.py")

with nav7:
    if st.button("Logout"):
        st.session_state.token = None
        st.switch_page("app.py")

# ---------- TITLE ----------
st.markdown(f"""
<div class='result-title'>
Results for: {st.session_state.last_query}
</div>
""", unsafe_allow_html=True)

# ---------- SORT UI ----------
left, right = st.columns([6,4])

with right:
    col1, col2 = st.columns(2)

    with col1:
        new_sort_by = st.selectbox(
            "Sort By",
            ["pe_ratio","market_cap","revenue","profit_margin","ebitda"],
            index=["pe_ratio","market_cap","revenue","profit_margin","ebitda"].index(st.session_state.sort_by)
        )

    with col2:
        new_sort_order = st.selectbox(
            "Order",
            ["ascending","descending"],
            index=0 if st.session_state.sort_order == "ascending" else 1
        )

# ✅ ONLY FIX: trigger rerun when sorting changes
if new_sort_by != st.session_state.sort_by or new_sort_order != st.session_state.sort_order:
    st.session_state.sort_by = new_sort_by
    st.session_state.sort_order = new_sort_order
    st.session_state.results_page = 1
    st.rerun()

# ---------- FETCH ----------
def fetch_page(page):
    response = requests.post(
        f"{API_URL}/query",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        json={
            "query": st.session_state.last_query,
            "page": page,
            "page_size": page_size,
            "sort_by": st.session_state.sort_by,
            "order": st.session_state.sort_order
        }
    )
    if response.status_code == 200:
        return response.json()
    return None

result = fetch_page(page)

if result is None:
    st.error("Failed to fetch results")
    st.stop()

data = result.get("data", [])
total_results = result.get("total_results", 0)

df = pd.DataFrame(data)

if df.empty:
    st.warning("No results found for this query")
    st.stop()

total_pages = max(math.ceil(total_results / page_size), 1)

# ---------- COMPANY CARD ----------
def company_card(row):
    symbol = row.get("symbol", "—")
    sector = row.get("sector", "N/A")

    with st.container(border=True):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3,1,1,1,1,1,0.4])

        with col1:
            st.markdown(f"<div class='company-name'>{row.get('company_name')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='company-sub'>{symbol} • {sector}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class='metric-title'>P/E</div>
                <div class='metric-value'>{round(row.get("pe_ratio",0),2)}</div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class='metric-title'>Market Cap</div>
                <div class='metric-value'>{row.get("market_cap")}</div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
                <div class='metric-title'>Revenue</div>
                <div class='metric-value'>{row.get("revenue")}</div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
                <div class='metric-title'>EBITDA</div>
                <div class='metric-value'>{row.get("ebitda")}</div>
            """, unsafe_allow_html=True)

        with col6:
            profit = row.get("profit_margin",0)
            st.markdown(f"""
                <div class='metric-title'>Profit</div>
                <div class='metric-value'>{round(profit*100,2)}%</div>
            """, unsafe_allow_html=True)

        with col7:
            star = "⭐" if symbol in st.session_state.watchlist else "☆"
            if st.button(star, key=f"watch_{symbol}"):
                if symbol in st.session_state.watchlist:
                    st.session_state.watchlist.remove(symbol)
                else:
                    st.session_state.watchlist.add(symbol)
                st.rerun()

        if st.button("➕ Add", key=f"add_{row['symbol']}"):

            response = requests.post(
                f"{API_URL}/portfolio/add",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                json={
                    "company_id": row["company_id"],
                    "quantity": 1
                }
            )

            if response.status_code == 200:
                st.success(f"{row['symbol']} added to portfolio")
            else:
                st.error("Failed to add")

# ---------- DISPLAY ----------
for _, row in df.iterrows():
    company_card(row)

# ---------- PAGINATION ----------
st.write("")
center = st.columns([2,3,2])

with center[1]:

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        if st.button("⬅ Previous", disabled=(page == 1)):
            st.session_state.results_page -= 1
            st.rerun()

    with col2:
        st.markdown(f"<div style='text-align:center'>Page {page} of {total_pages}</div>", unsafe_allow_html=True)

    with col3:
        if st.button("Next ➡", disabled=(page >= total_pages)):
            st.session_state.results_page += 1
            st.rerun()

# ---------- BACK ----------
st.write("")
center = st.columns([3,2,3])

with center[1]:
    if st.button("← Back to Search", use_container_width=True):
        st.session_state.results_page = 1
        st.switch_page("pages/query_screen.py")