import streamlit as st
import requests
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go
import random

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="StockSense AI", layout="wide")

# ---------- STYLE ----------
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

html, body, [class*="css"]{
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
letter-spacing:1.5px;
color:#eaf2ff;
text-shadow:0 0 10px rgba(59,130,246,0.35);
}

/* REMOVE RED BORDER */

div[data-baseweb="input"]:focus-within{
border:1px solid rgba(59,130,246,0.35) !important;
box-shadow:none !important;
}
            
div[data-testid="stButton"] button{
font-size:14px;
padding:7px 10px;
border-radius:10px;
border:1px solid rgba(59,130,246,0.45);
background:rgba(37,99,235,0.06);
color:#dbeafe;
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
        st.markdown(
        "<span class='brand'>StockSense <span style='color:#3b82f6'>AI</span></span>",
        unsafe_allow_html=True
        )

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

# ---------- FETCH ----------
def fetch_portfolio():
    try:
        res = requests.get(
            f"{API_URL}/portfolio/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.error("Please login again.")
        else:
            st.error("Failed to load portfolio.")

        return []

    except requests.exceptions.ConnectionError:
        st.error("Server unavailable.")
        return []

raw = fetch_portfolio()

# ---------- MERGE ----------
data_map = defaultdict(lambda: {
    "company": "",
    "symbol": "",
    "quantity": 0,
    "investment_value": 0,
    "current_value": 0,
    "company_id": None
})

for s in raw:
    k = s["symbol"]
    data_map[k]["company"] = s["company"]
    data_map[k]["symbol"] = s["symbol"]
    data_map[k]["company_id"] = s.get("company_id")
    data_map[k]["quantity"] += s["quantity"]
    data_map[k]["investment_value"] += s["investment_value"]
    data_map[k]["current_value"] += s["current_value"]

portfolio = list(data_map.values())


# ---------- FORMAT ----------
def format_currency(val):
    if val >= 1e7:
        return f"₹ {val/1e7:.2f} Cr"
    elif val >= 1e5:
        return f"₹ {val/1e5:.2f} L"
    else:
        return f"₹ {val:,.0f}"

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;'>Portfolio Analysis</h1>
<p style='text-align:center;color:#9ca3af;margin-top:-10px;'>
Track performance, allocation and growth of your investments
</p>
""", unsafe_allow_html=True)
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

if not portfolio:
    st.markdown(
        """
        <div style='text-align:center; margin-top:120px;'>
            <div style='font-size:22px; font-weight:600; color:#e2e8f0;'>
                No investments yet
            </div>
            <div style='font-size:14px; color:#94a3b8; margin-top:8px;'>
                Start building your portfolio to track performance, allocation and returns.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        if st.button("Add Stocks", use_container_width=True):
            st.switch_page("pages/query_screen.py")

    st.stop()

# ---------- SUMMARY ----------
total_inv = sum(s["investment_value"] for s in portfolio)
total_cur = sum(s["current_value"] for s in portfolio)
profit = total_cur - total_inv
pct = (profit / total_inv * 100) if total_inv else 0

col1, col2, col3 = st.columns(3)

def metric_card(col, title, value, pct_change=None, value_color="#eaf2ff"):
    with col:
        with st.container(border=True):
            top_left, top_right = st.columns([3,1])

            with top_left:
                st.markdown(f"""
                <div style="
                    font-size:18px;
                    color:#94a3b8;
                    margin-bottom:6px;
                    font-weight:500;
                    letter-spacing:0.3px;
                ">
                    {title}
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"<span style='font-size:27px; font-weight:600; color:{value_color};'>{value}</span>",
                    unsafe_allow_html=True
                )

            if pct_change is not None:
                color = "#22c55e" if pct_change >= 0 else "#ef4444"
                arrow = "▲" if pct_change >= 0 else "▼"

                with top_right:
                    st.markdown(
                        f"""
                        <div style="
                            color:{color};
                            font-size:18px;
                            font-weight:600;
                            text-align:right;
                            margin-top:18px;
                        ">
                            {arrow} {pct_change:.2f}%
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# Cards
metric_card(col1, "Total Value", format_currency(total_cur), pct)
metric_card(col2, "Investment", format_currency(total_inv))
metric_card(col3, "Profit", format_currency(profit),
            value_color="#22c55e" if profit >= 0 else "#ef4444")


# ---------- SEARCH + REFRESH ----------
col_search, col_refresh = st.columns([5, 1])

with col_search:
    search = st.text_input("", placeholder="Search holdings...").strip().lower()

with col_refresh:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()

# ---------- APPLY SEARCH FILTER ----------
if search:
    portfolio = [
        s for s in portfolio
        if search in s["company"].lower()
        or search in s["symbol"].lower()
    ]
# ---------- RANGE ----------
title_col, range_col = st.columns([4, 1])

with title_col:
    st.markdown("###  Portfolio Insights")

with range_col:
    range_option = st.radio(
        "",
        ["1W", "1M", "6M", "1Y"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ---------- REALISTIC TREND ----------
base = total_inv
trend = []

for i in range(260):
    change = random.uniform(-0.02, 0.03)
    base = base * (1 + change)
    trend.append(base)

df = pd.DataFrame({"value": trend})

if range_option == "1W":
    df = df.tail(5)
elif range_option == "1M":
    df = df.tail(22)
elif range_option == "6M":
    df = df.tail(120)
elif range_option == "1Y":
    df = df.tail(250)

df["date"] = pd.date_range(end=pd.Timestamp.today(), periods=len(df))


# ---------- CHART LAYOUT ----------
col_left, col_right = st.columns([1, 1.3])

# ---------- DONUT ----------
with col_left:
    with st.container(border=True):

        st.markdown(
            "<span style='font-size:15px; font-weight:600;'>Allocation Breakdown</span>",
            unsafe_allow_html=True
        )

        labels = [s["symbol"] for s in portfolio]
        values = [s["current_value"] for s in portfolio]

        donut = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.70,
            textinfo="percent",
            marker=dict(colors=[
                "#3b82f6",
                "#60a5fa",
                "#1d4ed8",
                "#93c5fd",
                "#2563eb"
            ])
        )])

        # Center total value
        donut.add_annotation(
            text=f"{format_currency(total_cur)}<br>Total",
            showarrow=False,
            font=dict(size=13, color="#eaf2ff")
        )

        donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=20, r=20),
            height=260,
            showlegend=True,
            legend=dict(font=dict(color="#cbd5e1"))
        )

        st.plotly_chart(donut, use_container_width=True)


# ---------- LINE ----------
with col_right:
    with st.container(border=True):

        st.markdown(
            "<span style='font-size:15px; font-weight:600;'>Portfolio Growth</span>",
            unsafe_allow_html=True
        )

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode='lines',
            line=dict(shape='spline', width=3, color="#3b82f6"),
            fill='tozeroy',
            fillcolor="rgba(59,130,246,0.15)"
        ))

        fig.update_traces(
            hovertemplate="₹ %{y:,.0f}<br>%{x|%b %d}"
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=20, r=20),
            height=260,
            xaxis=dict(
                tickformat="%b %d",
                showgrid=False,
                color="#cbd5e1"
            ),
            yaxis=dict(
                tickprefix="₹ ",
                tickformat=",.0f",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                color="#cbd5e1"
            )
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------- ACTIONS ----------
def add_stock(cid):
    requests.post(
        f"{API_URL}/portfolio/add",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        json={"company_id": cid, "quantity": 1}
    )

def remove_stock(cid):
    requests.delete(
        f"{API_URL}/portfolio/remove?company_id={cid}",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )

# ---------- HOLDINGS ----------
st.markdown("###  Current Holdings")

def get_status(pct):
    if pct >= 15:
        return "Growth", "#22c55e"
    elif pct >= 7:
        return "Stable", "#3b82f6"
    elif pct >= -2:
        return "Flat", "#eab308"
    else:
        return "Loss", "#ef4444"
    
for s in portfolio:

    investment = s["investment_value"]
    current = s["current_value"]
    profit = current - investment
    pct = (profit / investment * 100) if investment else 0

    profit_color = "#22c55e" if profit >= 0 else "#ef4444"
    status_text, status_color = get_status(pct)

    with st.container(border=True):

        cols = st.columns([2.5, 1, 1.5, 1.5, 1.2, 1.2, 2])

        # Company
        cols[0].markdown(f"**{s['company']}**<br><span style='color:#9ca3af'>{s['symbol']}</span>", unsafe_allow_html=True)

        # Qty
        cols[1].markdown(f"Qty<br>**{s['quantity']}**", unsafe_allow_html=True)

        # Investment
        cols[2].markdown(f"Investment<br>**{format_currency(investment)}**", unsafe_allow_html=True)

        # Current
        cols[3].markdown(f"Current<br>**{format_currency(current)}**", unsafe_allow_html=True)

        # Profit
        cols[4].markdown(
            f"Profit<br><span style='color:{profit_color}; font-weight:600;'>"
            f"{format_currency(profit)}</span>",
            unsafe_allow_html=True
        )

        # Return
        cols[5].markdown(
            f"Return<br><span style='color:{profit_color}; font-weight:600;'>"
            f"{pct:.2f}%</span>",
            unsafe_allow_html=True
        )

        # Actions on right side
        with cols[6]:
            b1, b2, b3 = st.columns(3)
            symbol = s.get("symbol")

            if b1.button("➕", key=f"add_{s['symbol']}"):
                add_stock(s["company_id"])
                st.rerun()

            if b2.button("➖", key=f"sub_{s['symbol']}"):
                requests.post(
                    f"{API_URL}/portfolio/decrease",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    json={"company_id": s["company_id"], "quantity": 1}
                )
                st.rerun()

            if b3.button("🗑️", key=f"del_{s['symbol']}"):
                remove_stock(s["company_id"])
                st.session_state.toast = "Removed from portfolio"
                st.session_state.refresh_portfolio = True  # update frontend state
                st.rerun()

        # Status badge aligned right
        st.markdown(
            f"<div style='text-align:right; margin-top:-8px;'>"
            f"<span style='color:{status_color}; font-weight:600;'>● {status_text}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

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