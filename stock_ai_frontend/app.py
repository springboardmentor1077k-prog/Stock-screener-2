import streamlit as st
import requests
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Stock Screener", layout="wide")


# ---------------- CACHE ----------------
@st.cache_data
def fetch_query_data(query):
    res = requests.post(
        "http://127.0.0.1:8000/query",
        params={"user_query": query}
    )
    return pd.DataFrame(res.json().get("data", []))

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

# ---------------- AUTH ----------------
if not st.session_state.logged_in:

    st.title("Authentication")

    option = st.radio("Select", ["Login", "Register"], key="auth_option")

    email = st.text_input("Email", key="auth_email")
    password = st.text_input("Password", type="password", key="auth_pass")

    if option == "Register":

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="auth_confirm"
        )

        if st.button("Register", key="register_btn"):

            if password != confirm_password:
                st.error("Passwords do not match")

            else:
                res = requests.post(
                    "http://127.0.0.1:8000/register",
                    json={"email": email, "password": password}
                )

                if res.status_code == 200:
                    st.success("Registered successfully. Please login.")
                else:
                    st.error("Registration failed")

    else:
        if st.button("Login", key="login_btn"):

            res = requests.post(
                "http://127.0.0.1:8000/login",
                json={"email": email, "password": password}
            )

            if res.status_code == 200:
                st.session_state.logged_in = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Dashboard")

if st.sidebar.button("Logout", key="logout_btn"):
    st.session_state.clear()
    st.rerun()

page = st.sidebar.radio(
    "Navigate",
    ["Query", "Portfolio", "Watchlist", "Alerts"],
    key="nav_radio"
)

st.title("AI Stock Screener")
st.warning(
    "⚠️ Disclaimer: This tool is for educational and informational purposes only. "
    "It does NOT provide financial advice. Always do your own research before investing."
)

# =========================================================
# ===================== QUERY =============================
# =========================================================
if page == "Query":

    # ---------------- STATE ----------------
    if "show_suggestions" not in st.session_state:
        st.session_state.show_suggestions = True

    st.subheader("Stock Search")

    # ---------------- INPUT ----------------
    query = st.text_input(
        "Enter query",
        key="query_input",
        value=st.session_state.get("query_input", "")
    )

    # ---------------- SEARCH ----------------
    if st.button("Search", key="search_btn") and query:
        st.session_state.df = fetch_query_data(query)
        st.session_state.show_suggestions = False

    # ---------------- SUGGESTIONS (CLEAN TEXT BELOW INPUT) ----------------
    if st.session_state.show_suggestions:

        st.markdown("#### 💡 Try queries like:")

        common_queries = [
            "IT companies with revenue > 500 and profit > 100",
            "Companies with growth > 15% and market cap > 2000",
            "Top 5 companies by net profit",
            "Companies with EBITDA > 200 and low market cap",
            "High growth companies with profit increasing",
            "Companies where revenue > 1000 and profit margin > 10%",
        ]

        for i, q in enumerate(common_queries):
            if st.button(f"{q}", key=f"query_text_{i}"):
                st.session_state["query_input"] = q
                st.session_state.df = fetch_query_data(q)
                st.session_state.show_suggestions = False
                st.rerun()

    # ---------------- RESET ----------------
    if not st.session_state.show_suggestions:
        if st.button("🔍 New Search"):
            st.session_state.show_suggestions = True
            if "df" in st.session_state:
                del st.session_state.df
            st.rerun()

    # ---------------- RESULTS ----------------
    if "df" in st.session_state:

        df = st.session_state.df

        if not df.empty:

            # -------- SUCCESS MESSAGES --------
            if "watchlist_msg" in st.session_state:
                st.success(st.session_state.watchlist_msg)
                del st.session_state.watchlist_msg

            if "portfolio_msg" in st.session_state:
                st.success(st.session_state.portfolio_msg)
                del st.session_state.portfolio_msg

            # -------- SUMMARY --------
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Companies", len(df))
            c2.metric("Avg Revenue", int(df["revenue"].mean()))
            c3.metric("Avg Profit", int(df["net_profit"].mean()))

            st.dataframe(df, use_container_width=True)

            companies = df["company_name"].unique()

            selected = st.selectbox(
                "Select Company",
                companies,
                key="query_select"
            )

            row = df[df["company_name"] == selected].iloc[0]

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Revenue", row["revenue"])
            c2.metric("Profit", row["net_profit"])
            c3.metric("Market Cap", row["market_cap"])
            c4.metric("Growth %", f"{round(row['growth_percent'],2)}%")
            c5.metric("EBITDA", row["ebitda"])

            colA, colB = st.columns(2)

            # ✅ WATCHLIST
            with colA:
                if st.button("Add to Watchlist", key="add_watchlist_btn"):
                    exists = any(
                        item["company_name"] == selected
                        for item in st.session_state.watchlist
                    )
                    if not exists:
                        st.session_state.watchlist.append(row.to_dict())
                        st.session_state.watchlist_msg = f"{selected} added to watchlist"
                        st.rerun()

            # ✅ PORTFOLIO
            with colB:
                if st.button("Add to Portfolio", key="add_portfolio_btn"):
                    st.session_state.portfolio.append({
                        "company_name": selected,
                        "quantity": 1,
                        "buy_price": row["market_cap"]
                    })
                    st.session_state.portfolio_msg = f"{selected} added to portfolio"
                    st.rerun()


# =========================================================
# ===================== PORTFOLIO =========================
# =========================================================
elif page == "Portfolio":

    st.subheader("Portfolio")

    if st.session_state.portfolio:

        df = pd.DataFrame(st.session_state.portfolio)

        df["Current Price"] = df["buy_price"] * 1.1
        df["Investment"] = df["quantity"] * df["buy_price"]
        df["Current Value"] = df["quantity"] * df["Current Price"]
        df["Profit"] = df["Current Value"] - df["Investment"]
        df["Growth %"] = (df["Profit"] / df["Investment"]) * 100

        st.dataframe(df, use_container_width=True)

        st.metric("Total Investment", int(df["Investment"].sum()))

        idx = st.selectbox(
            "Select Holding",
            df.index,
            format_func=lambda x: df.loc[x, "company_name"],
            key="portfolio_select"
        )

        col1, col2 = st.columns(2)

        with col1:
            qty = st.number_input(
                "Quantity",
                value=int(df.loc[idx, "quantity"]),
                key="update_qty"
            )

        with col2:
            price = st.number_input(
                "Buy Price",
                value=float(df.loc[idx, "buy_price"]),
                key="update_price"
            )

        colA, colB = st.columns(2)

        with colA:
            if st.button("Update", key="update_btn"):
                st.session_state.portfolio[idx]["quantity"] = qty
                st.session_state.portfolio[idx]["buy_price"] = price
                st.success("Updated successfully")

        # ✅ DELETE already exists (kept same)
        with colB:
            if st.button("Delete", key="delete_btn"):
                st.session_state.portfolio.pop(idx)
                st.success("Deleted successfully")
                st.rerun()

    else:
        st.info("No holdings available")

    st.markdown("### Add Holding")

    c1, c2, c3 = st.columns(3)

    with c1:
        name = st.text_input("Company", key="new_name")

    with c2:
        qty = st.number_input("Quantity", min_value=1, key="new_qty")

    with c3:
        price = st.number_input("Buy Price", min_value=0.0, key="new_price")

    if st.button("Add Holding", key="add_holding_btn"):
        if name:
            st.session_state.portfolio.append({
                "company_name": name,
                "quantity": qty,
                "buy_price": price
            })
            st.success("Holding added")

# =========================================================
# ===================== WATCHLIST =========================
# =========================================================
elif page == "Watchlist":

    st.subheader("Watchlist")

    if st.session_state.watchlist:

        # ✅ SHOW FULL DATA
        df = pd.DataFrame(st.session_state.watchlist)
        st.dataframe(df, use_container_width=True)

        idx = st.selectbox(
            "Select Company",
            df.index,
            format_func=lambda x: df.loc[x, "company_name"],
            key="watch_select"
        )

        if st.button("Remove", key="remove_watch_btn"):
            st.session_state.watchlist.pop(idx)
            st.success("Removed successfully")
            st.rerun()

    else:
        st.info("Watchlist empty")

# =========================================================
# ===================== ALERTS ============================
# =========================================================
elif page == "Alerts":

    st.subheader("Alerts")

    c1, c2, c3 = st.columns(3)

    with c1:
        metric = st.selectbox(
            "Metric",
            ["revenue", "net_profit", "market_cap"],
            key="alert_metric"
        )

    with c2:
        condition = st.selectbox(
            "Condition",
            [">", "<", ">=", "<=", "=="],
            key="alert_condition"
        )

    with c3:
        threshold = st.number_input(
            "Value",
            min_value=0,
            key="alert_value"
        )

    if st.button("Add Alert", key="add_alert_btn"):
        st.session_state.alerts.append({
            "metric": metric,
            "condition": condition,
            "threshold": threshold
        })
        st.success("Alert added")

    if st.session_state.alerts:
        st.dataframe(pd.DataFrame(st.session_state.alerts), use_container_width=True)

    st.markdown("### Trigger Alerts")

    sample = pd.DataFrame([
        {"company": "TCS", "revenue": 1000, "net_profit": 200, "market_cap": 3000},
        {"company": "Infosys", "revenue": 800, "net_profit": 150, "market_cap": 2500},
        {"company": "Wipro", "revenue": 600, "net_profit": 80, "market_cap": 1800},
    ])

    st.dataframe(sample)

    def check(val, cond, thr):
        if cond == ">": return val > thr
        if cond == "<": return val < thr
        if cond == ">=": return val >= thr
        if cond == "<=": return val <= thr
        if cond == "==": return val == thr

    triggered = []

    for alert in st.session_state.alerts:
        for _, row in sample.iterrows():
            if check(row[alert["metric"]], alert["condition"], alert["threshold"]):
                triggered.append(row["company"])

    if triggered:
        st.error(f"{len(triggered)} alerts triggered")
    else:
        st.success("No alerts triggered")
