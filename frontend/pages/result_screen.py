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

.metric-row{
    border-bottom:1px solid rgba(148,163,184,0.15);
    padding-bottom:10px;
    margin-bottom:10px;
}
            
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
font-size:20px;
font-weight:600;
color:white;
}

.company-sub{
color:#9ca3af;
font-size:15px;
}

.metrics-row {
    padding-top: 16px;
    padding-bottom: 10px;
}
            
.metric-title{
    font-size:15px;
    color:#94a3b8;
    margin-bottom:10px;
    letter-spacing:0.5px;
}

.metric-value{
    font-size:20px;
    font-weight:600;
    color:#e5e7eb;
    margin-bottom: 10px;
}

.metric-block{
    padding-top:10px;
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

div[data-testid="stButton"] button{
    font-size:14px;
    padding:6px 12px;
    border-radius:8px;
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
    if st.button("Markets", use_container_width=True):
        st.switch_page("pages/company_details_screen.py")

with nav4:
    if st.button("Portfolio", use_container_width=True):
        st.switch_page("pages/portfolio_screen.py")

with nav5:
    if st.button("Watchlist", use_container_width=True):
        st.switch_page("pages/watchlist_screen.py")

with nav6:
    if st.button("🕭", use_container_width=True):
        st.switch_page("pages/alert_screen.py")

with nav7:
    if st.button("Logout"):
        st.session_state.token = None
        st.switch_page("app.py")
        
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

# ---------- TITLE + SORT (SAME ROW) ----------
title_col, sort_col = st.columns([7.5,2.5])

with title_col:
    st.markdown(f"""
    <div class='result-title' style='text-align:left; margin-top:6px; margin-bottom:6px;'>
        ✎ᝰ.  Results for: {st.session_state.last_query}
    </div>
    """, unsafe_allow_html=True)

with sort_col:
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

# Divider line under title row
st.markdown("""
<hr style="
border: none;
height: 1px;
background: rgba(148,163,184,0.2);
margin-top: 8px;
margin-bottom: 20px;
">
""", unsafe_allow_html=True)

if new_sort_by != st.session_state.sort_by or new_sort_order != st.session_state.sort_order:
    st.session_state.sort_by = new_sort_by
    st.session_state.sort_order = new_sort_order
    st.session_state.results_page = 1
    st.rerun()

# ---------- FETCH ----------
def fetch_page(page):
    try:
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

        elif response.status_code == 401:
            st.error("Session expired. Please login again.")
        elif response.status_code == 404:
            st.info("No results found.")
        else:
            st.error("Failed to fetch results.")

        return None

    except requests.exceptions.ConnectionError:
        st.error("Server unavailable.")
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
def format_number(num):
    if num is None:
        return "—"
    num = float(num)
    if num >= 1_000_000_000_000:
        return f"₹{num/1_000_000_000_000:.1f}T"
    elif num >= 1_000_000_000:
        return f"₹{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"₹{num/1_000_000:.1f}M"
    else:
        return f"₹{num:.0f}"
    
def pe_color(pe):
    if pe < 18:
        return "#22c55e"  # green
    elif pe <= 25:
        return "#f59e0b"  # orange
    else:
        return "#ef4444"  # red

def profit_color(p):
    if p > 0.20:
        return "#22c55e"
    elif p >= 0.12:
        return "#f59e0b"
    else:
        return "#ef4444"
    
def ai_label(pe, industry_pe=20):
    if pe < industry_pe * 0.85:
        return "Undervalued", "#22c55e"
    elif pe > industry_pe * 1.15:
        return "Overvalued", "#ef4444"
    else:
        return "Fair Value", "#f59e0b"


def company_card(row):
    symbol = row.get("symbol", "—")
    sector = row.get("sector", "N/A")

    pe = row.get("pe_ratio", 0)
    profit = row.get("profit_margin", 0)

    pe_col = pe_color(pe)
    profit_col = profit_color(profit)

    label, label_color = ai_label(pe)

    with st.container(border=True):
        left, mid1, mid2, mid3, mid4, mid5, right = st.columns([3,1,1,1,1,1,1.5])

        # ---- LEFT: Company Name + AI Tag ----
        with left:
            st.markdown(f"""
            <div class='company-name'>
                {row.get('company_name')}
                <span style='
                    color:{label_color};
                    font-size:12px;
                    margin-left:10px;
                    padding:3px 8px;
                    border-radius:6px;
                    background:rgba(0,0,0,0.25);
                    border:1px solid {label_color};
                '>{label}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"<div class='company-sub'>{symbol} • {sector}</div>", unsafe_allow_html=True)

        # ---- METRICS ----
        with mid1:
            st.markdown(f"""
                <div class='metric-title'>P/E</div>
                <div class='metric-value' style='color:{pe_col}; font-size:20px; font-weight:600'>
                    {round(pe,2)}
                </div>
            """, unsafe_allow_html=True)

        with mid2:
            st.markdown(f"""
                <div class='metric-title'>Market Cap</div>
                <div class='metric-value' style='font-size:18px'>
                    {format_number(row.get("market_cap"))}
                </div>
            """, unsafe_allow_html=True)

        with mid3:
            st.markdown(f"""
                <div class='metric-title'>Revenue</div>
                <div class='metric-value' style='font-size:18px'>
                    {format_number(row.get("revenue"))}
                </div>
            """, unsafe_allow_html=True)

        with mid4:
            st.markdown(f"""
                <div class='metric-title'>EBITDA</div>
                <div class='metric-value' style='font-size:18px'>
                    {format_number(row.get("ebitda"))}
                </div>
            """, unsafe_allow_html=True)

        with mid5:
            st.markdown(f"""
                <div class='metric-title'>Profit</div>
                <div class='metric-value' style='color:{profit_col}; font-size:20px; font-weight:600'>
                    {round(profit*100,2)}%
                </div>
            """, unsafe_allow_html=True)

        # ---- RIGHT SIDE BUTTONS ----
        with right:
            c1, c2 = st.columns(2)

            with c1:
                if st.button("➕ Add", key=f"add_{symbol}"):
                    response = requests.post(
                        f"{API_URL}/portfolio/add",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        json={
                            "company_id": row["company_id"],
                            "quantity": 1
                        }
                    )

                    if response.status_code == 200:
                        st.success(f"{symbol} added to portfolio")
                    else:
                        st.error("Failed to add")

            with c2:
                star = "⭐" if symbol in st.session_state.watchlist else "☆"
                if st.button(star, key=f"watch_{symbol}"):
                    if symbol in st.session_state.watchlist:
                        st.session_state.watchlist.remove(symbol)
                    else:
                        st.session_state.watchlist.add(symbol)
                    st.rerun()

# ---------- DISPLAY ----------
for _, row in df.iterrows():
    company_card(row)

# ---------- PAGINATION ----------
st.markdown("""
<hr style="
border: none;
height: 1px;
background: rgba(148,163,184,0.2);
margin-top: 15px;
margin-bottom: 18px;
">
""", unsafe_allow_html=True)

total_pages = max(math.ceil(total_results / page_size), 1)

col1, col2, col3 = st.columns([1.5,1,1.5])

start = (page - 1) * page_size + 1
end = min(page * page_size, total_results)

with col1:
    if st.button("← Previous", disabled=(page == 1), use_container_width=True):
        st.session_state.results_page -= 1
        st.rerun()

with col2:
    st.markdown(f"""
    <div style='text-align:center; color:#94a3b8; font-size:14px; margin-top:6px;'>
        Page {page} of {total_pages}
    </div>
    """, unsafe_allow_html=True)

with col3:
    if st.button("Next →", disabled=(page >= total_pages), use_container_width=True):
        st.session_state.results_page += 1
        st.rerun()

# Back button 
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

center = st.columns([3,2,3])
with center[1]:
    if st.button("← Back to Search", use_container_width=True):
        st.session_state.results_page = 1
        st.switch_page("pages/query_screen.py")

st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="
    background-color: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 6px;
    font-size: 15px;
    color: #aaa;
    text-align: center;
">
Disclaimer: This platform is for educational purposes only. Data may not be real-time or fully accurate and should not be considered financial advice.
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)