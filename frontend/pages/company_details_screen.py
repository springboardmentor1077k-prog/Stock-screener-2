import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Markets", layout="wide")

# ---------- STYLE ----------
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
    font-size:18px;
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
    st.warning("Login first")
    st.stop()

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
    if st.button("🕭", use_container_width=True):
        st.switch_page("pages/alert_screen.py")

with nav7:
    if st.button("Logout"):
        st.session_state.token = None
        st.switch_page("app.py")

# ---------- FETCH MARKETS ----------
def fetch_markets():
    res = requests.get(
        f"{API_URL}/markets/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    if res.status_code == 200:
        return res.json()
    return []

markets = fetch_markets()

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;'>Markets</h1>
<p style='text-align:center;color:#9ca3af;margin-top:-10px;'>
Browse and analyze companies available in the market
</p>
""", unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

# ---------- HELPERS ----------
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
        return "#22c55e"
    elif pe <= 25:
        return "#f59e0b"
    else:
        return "#ef4444"

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

def add_watchlist(company_id):
    requests.post(
        f"{API_URL}/watchlist/add",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        params={"company_id": company_id}
    )

def add_portfolio(company_id):
    requests.post(
        f"{API_URL}/portfolio/add",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        json={
            "company_id": company_id,
            "quantity": 1
        }
    )

# ---------- COMPANY CARD ----------
for row in markets:

    pe = row.get("pe_ratio", 0)
    profit = row.get("profit_margin", 0)

    pe_col = pe_color(pe)
    profit_col = profit_color(profit)

    label, label_color = ai_label(pe)

    with st.container(border=True):
        left, mid1, mid2, mid3, mid4, mid5, right = st.columns([3,1,1,1,1,1,1.5])

        # Company + Tag
        with left:
            st.markdown(f"""
            <div style='font-size:18px; font-weight:600; color:white'>
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

            st.markdown(f"<div style='color:#9ca3af'>{row.get('symbol')} • {row.get('sector')}</div>", unsafe_allow_html=True)

        # Metrics
        with mid1:
            st.markdown(f"P/E<br><span style='color:{pe_col}; font-weight:600'>{round(pe,2)}</span>", unsafe_allow_html=True)

        with mid2:
            st.markdown(f"Market Cap<br>**{format_number(row.get('market_cap'))}**", unsafe_allow_html=True)

        with mid3:
            st.markdown(f"Revenue<br>**{format_number(row.get('revenue'))}**", unsafe_allow_html=True)

        with mid4:
            st.markdown(f"EBITDA<br>**{format_number(row.get('ebitda'))}**", unsafe_allow_html=True)

        with mid5:
            st.markdown(f"Profit<br><span style='color:{profit_col}; font-weight:600'>{round(profit*100,2)}%</span>", unsafe_allow_html=True)

        # Button
        with right:
            b1, b2 = st.columns(2)

            if b1.button("➕ Add", key=f"port_{row['company_id']}"):
                add_portfolio(row["company_id"])
                st.success("Added to portfolio")
                st.rerun()

            if b2.button("☆", key=f"watch_{row['company_id']}"):
                add_watchlist(row["company_id"])
                st.success("Added to watchlist")
                st.rerun()

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