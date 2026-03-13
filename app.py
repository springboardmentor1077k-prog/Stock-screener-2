import streamlit as st
import requests
import pandas as pd
# restore token from query params
params = st.query_params

if "token" in params and "token" not in st.session_state:
    st.session_state.token = params["token"]
if "username" in params and "username" not in st.session_state:
    st.session_state.username = params["username"]
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Stock Intelligence",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

/* Force column menu (3 dots) to stay visible */
.ag-header-cell-menu-button {
    opacity: 1 !important;
    visibility: visible !important;
    display: inline-block !important;
}

/* Make the 3 dots black */
.ag-header-cell-menu-button svg {
    color: black !important;
    fill: black !important;
}

/* Increase icon visibility */
.ag-header-cell-menu-button svg {
    width: 16px !important;
    height: 16px !important;
}


</style>
""", unsafe_allow_html=True)


# SAFE REQUEST HANDLER


def safe_request(method, url, **kwargs):
    try:
        res = requests.request(method, url, timeout=10, **kwargs)

        try:
            data = res.json()
        except:
            return res.status_code, {
                "success": False,
                "error": {
                    "message": res.text
                }
            }

        # If backend uses new structured error
        if not data.get("success", True) and "error" in data:
            return res.status_code, data

        return res.status_code, data

    except requests.exceptions.RequestException as e:
        return 500, {
            "success": False,
            "error": {
                "message": f"Connection error: {str(e)}"
            }
        }


def show_error(data, default_msg="Something went wrong"):
    if isinstance(data, dict):
        if "error" in data and "message" in data["error"]:
            st.error(data["error"]["message"])
        elif "detail" in data:
            st.error(data["detail"])
        else:
            st.error(default_msg)
    else:
        st.error(default_msg)
def get_initials(name):
    if not name:
        return "U"   # default avatar letter

    parts = name.split()
    initials = ""

    for p in parts:
        initials += p[0]

    return initials.upper()
        

# SESSION STATE INIT


if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "history" not in st.session_state:
    st.session_state.history = []


# AUTH FUNCTIONS


def login(username, password):
    return safe_request(
        "POST",
        f"{API_URL}/auth/login",
        data={
            "username": username,
            "password": password
        }
    )


def register(username, email, password):
    return safe_request(
        "POST",
        f"{API_URL}/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )



# LOGIN / REGISTER PAGE


if st.session_state.token is None:

    st.title(" Login / Register")

    mode = st.radio("Choose Action", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if mode == "Register":
        email = st.text_input("Email")

    if st.button(mode):

        if username == "" or password == "":
            st.warning("Fill required fields.")
        else:

            if mode == "Login":

                status, data = login(username, password)

                if status == 200:
                    token = data["access_token"]
                    st.session_state.token = token
                    st.session_state.username = username

                    # store token in URL so refresh keeps login
                    st.query_params["token"] = token
                    st.query_params["username"] = username

                    st.success("Login successful!")
                    st.rerun()
                else:
                    show_error(data, "Login failed")

            else:

                if email == "":
                    st.warning("Email required.")
                else:
                    status, data = register(username, email, password)

                    if status == 200:
                        st.success("Registration successful. Please login.")
                    else:
                        show_error(data, "Registration failed")


# MAIN APP


else:

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }
    if "show_user_menu" not in st.session_state:
        st.session_state.show_user_menu = False
    st.sidebar.title(" AI Stock Platform")
    

    if "page" not in st.session_state:
        st.session_state.page = "AI Screener"

    page = st.sidebar.radio(
        "Navigation",
        ["AI Screener", "Portfolio", "Watchlist", "Alerts", "Company Explorer"],
        index=["AI Screener", "Portfolio", "Watchlist", "Alerts", "Company Explorer"].index(st.session_state.page)
    )

    st.session_state.page = page
    st.sidebar.markdown("<div style='height:250px'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    initials = get_initials(st.session_state.get("username"))

    col1, col2, col3 = st.sidebar.columns([1,4,1])

    # avatar circle
    if col1.button(initials):
        st.session_state.show_user_menu = not st.session_state.show_user_menu

    # username
    username = st.session_state.get("username")

    if username:
        col2.markdown(f"**{username.upper()}**")
    else:
        col2.markdown("**USER**")

    # three dots
    if col3.button("⋮"):
        st.session_state.show_user_menu = not st.session_state.show_user_menu
    if st.session_state.show_user_menu:

        st.sidebar.markdown("---")

        st.sidebar.markdown(f" **{st.session_state.username}@gmail.com**")

        if st.sidebar.button(" Change Password"):
            st.sidebar.info("Password change feature coming soon")

        if st.sidebar.button(" Logout"):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.search_results = None
            st.query_params.clear()
            st.rerun()





    st.title(" AI Stock Intelligence")
    
    st.caption(f"Welcome, {st.session_state.username}")

    for q in st.session_state.history[-5:]:
        if st.sidebar.button(q):
            st.session_state.last_query = q

    


    
    #  SCREENER
   

    if page == "AI Screener":
        st.markdown("""
        Ask questions about companies using **natural language**.

        Example queries:
        - companies where pe_ratio < 20
        - companies where eps > 5
        - companies where revenue_growth > 10
        """)
        st.markdown("### Quick Queries")

        col1, col2, col3 = st.columns(3)

        if col1.button("Low PE Stocks"):
            st.session_state.last_query = "companies where pe_ratio < 20"

        if col2.button("High EPS Stocks"):
            st.session_state.last_query = "companies where eps > 5"

        if col3.button("High Growth Stocks"):
            st.session_state.last_query = "companies where revenue_growth > 10"

        query = st.text_input(
            " Ask about stocks",
            value=st.session_state.get("last_query", ""),
            placeholder="Example: companies where pe_ratio < 20"
        )
        search_clicked = st.button(" Search Stocks")
        if search_clicked:

            if query.strip() == "":
                st.warning("Enter a query.")
            else:

                with st.spinner("AI analyzing stocks..."):
                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/screener",
                        json={"query": query},
                        headers=headers
                    )

                if status == 200:

                    # Backend returns list directly inside "data"
                    results = data.get("data", [])

                    st.session_state.search_results = results
                    st.session_state.last_query = query
                    st.session_state.page_number = 1
                    if query not in st.session_state.history:
                        st.session_state.history.append(query)
                    st.success(f"Found {len(results)} companies")
                elif status == 401:
                    st.error("Session expired. Please login again.")
                    st.session_state.token = None
                    st.rerun()
                else:
                    if status == 503:
                        st.warning(" AI service temporarily unavailable. Please try later.")
                    else:
                        show_error(data, "Screener failed")

        if st.session_state.search_results is not None:

            if len(st.session_state.search_results) == 0:
                st.info("No companies matched your query.")

            else:

                df = pd.DataFrame(st.session_state.search_results)

                col1, col2, col3 = st.columns(3)

                col1.metric("Companies Found", len(df))
                col2.metric("Highest EPS", round(df["eps"].max(), 2))
                col3.metric("Average PE Ratio", round(df["pe_ratio"].mean(), 2))
                
                
                
                st.markdown("### Top Companies")

                top = df.head(3)

                cols = st.columns(len(top))

                for i, (_, row) in enumerate(top.iterrows()):
                    with cols[i]:
                        st.metric(
                            label=row["symbol"],
                            value=f"EPS {row['eps']}"
                            )

                st.subheader(" Screening Results")

                # ---------- Pagination ----------
                rows_per_page = 10

                total_rows = len(df)
                total_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page > 0 else 0)

                # store current page
                if "page_number" not in st.session_state:
                    st.session_state.page_number = 1
                start = (st.session_state.page_number - 1) * rows_per_page
                end = start + rows_per_page

                paginated_df = df.iloc[start:end]
                st.data_editor(paginated_df, use_container_width=True, disabled=True)

                

                # ---------- Compact Pagination ----------
                if total_pages > 1:

                    left_space, nav = st.columns([9,1])

                    with nav:

                        prev_col, page_col, next_col = st.columns([1,2,1], gap="small")

                        if prev_col.button("◀", key="prev_page"):
                            if st.session_state.page_number > 1:
                                st.session_state.page_number -= 1

                        page_col.markdown(
                                f"""
                                <div style="
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                    height:38px;
                                    font-size:14px;
                                ">
                                    {st.session_state.page_number}/{total_pages}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        if next_col.button("▶", key="next_page"):
                            if st.session_state.page_number < total_pages:
                                st.session_state.page_number += 1

                

                
                st.markdown("### Save Company")

                col1, col2 = st.columns(2)

                save_symbol = st.selectbox(
                    "Select company",
                    df["symbol"],
                    key="save_symbol"
                )

                if col1.button(" Add to Watchlist"):

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/watchlist",
                        json={"stock_symbol": save_symbol},
                        headers=headers
                    )

                    if status == 200:
                        st.success("Added to Watchlist!")
                    else:
                        show_error(data)

                if col2.button(" Add to Portfolio"):

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/portfolio",
                        json={
                            "stock_symbol": save_symbol,
                            "quantity": 1
                        },
                        headers=headers
                    )

                    if status == 200:
                        st.success("Added to Portfolio!")
                    else:
                        show_error(data)
                selected_symbol = st.selectbox(
                    "Open company details",
                    df["symbol"]
                )

                if st.button("View Company"):
                    st.session_state.selected_company = selected_symbol
                    st.session_state.page = "Company Explorer"
                    st.rerun()
                st.markdown("### EPS Comparison")

                st.bar_chart(df.set_index("symbol")["eps"])
                
                st.markdown("### AI Insight")

                st.info(
                    f"The screener found {len(df)} companies matching your filters. "
                    "These companies satisfy the financial conditions you provided."
                )
        
  
    #  PORTFOLIO


    elif page == "Portfolio":

        st.subheader("Add to Portfolio")

        stock_symbol = st.text_input("Stock Symbol (e.g., AAPL)")
        quantity = st.number_input("Quantity", min_value=1, value=1)

        if st.button("Add Stock", key="add_stock_btn"):

            status, data = safe_request(
                "POST",
                f"{API_URL}/portfolio",
                json={
                    "stock_symbol": stock_symbol.upper(),
                    "quantity": quantity
                },
                headers=headers
            )

            if status == 200:
                st.success("Added to portfolio!")
            else:
                show_error(data, "Failed operation")

        st.subheader("Your Portfolio")

        if st.button("Load Portfolio", key="load_portfolio_btn"):

            status, data = safe_request(
                "GET",
                f"{API_URL}/portfolio",
                headers=headers
            )

            if status == 200:
                df = pd.DataFrame(data.get("data", []))
                st.dataframe(df, use_container_width=True)
            else:
                st.error("Failed to load portfolio")

        delete_id = st.number_input("Portfolio ID to delete", min_value=1)

        if st.button("Delete Portfolio Entry", key="delete_portfolio_btn"):

            status, data = safe_request(
                "DELETE",
                f"{API_URL}/portfolio/{delete_id}",
                headers=headers
            )

            if status == 200:
                st.success("Deleted successfully")
            else:
                st.error(data.get("detail", "Delete failed"))
                
                

#  WATCHLIST


    elif page == "Watchlist":

        st.subheader("Add to Watchlist")

        stock_symbol = st.text_input("Stock Symbol (e.g., AAPL)")

        if st.button("Add to Watchlist"):

            status, data = safe_request(
                "POST",
                f"{API_URL}/watchlist",
                json={
                    "stock_symbol": stock_symbol.upper()
                },
                headers=headers
            )

            if status == 200:
                st.success("Added to watchlist!")
            else:
                show_error(data)


        st.subheader("Your Watchlist")

        if st.button("Load Watchlist"):

            status, data = safe_request(
                "GET",
                f"{API_URL}/watchlist",
                headers=headers
            )

            if status == 200:
                df = pd.DataFrame(data.get("data", []))
                st.dataframe(df, use_container_width=True)
                
            else:
                show_error(data)


        delete_id = st.number_input("Watchlist ID to delete", min_value=1)

        if st.button("Delete Watchlist Entry"):

            status, data = safe_request(
                "DELETE",
                f"{API_URL}/watchlist/{delete_id}",
                headers=headers
            )

            if status == 200:
                st.success("Removed from watchlist")
            else:
                show_error(data)
  
    #  ALERTS


    elif page == "Alerts":

        st.subheader("Create Alert")

        stock_symbol = st.text_input("Stock Symbol")
        metric = st.selectbox("Metric", ["pe_ratio", "eps"])
        condition = st.selectbox("Condition", [">", "<"])
        threshold = st.number_input("Threshold", value=0.0)

        if st.button("Create Alert", key="create_alert_btn"):

            status, data = safe_request(
                "POST",
                f"{API_URL}/alerts",
                json={
                    "stock_symbol": stock_symbol.upper(),
                    "metric": metric,
                    "condition": condition,
                    "threshold": threshold
                },
                headers=headers
            )

            if status == 200:
                st.success("Alert created!")
            else:
                show_error(data, "Alert operation failed")

        st.subheader("Your Alerts")

        if st.button("Load Alerts", key="load_alerts_btn"):

            status, data = safe_request(
                "GET",
                f"{API_URL}/alerts",
                headers=headers
            )

            if status == 200:
                df = pd.DataFrame(data.get("data", []))
                st.dataframe(df, use_container_width=True)
            else:
                st.error("Failed to load alerts")

        delete_alert_id = st.number_input("Alert ID to delete", min_value=1)

        if st.button("Delete Alert", key="delete_alert_btn"):

            status, data = safe_request(
                "DELETE",
                f"{API_URL}/alerts/{delete_alert_id}",
                headers=headers
            )

            if status == 200:
                st.success("Alert deleted")
            else:
                st.error(data.get("detail", "Delete failed"))

#  COMPANY EXPLORER


    elif page == "Company Explorer":

        st.subheader("Company Explorer")

        symbol = st.text_input(
    "Enter stock symbol (example: AAPL)",
    value=st.session_state.get("selected_company", "")
)

        if symbol:

            if symbol.strip() == "":
                st.warning("Please enter a stock symbol")
                st.stop()

            
            # COMPANY DETAILS
            

            status, data = safe_request(
                "GET",
                f"{API_URL}/company/{symbol}/details",
                headers=headers
            )

            if status == 200:

                company = data["data"]

                st.subheader(company["company_name"])
                st.write("Sector:", company["sector"])

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("PE Ratio", company["pe_ratio"])
                col2.metric("EPS", company["eps"])
                col3.metric("Revenue Growth", company["revenue_growth"])
                col4.metric("Market Cap", company["market_cap"])

            else:
                show_error(data)

            
            # PRICE HISTORY
            

            status, price_data = safe_request(
                "GET",
                f"{API_URL}/company/{symbol}/price-history",
                headers=headers
            )

            if status == 200:

                df = pd.DataFrame(price_data["data"])

                if not df.empty:

                    df["date"] = pd.to_datetime(df["date"])

                    st.subheader("Stock Price Trend")

                    st.line_chart(
                        df.set_index("date")["close"]
                    )

            else:
                show_error(price_data)   