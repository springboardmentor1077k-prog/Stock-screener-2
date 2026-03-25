from urllib import response

import streamlit as st
import requests
import pandas as pd
# restore token from query params
params = st.query_params

if "symbol" in params:
    st.session_state.selected_company = params["symbol"]
    st.session_state.page = "Company Explorer"
    del st.query_params["symbol"]
    
if "folder" in params:
    st.session_state.selected_folder = params["folder"]
    st.session_state.page = "Portfolio"
    del st.query_params["folder"]
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

query_params = st.query_params

# EDIT CLICK
if "edit_folder" in query_params:
    st.session_state.rename_folder = query_params["edit_folder"]





# SAFE REQUEST HANDLER


def safe_request(method, url, **kwargs):
    try:
        res = requests.request(method, url, timeout=20, **kwargs)

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
if "show_create_folder" not in st.session_state:
    st.session_state.show_create_folder = False

if "show_stock_modal" not in st.session_state:
    st.session_state.show_stock_modal = False

if "portfolio_folders" not in st.session_state:
    st.session_state.portfolio_folders = {}

if "selected_folder" not in st.session_state:
    st.session_state.selected_folder = None
if "folders" not in st.session_state:
    st.session_state.folders = []


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

def get_current_price(symbol):

    status, data = safe_request(
        "GET",
        f"{API_URL}/company/{symbol}/price",
        headers=headers
    )

    if status == 200:
        return data["data"]["price"]

    return 0

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
   
    header_left, header_right = st.columns([10,1])

    with header_left:
        st.title("AI Stock Intelligence")

    with header_right:

        initials = get_initials(st.session_state.get("username"))

        avatar_clicked = st.button(
            initials,
            key="avatar_btn",
            help="Account"
        )

        if avatar_clicked:
            st.session_state.show_user_menu = not st.session_state.show_user_menu

        

    if st.session_state.show_user_menu:

        col_space, col_menu = st.columns([9,1])

        with col_menu:

            st.markdown(
                f"""
                <div style="
                    background:white;
                    padding:15px;
                    border-radius:10px;
                    box-shadow:0 4px 10px rgba(0,0,0,0.2);
                    text-align:center;
                ">
                <b>{st.session_state.username}@gmail.com</b>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.username = None
                st.session_state.search_results = None
                st.query_params.clear()
                st.rerun()
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

                    # load current watchlist
                    status, data = safe_request(
                        "GET",
                        f"{API_URL}/watchlist",
                        headers=headers
                    )

                    if status == 200:

                        df_watch = pd.DataFrame(data.get("data", []))

                        # check if already exists
                        if not df_watch.empty and save_symbol in df_watch["symbol"].values:
                            st.warning("Stock already in watchlist")

                        else:

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

                    else:
                        show_error(data)
                symbol = st.text_input("Enter Symbol")

                quantity = st.number_input("Quantity", min_value=1, value=1)

                buy_price = st.number_input("Buy Price", min_value=0.0, value=0.0)

                folder_name = st.text_input("Folder Name", value="Tech")

                if st.button("Add to Portfolio"):

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/portfolio",
                        json={
                            "stock_symbol": str(symbol).upper(),
                            "quantity": int(quantity),
                            "buy_price": float(buy_price),
                            "folder_name": str(folder_name).strip().lower()
                            },
                        headers=headers
                    )

                    if status == 200:
                        st.success("Added to Portfolio!")
                    else:
                        show_error(data)

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

        if st.session_state.selected_folder is None:
            st.title("📂 Portfolio")

        # ---------- SESSION STATE ----------
        

        if "selected_folder" not in st.session_state:
            st.session_state.selected_folder = None

        if "show_create_folder" not in st.session_state:
            st.session_state.show_create_folder = False

        if "show_add_stock" not in st.session_state:
            st.session_state.show_add_stock = False


        # ---------- CREATE FOLDER BUTTON ----------
        if st.session_state.selected_folder is None:
            col1, col2 = st.columns([10,2])

            with col2:
                if st.button("➕ Create Folder"):
                    st.session_state.show_create_folder = True


        # ---------- SHOW FOLDERS ----------

        if st.session_state.selected_folder is None:

                folders = set()

                # backend folders
                status, data = safe_request(
                    "GET",
                    f"{API_URL}/portfolio",
                    headers=headers
                )

                if status == 200 and "data" in data:
                    df = pd.DataFrame(data["data"])
                    if not df.empty:
                        for f in df["folder_name"].dropna():
                            folders.add(f.strip().lower())

                # session folders
                for f in st.session_state.folders:
                    folders.add(f.strip().lower())

                folders = list(folders)

                if len(folders) == 0:
                    st.info("No folders yet")

                else:
                    for folder in folders:

                        col1, col2, col3 = st.columns([8,1,1])

                        with col1:
                            token = st.session_state.token
                            username = st.session_state.username

                            st.markdown(
                                f"""
                                <a href="?folder={folder}&token={token}&username={username}" 
                                style="text-decoration:none; font-size:16px;">
                                📁 {folder}
                                </a>
                                """,
                                unsafe_allow_html=True
                            )

                        with col2:
                            if st.button("✏️", key=f"edit_folder_{folder}"):
                                st.session_state.rename_folder = folder
                                st.rerun()

                        with col3:
                            if st.button("🗑️", key=f"delete_folder_{folder}"):

                                status, data = safe_request(
                                    "GET",
                                    f"{API_URL}/portfolio",
                                    headers=headers
                                )

                                df = pd.DataFrame(data.get("data", []))

                                folder_stocks = df[
                                    df["folder_name"].fillna("").str.strip().str.lower() ==
                                    folder.strip().lower()
                                ]

                                for _, stock in folder_stocks.iterrows():
                                    safe_request(
                                        "DELETE",
                                        f"{API_URL}/portfolio/{stock['id']}",
                                        headers=headers
                                    )

                                st.success(f"{folder} deleted ✅")
                                st.rerun()

                        st.divider()
                    
                    # -------- RENAME FOLDER --------
                    if "rename_folder" in st.session_state:

                        st.markdown(f"### ✏️ Rename Folder: {st.session_state.rename_folder}")

                        new_name = st.text_input("New Folder Name")

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button("Save Rename"):

                                if new_name.strip() == "":
                                    st.warning("Enter folder name")
                                    st.stop()

                                status, data = safe_request(
                                    "PUT",
                                    f"{API_URL}/portfolio/rename-folder",
                                    json={
                                        "old_name": str(st.session_state.rename_folder),
                                        "new_name": str(new_name.strip())
                                    },
                                    headers=headers
                                )

                                if status == 200:
                                    st.success("Renamed ✅")
                                    del st.session_state.rename_folder
                                    st.rerun()
                                else:
                                    show_error(data)

                        with col2:
                            if st.button("Cancel Rename"):
                                del st.session_state.rename_folder
                                st.rerun()
                        
                    
                    
                    
                    

                    


        # ---------- OPEN FOLDER ----------
        if st.session_state.selected_folder is not None:

            folder = st.session_state.selected_folder

            col1, col2,col3 = st.columns([1,8,2])

            with col1:
                if st.button("⬅"):
                    st.session_state.selected_folder = None
                    st.rerun()

            with col2:
                st.markdown(f"### {folder}")
            with col3:
                if st.button("➕ Add Stock"):
                    st.session_state.show_add_stock = True
        # -------- ADD STOCK UI INSIDE FOLDER --------
            if st.session_state.show_add_stock:

                st.markdown(f"### Add Stock to {folder}")

                symbol = st.text_input("Enter Symbol").upper()
                quantity = st.number_input("Quantity", min_value=1, value=1)
                buy_price = st.number_input("Buy Price", min_value=0.0, value=0.0)

                current_price = 0

                if symbol:
                    current_price = get_current_price(symbol)

                    if current_price > 0:
                        st.success(f"Current Price: ₹{round(current_price,2)}")
                        st.info(f"Total Value: ₹{round(current_price * quantity,2)}")
                    else:
                        st.warning("Invalid symbol")

                colA, colB = st.columns(2)

                with colA:
                    if st.button("Add Now"):

                        if symbol == "":
                            st.warning("Enter symbol")
                            st.stop()

                        status, data = safe_request(
                            "POST",
                            f"{API_URL}/portfolio",
                            json={
                                "stock_symbol": symbol,
                                "quantity": quantity,
                                "buy_price": buy_price,
                                "folder_name": folder   # 🔥 VERY IMPORTANT
                            },
                            headers=headers
                        )

                        if status == 200:
                            st.success("Stock Added ✅")
                            st.session_state.show_add_stock = False
                            st.rerun()
                        else:
                            show_error(data)

                with colB:
                    if st.button("Cancel"):
                        st.session_state.show_add_stock = False
                        st.rerun()
            # ---------- LOAD STOCKS ----------
            status, data = safe_request(
                "GET",
                f"{API_URL}/portfolio",
                headers=headers
            )

            if status == 200 and "data" in data:

                df = pd.DataFrame(data["data"])
                

                if df.empty:
                    st.info("No stocks in portfolio")

                else:

                    folder_df = df[
                        df["folder_name"].str.strip().str.lower() == str(folder).strip().lower()
                    ].copy()

                    if folder_df.empty:
                        st.info("No stocks in this folder")

                    else:

                        st.markdown("### Your Stocks")

                        
                        folder_df["current_price"] = folder_df["symbol"].apply(get_current_price)
                        folder_df["current_value"] = folder_df["current_price"] * folder_df["quantity"]
                        folder_df["invested"] = folder_df["buy_price"] * folder_df["quantity"]
                        folder_df["profit"] = folder_df["current_value"] - folder_df["invested"]
                        folder_df["profit_percent"] = (folder_df["profit"] / folder_df["invested"]) * 100

                        # fallback company name
                        folder_df["company_name"] = folder_df["symbol"]

                        display_df = pd.DataFrame({
                            "Symbol": folder_df["symbol"],
                            "Company": folder_df["company_name"],
                            "Quantity": folder_df["quantity"],
                            "Buy Price": folder_df["buy_price"],
                            "Current Price": folder_df["current_price"].round(2),
                            "Value": folder_df["current_value"].round(2),
                            "Change %": folder_df["profit_percent"].round(2)
                        })


                        # ---------- AI SCREENER STYLE TABLE ----------

                        display_df = pd.DataFrame({
                            "Symbol": folder_df["symbol"],
                            "Company": folder_df["company_name"],
                            "Quantity": folder_df["quantity"],
                            "Buy Price": folder_df["buy_price"],
                            "Current Price": folder_df["current_price"].round(2),
                            "Value": folder_df["current_value"].round(2),
                            "Change %": folder_df["profit_percent"].round(2),
                        })

                        h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2,3,2,2,2,2,2,1,1])

                        h1.markdown("**Symbol**")
                        h2.markdown("**Company**")
                        h3.markdown("**Qty**")
                        h4.markdown("**Buy Price**")
                        h5.markdown("**Current**")
                        h6.markdown("**Value**")
                        h7.markdown("**Change %**")
                        h8.markdown("**Edit**")
                        h9.markdown("**Delete**")

                        st.divider()

                        # ROWS
                        for _, row in folder_df.iterrows():

                            cols = st.columns([2,3,2,2,2,2,2,1,1])

                            with cols[0]:
                                st.write(row["symbol"])

                            with cols[1]:
                                st.write(row["company_name"])

                            with cols[2]:
                                st.write(row["quantity"])

                            with cols[3]:
                                st.write(row["buy_price"])

                            with cols[4]:
                                st.write(round(row["current_price"], 2))

                            with cols[5]:
                                st.write(round(row["current_value"], 2))

                            with cols[6]:
                                if row["profit_percent"] >= 0:
                                    st.markdown(f"<span style='color:green'>{round(row['profit_percent'],2)}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<span style='color:red'>{round(row['profit_percent'],2)}</span>", unsafe_allow_html=True)

                            with cols[7]:
                                if st.button("✏️", key=f"edit_{row['id']}"):
                                    st.session_state.edit_id = row["id"]
                                    st.session_state.edit_qty = row["quantity"]
                                    st.session_state.edit_price = row["buy_price"]
                            with cols[8]:
                                if st.button("🗑️", key=f"delete_{row['id']}"):

                                    st.session_state.delete_id = row["id"]
                                    st.session_state.delete_symbol = row["symbol"]  # optional (nice UX)

                                    st.rerun()
                        
                        
                        # -------- DELETE CONFIRMATION --------
                        if "delete_id" in st.session_state:

                            st.warning(f"⚠️ Are you sure you want to delete {st.session_state.delete_symbol}?")

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("Confirm Delete"):

                                    status, data = safe_request(
                                        "DELETE",
                                        f"{API_URL}/portfolio/{st.session_state.delete_id}",
                                        headers=headers
                                    )

                                    if status == 200:
                                        st.success("Stock deleted 🗑️")
                                        del st.session_state.delete_id
                                        del st.session_state.delete_symbol
                                        st.rerun()
                                    else:
                                        show_error(data)

                            with col2:
                                if st.button("Cancel", key="cancel_stock_delete"):
                                    del st.session_state.delete_id
                                    del st.session_state.delete_symbol
                                    st.rerun()

                        
                        
                        if "edit_id" in st.session_state:

                            st.markdown("### ✏️ Update Stock")

                            # 🔥 ACTION SELECT
                            action = st.radio(
                                "Action",
                                ["Buy ➕", "Sell ➖"]
                            )

                            # 🔥 INPUT
                            qty = st.number_input("Quantity", min_value=1)

                            price = 0
                            if action == "Buy ➕":
                                price = st.number_input("Buy Price", min_value=0.0)

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("Confirm"):

                                    current_qty = st.session_state.edit_qty
                                    current_price = st.session_state.edit_price

                                    # -------- BUY --------
                                    if action == "Buy ➕":

                                        new_qty = current_qty + qty

                                        new_price = (
                                            (current_qty * current_price + qty * price)
                                            / new_qty
                                        )

                                    # -------- SELL --------
                                    else:

                                        new_qty = current_qty - qty

                                        if new_qty <= 0:
                                            # DELETE STOCK
                                            safe_request(
                                                "DELETE",
                                                f"{API_URL}/portfolio/{st.session_state.edit_id}",
                                                headers=headers
                                            )

                                            st.success("Stock removed 🗑️")
                                            del st.session_state.edit_id
                                            st.rerun()

                                        new_price = current_price

                                    # -------- UPDATE --------
                                    status, data = safe_request(
                                        "PUT",
                                        f"{API_URL}/portfolio/{st.session_state.edit_id}",
                                        json={
                                            "quantity": int(new_qty),
                                            "buy_price": float(new_price)
                                        },
                                        headers=headers
                                    )

                                    if status == 200:
                                        st.success("Updated ✅")
                                        del st.session_state.edit_id
                                        st.rerun()
                                    else:
                                        show_error(data)

                            with col2:
                                if st.button("Cancel"):
                                    del st.session_state.edit_id
                                    st.rerun()
                        
            

        
        # ---------- CREATE FOLDER MODAL ----------
        if st.session_state.show_create_folder:

            st.subheader("Create Folder")

            folder_name = st.text_input("Folder Name")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Create"):

                    if folder_name.strip() == "":
                        st.warning("Enter folder name")

                    else:
                        clean_name = folder_name.strip()

                        # get backend folders also
                        existing_names = []

                        # from session
                        existing_names += st.session_state.folders

                        # from backend
                        status, data = safe_request("GET", f"{API_URL}/portfolio", headers=headers)

                        if status == 200 and "data" in data:
                            df = pd.DataFrame(data["data"])
                            if not df.empty:
                                existing_names += df["folder_name"].dropna().tolist()

                        # check duplicate (case-insensitive)
                        if any(f.lower() == clean_name.lower() for f in existing_names):
                            st.warning("Folder already exists")
                        else:
                            st.session_state.folders.append(clean_name)
                            st.session_state.show_create_folder = False
                            st.rerun()

            with col2:
                if st.button("Cancel"):
                    st.session_state.show_create_folder = False
                    st.rerun()
    
    
                 
                

#  WATCHLIST


    elif page == "Watchlist":

        st.title("📊 Watchlist")

        # ---------------- ADD STOCK ----------------

        st.subheader("Add Stock")

        stock_symbol = st.text_input("Stock Symbol (example: AAPL)").upper()

        if st.button("Add to Watchlist"):

            status, data = safe_request(
                "GET",
                f"{API_URL}/watchlist",
                headers=headers
            )

            if status == 200:

                df_watch = pd.DataFrame(data.get("data", []))

                if not df_watch.empty and stock_symbol in df_watch["symbol"].values:

                    st.warning("Stock already in watchlist")

                else:

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/watchlist",
                        json={"stock_symbol": stock_symbol},
                        headers=headers
                    )

                    if status == 200:
                        st.success("Stock added to watchlist")
                        st.rerun()
                    else:
                        show_error(data)

            else:
                show_error(data)

        st.divider() # here is the stop right now okay...

        # ---------------- LOAD WATCHLIST ----------------

        st.subheader("Your Watchlist")

        status, data = safe_request(
            "GET",
            f"{API_URL}/watchlist",
            headers=headers
        )

        if status == 200:

            df = pd.DataFrame(data.get("data", []))
            

            if df.empty:
                st.info("No stocks in watchlist")

            else:

                # -------- GET LIVE PRICE --------

                df["current_price"] = df["symbol"].apply(get_current_price)

                # -------- TEMP PREVIOUS CLOSE --------

                df["previous_close"] = df["current_price"] * 0.98

                # -------- CALCULATIONS --------

                df["change"] = df["current_price"] - df["previous_close"]

                df["change_percent"] = (df["change"] / df["previous_close"]) * 100

                # -------- TABLE HEADER --------

                h1, h2, h3, h4, h5 = st.columns(5)

                h1.markdown("**Symbol**")
                h2.markdown("**Price**")
                h3.markdown("**Change**")
                h4.markdown("**Change %**")
                h5.markdown("**Delete**")

                st.divider()

                # -------- ROWS --------

                for _, row in df.iterrows():

                    c1, c2, c3, c4, c5 = st.columns(5)

                    symbol = row["symbol"]

                    price = round(row["current_price"], 2)

                    change = round(row["change"], 2)

                    percent = round(row["change_percent"], 2)

                    if percent >= 0:
                        change_text = f"▲ {percent}%"
                        color = "green"
                    else:
                        change_text = f"▼ {percent}%"
                        color = "red"

                    # clickable symbol → company explorer
                    token = st.session_state.token
                    username = st.session_state.username

                    c1.markdown(
                        f"<a href='?symbol={symbol}&token={token}&username={username}'>{symbol}</a>",
                        unsafe_allow_html=True
                    )

                    c2.write(price)

                    c3.write(change)

                    c4.markdown(
                        f"<span style='color:{color};font-weight:600'>{change_text}</span>",
                        unsafe_allow_html=True
                    )

                    # delete button
                    if c5.button("Delete", key=f"watch_delete_{row['id']}"):

                        status, data = safe_request(
                            "DELETE",
                            f"{API_URL}/watchlist/{row['id']}",
                            headers=headers
                        )

                        if status == 200:
                            st.success("Stock removed")
                            st.rerun()
                        else:
                            show_error(data)

        else:
            show_error(data)
  
    #  ALERTS


    elif page == "Alerts":
        if "show_alert_modal" not in st.session_state:
            st.session_state.show_alert_modal = False

        if st.button("➕ Create Alert"):
            st.session_state.show_alert_modal = True
            
        if st.session_state.show_alert_modal:

            st.markdown("### Create Alert")

            symbol = st.text_input("Symbol").upper()

            condition = st.selectbox(
                "Condition",
                ["<", "<=", ">", ">=", "="]
            )

            threshold = st.number_input("Value", value=0.0)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Create Alert Confirm"):

                    if symbol.strip() == "":
                        st.warning("Enter symbol")
                        st.stop()

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/alerts",
                        json={
                            "stock_symbol": symbol,
                            "metric": "price",
                            "condition": condition,
                            "threshold": threshold
                        },
                        headers=headers
                    )

                    if status == 200:
                        st.success("Alert created!")
                        st.session_state.show_alert_modal = False
                        st.rerun()
                    else:
                        show_error(data)

            with col2:
                if st.button("Cancel"):
                    st.session_state.show_alert_modal = False
                    st.rerun()

        
        
        st.subheader("Triggered Alerts")

        status, data = safe_request(
            "GET",
            f"{API_URL}/alerts",
            headers=headers
        )

        if status == 200:

            df = pd.DataFrame(data.get("data", []))

            if df.empty:
                st.info("No alerts created yet")

            else:

                triggered_map = {}

                for _, row in df.iterrows():

                    symbol = row["stock_symbol"]
                    threshold = row["threshold"]
                    condition = row["condition"]

                    current_price = get_current_price(symbol)

                    triggered = False

                    if condition == ">" and current_price > threshold:
                        triggered = True
                    elif condition == "<" and current_price < threshold:
                        triggered = True
                    elif condition == ">=" and current_price >= threshold:
                        triggered = True
                    elif condition == "<=" and current_price <= threshold:
                        triggered = True
                    elif condition == "=" and current_price == threshold:
                        triggered = True

                    if triggered:

                        change = current_price - threshold
                        change_percent = (change / threshold) * 100 if threshold != 0 else 0
                        key = f"{symbol}_{condition}_{threshold}"

                        triggered_map[key] = {
                            "symbol": symbol,
                            "threshold": threshold,
                            "current_price": current_price,
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2)
                        }
                triggered_rows = list(triggered_map.values())

                if not triggered_rows:
                    st.info("No alerts triggered yet")

                else:

                    st.success(f"{len(triggered_rows)} Alerts Triggered 🚀")

                    for row in triggered_rows:

                        col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])

                        symbol = row["symbol"]

                        token = st.session_state.token
                        username = st.session_state.username

                        col1.markdown(
                            f"<a href='?symbol={symbol}&token={token}&username={username}'>{symbol}</a>",
                            unsafe_allow_html=True
                        )

                        col2.write(f"Old: {row['threshold']}")
                        col3.write(f"Current: {row['current_price']}")

                        if row["change_percent"] >= 0:
                            color = "green"
                            arrow = "▲"
                        else:
                            color = "red"
                            arrow = "▼"

                        col4.markdown(
                            f"<span style='color:{color}'>{arrow} {row['change']}</span>",
                            unsafe_allow_html=True
                        )

                        col5.markdown(
                            f"<span style='color:{color}'>{arrow} {row['change_percent']}%</span>",
                            unsafe_allow_html=True
                        )

        else:
            show_error(data)

        

        st.subheader("Delete Alert")

        delete_symbol = st.text_input("Enter Symbol").upper()

        if st.button("Delete Alert by Symbol"):

            status, data = safe_request(
                "GET",
                f"{API_URL}/alerts",
                headers=headers
            )

            if status == 200:
                for alert in data.get("data", []):
                    if alert["stock_symbol"] == delete_symbol:
                        safe_request(
                            "DELETE",
                            f"{API_URL}/alerts/{alert['id']}",
                            headers=headers
                        )

                st.success("Deleted!")
                st.rerun()

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