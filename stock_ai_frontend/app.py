import streamlit as st
import requests
import pandas as pd

# Page config
st.set_page_config(page_title="AI Stock Screener", layout="wide")

# Custom CSS
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
.block-container {
    padding-top: 2rem;
}
.stButton>button {
    background-color: #2E86C1;
    color: white;
    border-radius: 8px;
    height: 3em;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📊 Dashboard")
page = st.sidebar.radio("Navigate", ["Query", "Portfolio", "Watchlist", "Alerts"])

# Header
st.title("📈 AI-Powered Stock Screener")

# ---------------- QUERY PAGE ----------------
if page == "Query":

    st.subheader("🔍 Smart Stock Search")

    col1, col2 = st.columns([5, 1])

    with col1:
        user_query = st.text_input(
            "Enter your query",
            placeholder="e.g. Companies with profit > 500 Cr"
        )

    with col2:
        search_btn = st.button("Search")

    if search_btn:
        if user_query:

            with st.spinner("Fetching data..."):
                try:
                    response = requests.get(
                        "http://127.0.0.1:8000/query",
                        params={"user_query": user_query}
                    )

                    data = response.json()
                    df = pd.DataFrame(data["results"])

                    if not df.empty:

                        # Metrics
                        st.subheader("📊 Summary")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Companies", len(df))
                        c2.metric("Avg Revenue", int(df["revenue"].mean()))
                        c3.metric("Avg Profit", int(df["profit"].mean()))

                        # Table
                        st.subheader("📋 Results")
                        st.dataframe(df, use_container_width=True)

                        # Details
                        st.subheader("🏢 Company Details")

                        selected = st.selectbox("Select Company", df["name"])
                        company = df[df["name"] == selected].iloc[0]

                        d1, d2, d3 = st.columns(3)
                        d1.metric("Revenue", company["revenue"])
                        d2.metric("Profit", company["profit"])
                        d3.metric("Market Cap", company["market_cap"])

                    else:
                        st.warning("No results found")

                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.warning("Please enter a query")

# ---------------- PORTFOLIO ----------------
elif page == "Portfolio":
    st.subheader("📁 Portfolio")
    st.info("Feature coming soon")

# ---------------- WATCHLIST ----------------
elif page == "Watchlist":
    st.subheader("⭐ Watchlist")
    st.info("Feature coming soon")

# ---------------- ALERTS ----------------
elif page == "Alerts":

    st.subheader("🔔 Alerts Engine")

    # Initialize session state
    if "alerts" not in st.session_state:
        st.session_state.alerts = []

    # -------- CREATE ALERT --------
    st.markdown("### ➕ Create Alert")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric = st.selectbox("Metric", ["revenue", "profit", "market_cap"])

    with col2:
        condition = st.selectbox("Condition", [">", "<", ">=", "<=", "=="])

    with col3:
        threshold = st.number_input("Value", min_value=0, value=100)

    if st.button("Add Alert"):
        st.session_state.alerts.append({
            "metric": metric,
            "condition": condition,
            "threshold": threshold
        })
        st.success("Alert added successfully!")

    # -------- SHOW ALERTS --------
    st.markdown("### 📋 Active Alerts")

    if st.session_state.alerts:
        st.dataframe(pd.DataFrame(st.session_state.alerts))
    else:
        st.info("No alerts created yet")

    # -------- SAMPLE DATA --------
    st.markdown("### 🧪 Test Alerts on Sample Data")

    sample_data = pd.DataFrame([
        {"name": "TCS", "revenue": 1000, "profit": 200, "market_cap": 3000},
        {"name": "Infosys", "revenue": 800, "profit": 150, "market_cap": 2500},
        {"name": "Wipro", "revenue": 600, "profit": 80, "market_cap": 1800},
    ])

    st.dataframe(sample_data, use_container_width=True)

    # -------- ALERT LOGIC --------
    def check_condition(value, condition, threshold):
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        return False

    # -------- RUN ALERTS --------
    st.markdown("### 🚨 Triggered Alerts")

    triggered = []

    for alert in st.session_state.alerts:
        for _, row in sample_data.iterrows():
            if check_condition(row[alert["metric"]], alert["condition"], alert["threshold"]):
                triggered.append({
                    "Company": row["name"],
                    "Metric": alert["metric"],
                    "Value": row[alert["metric"]],
                    "Condition": f'{alert["condition"]} {alert["threshold"]}'
                })

    if triggered:
        st.error(f"{len(triggered)} Alerts Triggered!")
        st.dataframe(pd.DataFrame(triggered), use_container_width=True)
    else:
        st.success("No alerts triggered")
