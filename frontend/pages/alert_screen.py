import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Alerts - StockSense AI", layout="wide")

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
if "token" not in st.session_state or st.session_state.token is None:
    st.warning("Please login first.")
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

# ---------- HERO TITLE ----------
st.markdown(
"""
<h1 style='text-align:center;font-size:40px;'>Smart Market Alerts</h1>
<p style='text-align:center;color:#9fb0c4;font-size:15px'>
Create alerts and monitor market conditions in real-time
</p>
""",
unsafe_allow_html=True
)

st.write("")
st.write("")

# ---------- FETCH ALERTS ----------
alerts = []
res = requests.get(
    f"{API_URL}/alerts/",
    headers={"Authorization": f"Bearer {st.session_state.token}"}
)
if res.status_code == 200:
    alerts = res.json()

# ---------- MAIN SPLIT LAYOUT ----------
left_col, spacer, right_col = st.columns([1, 0.01, 1.3])

# ---------- LEFT: CREATE ALERT ----------

with left_col:
    st.markdown("### Create New Alert")

    card = st.container(border=True)

    with card:
        sym_res = requests.get(f"{API_URL}/alerts/symbols")
        symbol_data = sym_res.json()
        symbol_options = [f"{s['symbol']} - {s['name']}" for s in symbol_data]
        selected = st.selectbox("Select Company", symbol_options)
        symbol = selected.split(" - ")[0]
        company_name = selected.split(" - ")[1]

        # Friendly metric names
        metric_map = {
            "Current Price": "current_price",
            "P/E Ratio": "pe_ratio",
            "Revenue": "revenue",
            "Profit Margin": "profit_margin"
        }

        col1, col2 = st.columns(2)

        with col1:
            metric_label = st.selectbox("Alert Metric", list(metric_map.keys()))
            metric = metric_map[metric_label]

        with col2:
            operator = st.selectbox("Trigger Condition", [">", "<", ">=", "<="])

        value = st.number_input("Threshold Value")

        st.caption("Example: Alert when Price > 3000")
        if st.button("Create Alert", use_container_width=True):
            condition = {
                "symbol": symbol,
                "company_name": company_name,
                "metric": metric,
                "operator": operator,
                "value": value
            }

            response = requests.post(
                f"{API_URL}/alerts/create",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                json=condition
            )

            if response.status_code == 200:
                st.success("Alert created successfully")
            elif response.status_code == 400:
                st.warning("Invalid alert parameters.")
            elif response.status_code == 401:
                st.error("Session expired. Please login again.")
            else:
                st.error("Could not create alert. Try again later.")

# ---------- RIGHT: ACTIVE ALERTS ----------
with right_col:
    st.markdown("### Active Alerts")

    metric_names = {
        "current_price": "Current Price",
        "pe_ratio": "P/E Ratio",
        "revenue": "Revenue",
        "profit_margin": "Profit Margin"
    }

    operator_text = {
        ">": "goes above",
        "<": "goes below",
        ">=": "reaches or goes above",
        "<=": "reaches or goes below"
    }

    if alerts:
        for alert in alerts:
            cond = alert["condition"]

            metric_display = metric_names.get(cond['metric'], cond['metric'])
            operator_display = operator_text.get(cond['operator'], cond['operator'])

            with st.container(border=True):

                col1, col2, col3 = st.columns([4, 7, 1.5])

                with col1:
                    with col1:
                        st.markdown(
                            f"<div style='font-size:24px; font-weight:700; color:#50C878'>🕭 {cond['symbol']}</div>",
                            unsafe_allow_html=True
                        )

                with col2:
                    st.markdown(
                        f"<span style='color:#e5e7eb; font-size:18px;'>{cond.get('company_name','')}</span>",
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f"""
                        <div style="margin-top:-10px; font-size:16px;">
                            Trigger when <b style='color:#50C878;'>
                            {metric_display} {operator_display} {cond['value']}
                            </b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f"<div style='color:#9ca3af; font-size:14px; margin-top:2px; margin-bottom:15px;'>Created: {alert['created_at']}</div>",
                        unsafe_allow_html=True
                    )
                with col3:
                    st.markdown("<div style='display:flex; justify-content:flex-end;'>", unsafe_allow_html=True)
                    if st.button("Delete", key=f"del_{alert['id']}"):
                        requests.delete(
                            f"{API_URL}/alerts/delete/{alert['id']}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No alerts created yet")

# ---------- Triggered Alerts ----------

st.markdown("### ⚠ Triggered Alerts")

# Button to check alerts
if st.button("Check Alerts Now", use_container_width=True):
    res = requests.get(
        f"{API_URL}/alerts/check",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )

    if res.status_code == 200:
        st.success("Alerts checked")
    st.rerun()

# Fetch triggered alerts
triggered_alerts = []
res = requests.get(
    f"{API_URL}/alerts/triggered",
    headers={"Authorization": f"Bearer {st.session_state.token}"}
)
if res.status_code == 200:
    triggered_alerts = res.json()

metric_names = {
    "current_price": "Current Price",
    "pe_ratio": "P/E Ratio",
    "revenue": "Revenue",
    "profit_margin": "Profit Margin"
}

operator_text = {
    ">": "went above",
    "<": "went below",
    ">=": "reached or went above",
    "<=": "reached or went below"
}

if triggered_alerts:
    for alert in triggered_alerts:
        cond = alert["condition"]

        metric_display = metric_names.get(cond['metric'], cond['metric'])
        operator_display = operator_text.get(cond['operator'], cond['operator'])

        with st.container(border=True):

            col1, col2, col3 = st.columns([4, 7, 3])

            # LEFT: Symbol
            with col1:
                st.markdown(
                    f"<div style='font-size:24px; font-weight:700; color:#f87171;'>⚠ {cond['symbol']}</div>",
                    unsafe_allow_html=True
                )

            # MIDDLE: Company + Trigger text
            with col2:
                st.markdown(
                    f"<div style='font-size:18px; color:#e5e7eb; font-weight:500;'>"
                    f"{cond.get('company_name','')}"
                    f"</div>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div style='font-size:16px; margin-top:4px;'>"
                    f"Triggered when <b style='color:#f87171;'>"
                    f"{metric_display} {operator_display} {cond['value']}"
                    f"</b></div>",
                    unsafe_allow_html=True
                )
                # CURRENT VALUE
                price_res = requests.get(
                    f"{API_URL}/alerts/current_value/{cond['symbol']}/{cond['metric']}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if price_res.status_code == 200:
                    current_val = price_res.json().get("value")

                    if current_val is not None:
                        current_val = float(current_val)
                        alert_val = float(cond['value'])

                        diff = current_val - alert_val

                        st.markdown(
                            f"<div style='font-size:15px; color:#9ca3af;'>Current: {current_val}</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            f"<div style='font-size:15px; color:#f87171;'>Difference: {diff:.2f}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown(
                    f"<div style='font-size:14px; color:#9ca3af; margin-top:4px; margin-bottom:15px;'>"
                    f"Triggered: {alert['triggered_at']}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            
            with col3:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Reactivate", key=f"react_{alert['id']}"):
                        requests.put(
                            f"{API_URL}/alerts/reactivate/{alert['id']}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        st.rerun()

                with b2:
                    if st.button("Delete", key=f"del_trig_{alert['id']}"):
                        requests.delete(
                            f"{API_URL}/alerts/delete/{alert['id']}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        st.rerun()

else:               
    st.info("No triggered alerts yet")


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