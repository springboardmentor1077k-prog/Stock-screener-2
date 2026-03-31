import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Watchlist", layout="wide")

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
    st.warning("Please login first")
    st.stop()


# ---------- FORMAT NUMBERS ----------
def format_number(val):
    try:
        val = float(val)
        if val >= 1e7:
            return f"{val/1e7:.2f} Cr"
        elif val >= 1e5:
            return f"{val/1e5:.2f} L"
        else:
            return f"{val:,.0f}"
    except:
        return val


# ---------- RECOMMENDATION ----------
def recommendation(pe, profit):
    if pe < 20 and profit > 0.15:
        return "Attractive", "#22c55e"   
    elif pe < 35:
        return "Neutral", "#f59e0b"      
    else:
        return "Risky", "#ef4444"        

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


# ---------- TITLE ----------
st.markdown("""
<h1 style='text-align:center;'>Watchlist Dashboard</h1>
<p style='text-align:center;color:#9ca3af;margin-top:-10px;'>
Track, analyze and manage your saved companies
</p>
""", unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

# ---------- FETCH WATCHLIST ----------
def fetch_watchlist():
    try:
        res = requests.get(
            f"{API_URL}/watchlist/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if res.status_code == 200:
            return res.json()
        else:
            st.error("Failed to load watchlist")
            return []
    except:
        st.error("Server unavailable")
        return []


# ---------- ADD TO PORTFOLIO ----------
def add_to_portfolio(company_id):
    requests.post(
        f"{API_URL}/portfolio/add",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        json={"company_id": company_id, "quantity": 1}
    )


# ---------- REMOVE ----------
def remove_watchlist(company_id):
    requests.delete(
        f"{API_URL}/watchlist/remove",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        params={"company_id": company_id}
    )


watchlist = fetch_watchlist()

# ---------- WATCHLIST CARDS ----------
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
    
if watchlist:
    for row in watchlist:
        pe = row.get("pe_ratio", 0)
        profit = row.get("profit_margin", 0)

        rec, rec_color = recommendation(pe, profit)

        with st.container(border=True):

            cols = st.columns([3, 1, 1.2, 1.2, 1, 1.2, 1.5])

            # Company
            cols[0].markdown(f"""
            <div class='company-name'>{row['company_name']}</div>
            <div class='company-sub'>{row['symbol']} • {row['sector']}</div>
            """, unsafe_allow_html=True)

            pe_col = pe_color(pe)
            profit_col = profit_color(profit)

            # PE
            cols[1].markdown(f"""
            <div class='metric-title'>P/E</div>
            <div class='metric-value' style='color:{pe_col}; font-size:18px; font-weight:600'>
                {round(pe,2)}
            </div>
            """, unsafe_allow_html=True)

            # Market Cap
            cols[2].markdown(f"""
            <div class='metric-title'>Market Cap</div>
            <div class='metric-value'>
                {format_number(row.get("market_cap",0))}
            </div>
            """, unsafe_allow_html=True)

            # Revenue
            cols[3].markdown(f"""
            <div class='metric-title'>Revenue</div>
            <div class='metric-value'>
                {format_number(row.get("revenue",0))}
            </div>
            """, unsafe_allow_html=True)

            # Profit
            cols[4].markdown(f"""
            <div class='metric-title'>Profit</div>
            <div class='metric-value' style='color:{profit_col}; font-weight:600'>
                {round(profit*100,2)}%
            </div>
            """, unsafe_allow_html=True)

            cols[5].markdown(f"""
            <div style="
                display:inline-block;
                padding:6px 16px;
                border-radius:20px;
                border:1px solid {rec_color};
                color:{rec_color};
                font-weight:600;
                font-size:14px;
                text-align:center;
                background:rgba(0,0,0,0.25);
                box-shadow:0 0 8px {rec_color}33;
            ">
            {rec}
            </div>
            """, unsafe_allow_html=True)
            
            # Buttons
            with cols[6]:
                b1, b2 = st.columns(2)

                if b1.button("➕ Add", key=f"port_{row['company_id']}"):
                    add_to_portfolio(row["company_id"])
                    st.rerun()

                if b2.button("Remove", key=f"rem_{row['company_id']}"):
                    remove_watchlist(row["company_id"])
                    st.rerun()
else:
    st.markdown("""
    <div style='text-align:center; margin-top:100px;'>
        <div style='font-size:22px; font-weight:600; color:#e2e8f0;'>
            Your watchlist is empty
        </div>
        <div style='font-size:14px; color:#94a3b8; margin-top:8px;'>
            Add companies from the results page to track them here.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------- DISCLAIMER ----------

st.markdown("<div style='height:300px'></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    background-color: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 6px;
    font-size: 14px;
    color: #aaa;
    text-align: center;
">
Disclaimer: This platform is for educational purposes only. Data may not be real-time or fully accurate and should not be considered financial advice.
</div>
""", unsafe_allow_html=True)