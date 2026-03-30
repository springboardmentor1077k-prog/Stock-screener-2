from urllib import response

import streamlit as st
import requests
import pandas as pd

# restore token from query params
params = st.query_params
if "logout" in params:
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.show_user_menu = False
    st.query_params.clear()
    st.rerun()

if "symbol" in params:
    st.session_state.selected_company = params["symbol"]
    st.session_state.page = "Company Explorer"
    del st.query_params["symbol"]
    st.rerun()
    

if "folder" in params:
    st.session_state.selected_folder = params["folder"]
    st.session_state.page = "Portfolio"
    del st.query_params["folder"]
    st.rerun()

if "show_account_popup" not in st.session_state:
    st.session_state.show_account_popup = False
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Stock Intelligence",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

/* ONLY history buttons */
div[data-testid="stSidebar"] button[data-key^="history_"] {
    background-color: #f5f7fb;
    border: 1px solid #e0e0e0;
    border-radius: 0px;
    text-align: left;
    padding: 10px;
    font-size: 13px;
    margin-bottom: 8px;

    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* hover */
div[data-testid="stSidebar"] button[data-key^="history_"]:hover {
    background-color: #e8f0fe;
    border-color: #4a90e2;
    color: #4a90e2;
}

</style>
""", unsafe_allow_html=True)

query_params = st.query_params

# EDIT CLICK
if "edit_folder" in query_params:
    st.session_state.rename_folder = query_params["edit_folder"]

def format_query(q, max_len=20):
    if len(q) > max_len:
        return q[:max_len] + "..."
    return q




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
def get_all_companies():
    status, data = safe_request(
        "GET",
        f"{API_URL}/companies"
    )

    if status == 200:
        return data.get("data", [])
    
    return []
        
def get_sector(symbol):
    status, data = safe_request(
        "GET",
        f"{API_URL}/company/{symbol}/full-details",
        headers=headers
    )

    if status == 200:
        return data["data"].get("sector", "N/A")

    return "N/A"
# SESSION STATE INIT


if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "token" in params and st.session_state.token is None:
    st.session_state.token = params["token"]

if "username" in params and st.session_state.username is None:
    st.session_state.username = params["username"]

if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False
if "search_results" not in st.session_state:
    st.session_state.search_results = None
    
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
if "show_login" not in st.session_state:
    st.session_state.show_login = False


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

def require_login():
    if st.session_state.token is None:
        st.session_state.show_login = True
        st.rerun()

def get_current_price(symbol):

    status, data = safe_request(
        "GET",
        f"{API_URL}/company/{symbol}/price",
        headers=headers
    )

    if status == 200:
        return data["data"]["price"]

    return 0

def format_query_title(q, max_len=35):
    if not q:
        return ""

    # make it cleaner 
    q = q.replace("_", " ").capitalize()

    # trim long queries
    if len(q) > max_len:
        return q[:max_len] + "..."

    return q

st.markdown("""
<style>
/*  Only primary buttons (your login button) */
div.stButton > button[kind="primary"] {
    background-color: #ff4b4b;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}

/* Hover */
div.stButton > button[kind="primary"]:hover {
    background-color: #e63b3b;
    color: white;
}
</style>
""", unsafe_allow_html=True)
                        
 # LOGIN POPUP
if st.session_state.show_login:

    left, right = st.columns([3, 1])
    

    with left:
        st.image("images/login.jpg", use_container_width=True)

    #  RIGHT SIDE → LOGIN FORM
    with right:
        st.markdown("###  Welcome Back")
        st.caption("Login to access your AI stock dashboard")

        mode = st.radio("", ["Login", "Register"], horizontal=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if mode == "Register":
            email = st.text_input("Email")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(mode, use_container_width=True, type="primary"):

                if username == "" or password == "":
                    st.warning("Fill required fields")
                else:

                    if mode == "Login":
                        status, data = login(username, password)

                        if status == 200:
                            st.session_state.token = data["access_token"]
                            st.session_state.username = username
                            st.session_state.show_login = False

                            #  persist in browser (important)
                            st.query_params["token"] = data["access_token"]
                            st.query_params["username"] = username

                            st.rerun()
                        else:
                            show_error(data)

                    else:
                        if email == "":
                            st.warning("Email required")
                        else:
                            status, data = register(username, email, password)

                            if status == 200:
                                st.success("Registered! Now login")
                            else:
                                show_error(data)

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()

    st.stop()                    


# MAIN APP



headers = {}

if st.session_state.token:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }
st.sidebar.title(" AI Stock Platform")



if "page" not in st.session_state:
    st.session_state.page = "AI Screener"
#  HANDLE REDIRECT BEFORE SIDEBAR
if "go_to_company" in st.session_state:

    st.session_state.page = "Company Explorer"
    st.session_state.selected_company = st.session_state.go_to_company

    del st.session_state["go_to_company"]

    st.rerun()

st.sidebar.radio(
    "Navigation",
    ["AI Screener", "Portfolio", "Watchlist", "Alerts", "Company Explorer"],
    key="page"
)

st.sidebar.markdown("# History")

if st.session_state.token:

    status, data = safe_request(
        "GET",
        f"{API_URL}/history",
        headers=headers
    )

    if status == 200:
        history_list = data.get("data", [])
    else:
        history_list = []

    if len(history_list) == 0:
        st.sidebar.caption("No searches yet")

    else:
        for i, q in enumerate(history_list):

            title = q.lower()

            #  detect main meaning
            if "pe" in title:
                title = "Low PE Stocks"
            elif "eps" in title:
                title = "High EPS Stocks"
            elif "growth" in title:
                title = "High Growth Stocks"
            elif "revenue" in title:
                title = "Revenue Based Stocks"
            elif "profit" in title:
                title = "Profit Based Stocks"
            else:
                title = title.capitalize()

            #  trim long text
            if len(title) > 15:
                title = title[:15] + "..."

            

            if st.sidebar.button(title, key=f"history_{i}", use_container_width=True):
                st.session_state.last_query = q

else:
    st.sidebar.caption("Login to see history")


header_left, header_right = st.columns([9,1])
with header_left:
    if st.session_state.page == "AI Screener":
        st.title("AI Stock Intelligence")
    elif st.session_state.page == "Portfolio":
        st.title("📂 Portfolio")
    elif st.session_state.page == "Watchlist":
        st.title("Watchlist")
    elif st.session_state.page == "Alerts":
        st.title("🚨 Alerts")
    elif st.session_state.page == "Company Explorer":
        st.title("🏢 Company Explorer")

with header_right:

    #  NOT LOGGED IN
    if st.session_state.token is None:

        if st.button("Login / Signup"):
            st.session_state.show_login = True
            st.rerun()

    #  LOGGED IN → ONLY LOGOUT BUTTON
    else:
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.username = None
            st.query_params.clear()
            st.rerun()

   


    
   

    

if st.session_state.username:
    st.caption(f"Welcome, {st.session_state.username}")
 








#  SCREENER


if st.session_state.page == "AI Screener":
    st.session_state.show_login = False
    st.markdown("""
    Ask AI to find stocks based on financial metrics, growth indicators, or any custom criteria you have in mind.
    """)
    st.markdown("### Quick Queries")
    st.markdown("""
<style>
div.stButton > button {
    border-radius: 25px !important;
    padding: 8px 16px !important;
    border: 1px solid #ddd !important;
    background-color: #f9f9f9 !important;
    font-size: 14px !important;
}

div.stButton > button:hover {
    background-color: #e6f0ff !important;
    border-color: #4a90e2 !important;
    color: #4a90e2 !important;
}
</style>
""", unsafe_allow_html=True)

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

        #  NOT LOGGED IN
        if st.session_state.token is None:
            st.session_state.show_login = True
            st.rerun()

        # LOGGED IN
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

                results = data.get("data", [])

                st.session_state.search_results = results
                st.session_state.last_query = query
                st.session_state.page_number = 1
                st.success(f"Found {len(results)} companies")
                st.rerun()

            elif status == 401:
                st.error("Session expired. Please login again.")
                st.session_state.token = None
                st.rerun()

            else:
                show_error(data)

    if st.session_state.search_results is not None:

        if len(st.session_state.search_results) == 0:
            st.info("No companies matched your query.")

        else:

            df = pd.DataFrame(st.session_state.search_results)
            #  REMOVE DUPLICATES BASED ON SYMBOL
            df = df.drop_duplicates(subset=["symbol"], keep="first")

            st.markdown(f"### {len(df)} companies match your query")
            
            
            
            st.markdown("### Top 3 Companies")

            #  make sure values are numeric
            df["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce")

            #  remove missing values
            clean_df = df.dropna(subset=["market_cap"])

            #  now sort ALL companies and take top 3
            top = clean_df.sort_values(by="market_cap", ascending=False).head(3)

            for _, row in top.iterrows():
                st.write(f"{row['symbol']} — Market Cap: {round(row['market_cap']/1_000_000,2)}M")

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

            paginated_df = df.iloc[start:end].copy()

           # ========= FORMAT FUNCTIONS =========

            def format_number(x):
                try:
                    if isinstance(x, str) and any(s in x for s in ["B", "M", "K"]):
                        return x

                    x = float(x)

                    if x >= 1_000_000_000:
                        return f"{x/1_000_000_000:.1f}B"
                    elif x >= 1_000_000:
                        return f"{x/1_000_000:.1f}M"
                    elif x >= 1_000:
                        return f"{x/1_000:.1f}K"
                    else:
                        return round(x, 2)

                except:
                    return x


            def format_percent(x):
                try:
                    x = float(x)

                    #  FIX huge backend values
                    if abs(x) > 1000:
                        x = x / 1_000_000_000

                    return f"{round(x,2)}%"
                except:
                    return x


            # ========= APPLY FORMATTING =========

            # BIG NUMBERS
            for col in ["market_cap", "revenue", "debt"]:
                if col in paginated_df.columns:
                    paginated_df[col] = paginated_df[col].apply(format_number)

            # PERCENT
            for col in ["price_change_1y", "revenue_growth"]:
                if col in paginated_df.columns:
                    paginated_df[col] = paginated_df[col].apply(format_percent)

            # SMALL NUMBERS
            for col in ["eps", "pe_ratio"]:
                if col in paginated_df.columns:
                    paginated_df[col] = paginated_df[col].apply(
                        lambda x: round(float(x), 2) if x not in [None, ""] else x
                    )

            # SCORE FIX
            if "score" in paginated_df.columns:
                paginated_df["score"] = paginated_df["score"].apply(
                    lambda x: f"{float(x)/1_000_000:.2f}M" if x not in [None, ""] else ""
                )
                    
            st.data_editor(paginated_df, use_container_width=True, disabled=True)

            
            
            

            

            # ---------- Compact Pagination ----------
            if total_pages > 1:

                left_space, nav = st.columns([9,1])

                with nav:

                    prev_col, page_col, next_col = st.columns([1,1,1], gap="small")

                    if prev_col.button("◀", key="prev_page"):
                        if st.session_state.page_number > 1:
                            st.session_state.page_number -= 1

                    page_col.markdown(
                        f"""
                        <div style="
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:14px;
                            margin-top:4px;
                        ">
                            {st.session_state.page_number}/{total_pages}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if next_col.button("▶", key="next_page"):
                        if st.session_state.page_number < total_pages:
                            st.session_state.page_number += 1

            

            
            # ================= SAVE COMPANY =================
            st.markdown("### Save Company")

            col1, col2 = st.columns([4,1], gap="small")

            with col1:
                save_symbol = st.selectbox(
                    "Select Company",
                    df["symbol"].tolist(),
                    key="save_symbol"
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # align vertically

                if st.button(" Add", use_container_width=True):

                    if st.session_state.token is None:
                        st.session_state.show_login = True
                        st.rerun()

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/watchlist",
                        json={"stock_symbol": save_symbol},
                        headers=headers
                    )

                    if status == 200:
                        st.success(f"{save_symbol} added ")
                    else:
                        show_error(data)


            # ================= ADD TO PORTFOLIO =================
            st.markdown("### 📂 Add to Portfolio")

            #  get all companies from database
            companies = get_all_companies()

            #  extract symbols
            symbols = [c["symbol"] for c in companies]

            #  safety check
            if not symbols:
                st.warning("No companies found in database")
                st.stop()

            #  selectbox
            portfolio_symbol = st.selectbox(
                "Select Company",
                symbols,
                key="portfolio_symbol"
            )
            col1, col2 = st.columns(2)

            with col1:
                quantity = st.number_input("Quantity", min_value=1, value=1)

            with col2:
                buy_price = st.number_input("Buy Price", min_value=0.0, value=0.0)

            #  CURRENT PRICE
            current_price = 0
            if portfolio_symbol:
                current_price = get_current_price(portfolio_symbol)

                if current_price > 0:
                    st.info(f"Current Price: ₹{round(current_price,2)}")
                else:
                    st.warning("Price not available")

            #  LOAD FOLDERS
            folder_options = []

            if st.session_state.token:
                status, data = safe_request(
                    "GET",
                    f"{API_URL}/portfolio",
                    headers=headers
                )

                if status == 200:
                    df_port = pd.DataFrame(data.get("data", []))
                    if not df_port.empty and "folder_name" in df_port.columns:
                        folder_options = sorted(
                            df_port["folder_name"].dropna().unique().tolist()
                        )

            if not folder_options:
                folder_options = ["My Stocks"]

            selected_folder = st.selectbox("Select Folder", folder_options)

            #  ADD BUTTON
            if st.button("➕ Add to Portfolio", use_container_width=True):

                if st.session_state.token is None:
                    st.session_state.show_login = True
                    st.rerun()

                status, data = safe_request(
                    "POST",
                    f"{API_URL}/portfolio",
                    json={
                        "stock_symbol": portfolio_symbol,
                        "quantity": int(quantity),
                        "buy_price": float(buy_price),
                        "folder_name": selected_folder
                    },
                    headers=headers
                )

                if status == 200:
                    st.success(f"{portfolio_symbol} added to Portfolio ")
                else:
                    show_error(data)
            #  REMOVE DUPLICATES + CLEAN LIST
            symbols = list(dict.fromkeys(df["symbol"].tolist()))

            selected_symbol = st.selectbox(
                "Open company details",
                symbols,
                key="view_company_symbol"
            )

            if st.button("🔍 View Company", use_container_width=True):

                st.session_state["go_to_company"] = selected_symbol
                st.rerun()
            st.markdown("### EPS Comparison")

            st.bar_chart(df.set_index("symbol")["eps"])
            
            st.markdown("### AI Insight")

            st.info(
                f"The screener found {len(df)} companies matching your filters. "
                "These companies satisfy the financial conditions you provided."
            )
    

#  PORTFOLIO
elif st.session_state.page == "Portfolio":

    if st.session_state.selected_folder is None:
        pass

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

                if st.session_state.token is None:
                    st.session_state.show_login = True
                    st.rerun()

                st.session_state.show_create_folder = True
        
        # ---------- CREATE FOLDER MODAL ----------
        if st.session_state.show_create_folder:

            st.subheader("Create Folder")

            folder_name = st.text_input("Folder Name")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Create"):

                    if st.session_state.token is None:
                        st.session_state.show_login = True
                        st.rerun()

                    if folder_name.strip() == "":
                        st.warning("Enter folder name")
                        st.stop()

                    clean_name = folder_name.strip()

                    folders = []   #  ALWAYS DEFINE FIRST

                    if st.session_state.token:
                        status, data = safe_request(
                            "GET",
                            f"{API_URL}/folders",
                            headers=headers
                        )

                        if status == 200:
                            folders = data.get("data", [])

                    if clean_name.lower() in [f.lower() for f in folders]:
                        st.warning("Folder already exists")
                        st.stop()

                    status, data = safe_request(
                        "POST",
                        f"{API_URL}/folders",
                        json={"folder_name": clean_name},
                        headers={
                            "Authorization": f"Bearer {st.session_state.token}"
                        }
                    )

                    if status == 200:
                        st.success("Folder created")
                        st.session_state.show_create_folder = False
                        st.rerun()
                    else:
                        st.error("Folder already exists")

            with col2:
                if st.button("Cancel"):
                    st.session_state.show_create_folder = False
                    st.rerun()


    # ---------- SHOW FOLDERS ----------
    if st.session_state.selected_folder is None:

        folders = []

        if st.session_state.token is None:
            st.info("Login to view your portfolio")

        else:
            status, data = safe_request(
                "GET",
                f"{API_URL}/folders",   #  IMPORTANT CHANGE
                headers=headers
            )

            if status == 200:
                folders = data.get("data", [])
                folders = list(reversed(folders))

        if len(folders) == 0:
            st.info("No folders yet")

        else:
            for i, folder in enumerate(folders):

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
                    if st.button("✏️", key=f"edit_folder_{folder}_{i}"):
                        st.session_state.rename_folder = folder
                        st.rerun()

                with col3:
                    if st.button("🗑️", key=f"delete_folder_{folder}_{i}"):

                        status, data = safe_request(
                            "DELETE",
                            f"{API_URL}/folders/{folder}",
                            headers={
                                "Authorization": f"Bearer {st.session_state.token}"
                            }
                        )

                        if status == 200:
                            st.success(f"{folder} deleted ")
                            st.rerun()
                        else:
                            show_error(data)

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
                            
                            if st.session_state.token is None:
                                st.session_state.show_login = True
                                st.rerun()
                            st.write("SENDING:", {
                                "old_name": st.session_state.rename_folder,
                                "new_name": new_name.strip()
                            })
                            status, data = safe_request(
                                "PUT",
                                f"{API_URL}/portfolio/rename-folder",
                                json={
                                    "old_name": st.session_state.rename_folder,
                                    "new_name": new_name.strip()
                                },
                                headers={
                                    "Authorization": f"Bearer {st.session_state.token}",
                                    "Content-Type": "application/json"
                                }
                            )

                            if status == 200:
                                st.success("Renamed ")
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
            col1, col2 = st.columns(2)

            with col1:
                quantity = st.number_input("Quantity", min_value=1, value=1)

            with col2:
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

                    #  LOGIN CHECK (ADD THIS)
                    if st.session_state.token is None:
                        st.session_state.show_login = True
                        st.rerun()

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
                            "folder_name": folder
                        },
                        headers=headers
                    )

                    if status == 200:
                        st.success("Stock Added ")
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

                if "folder_name" in df.columns:
                    folder_df = df[
                        df["folder_name"].fillna("").str.strip()
                        == str(folder).strip()
                    ]
                else:
                    st.warning("No folder data available")
                    folder_df = pd.DataFrame()

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
                    folder_df["sector"] = folder_df["symbol"].apply(get_sector)

                    display_df = pd.DataFrame({
                        "Symbol": folder_df["symbol"],
                        "Sector": folder_df["sector"],
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
                    h2.markdown("**Sector**")
                    h3.markdown("**Qty**")
                    h4.markdown("**Buy Price**")
                    h5.markdown("**Current**")
                    h6.markdown("**Value**")
                    h7.markdown("**Change %**")
                    h8.markdown("**Edit**")
                    h9.markdown("**Delete**")
                    
                    st.markdown(
    "<hr style='margin:1px 0 4px 0; border:0.5px solid #ddd;'>",
    unsafe_allow_html=True
)

                    

                    # ROWS
                    for _, row in folder_df.iterrows():

                        cols = st.columns([2,3,2,2,2,2,2,1,1])

                        with cols[0]:

                            token = st.session_state.token
                            username = st.session_state.username
                            symbol = row["symbol"]

                            st.markdown(
                                f"""
                                <a href="?symbol={symbol}&token={token}&username={username}" 
                                style="text-decoration:none; font-size:16px;">
                                {symbol}
                                </a>
                                """,
                                unsafe_allow_html=True
                            )

                        with cols[1]:
                            st.write(row["sector"])

                        with cols[2]:
                            st.write(row["quantity"])

                        with cols[3]:
                            st.write(round(row["buy_price"], 1))

                        with cols[4]:
                            st.write(round(row["current_price"], 2))

                        with cols[5]:
                            st.write(round(row["current_value"], 2))

                        with cols[6]:

                            percent = round(row["profit_percent"], 2)

                            if percent >= 0:
                                st.markdown(
                                    f"<span style='color:green; font-weight:600;'>▲ {percent}%</span>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<span style='color:red; font-weight:600;'>▼ {abs(percent)}%</span>",
                                    unsafe_allow_html=True
                                )

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
                        st.markdown(
                            "<hr style='margin:1px 0; border:0.5px solid #ddd;'>",
                            unsafe_allow_html=True
                        )
                    
                    
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
                                    st.success("Updated ")
                                    del st.session_state.edit_id
                                    st.rerun()
                                else:
                                    show_error(data)

                        with col2:
                            if st.button("Cancel"):
                                del st.session_state.edit_id
                                st.rerun()
                    
        


                
            

#  WATCHLIST


elif st.session_state.page == "Watchlist":
    

    st.title(" Watchlist")
    

    # ---------------- ADD STOCK ----------------

    st.subheader("Add Stock")

    stock_symbol = st.text_input("Stock Symbol (example: AAPL)").upper()

    if st.button("Add to Watchlist"):

        if st.session_state.token is None:
            st.session_state.show_login = True
            st.rerun()

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


    st.divider() 

    # ---------------- LOAD WATCHLIST ----------------

    st.subheader("Your Watchlist")
    #  NOT LOGGED IN → NO API CALL
    if st.session_state.token is None:
        st.info("Login to view your watchlist")
        df = pd.DataFrame()

    #  LOGGED IN → LOAD DATA
    else:
        status, data = safe_request(
            "GET",
            f"{API_URL}/watchlist",
            headers=headers
        )

        if status == 200:
            df = pd.DataFrame(data.get("data", []))
        else:
            show_error(data)
            df = pd.DataFrame()
        

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

                    if st.session_state.token is None:
                        st.session_state.show_login = True
                        
                        st.rerun()

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


#  ALERTS


elif st.session_state.page == "Alerts":
    

    st.title("🔔 Alerts")
    
    view = st.radio(
        "Select View",
        ["Your Alerts", "Triggered Alerts"]
    )

    # ---------------- CREATE ALERT ----------------
    if "show_alert_modal" not in st.session_state:
        st.session_state.show_alert_modal = False

    if st.button("➕ Create Alert"):
        if st.session_state.token is None:
            st.session_state.show_login = True
            st.rerun()
        st.session_state.show_alert_modal = True

    if st.session_state.show_alert_modal:

        st.markdown("### Create Alert")

        symbol = st.text_input("Symbol").upper()
        

        # fetch metrics
        status, data = safe_request(
            "GET",
            f"{API_URL}/alerts/metrics",
            headers=headers
        )

        metrics = []

        if status == 200:
            metrics = data.get("data", [])
        else:
            st.warning("Failed to load metrics")

        metric = st.selectbox("Metric", metrics)

        condition = st.selectbox(
            "Condition",
            ["<", ">", "<=", ">=", "="]
        )

        threshold = st.number_input("Value", value=0.0)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Create Alert Confirm"):

                if symbol.strip() == "":
                    st.warning("Enter symbol")
                    st.stop()
                require_login()

                status, data = safe_request(
                    "POST",
                    f"{API_URL}/alerts",
                    json={
                        "stock_symbol": symbol,
                        "metric": metric,
                        "condition": condition,
                        "threshold": threshold
                    },
                    headers=headers
                )

                if status == 200:
                    st.success("Alert created ")
                    st.session_state.show_alert_modal = False
                    st.rerun()
                else:
                    show_error(data)

        with col2:
            if st.button("Cancel"):
                st.session_state.show_alert_modal = False
                st.rerun()

    # ---------------- SHOW ALERTS ----------------
    if view == "Your Alerts":

        st.subheader("Your Alerts")
        #  NOT LOGGED IN → NO API CALL
        if st.session_state.token is None:
            st.info("Login to view your alerts")
            alerts = []

        #  LOGGED IN → LOAD DATA
        else:
            status, data = safe_request(
                "GET",
                f"{API_URL}/alerts",
                headers=headers
            )

            if status == 200:
                alerts = data.get("data", [])
            else:
                show_error(data)
                alerts = []

            if not alerts:
                st.info("No alerts created yet")

            else:
                for alert in alerts:

                    col1, col2 = st.columns([8,1])

                    col1.write(
                        f"{alert['symbol']} | {alert['metric']} {alert['condition']} {alert['threshold']}"
                    )

                    if col2.button("🗑️", key=f"del_{alert['id']}"):
                        require_login()

                        safe_request(
                            "DELETE",
                            f"{API_URL}/alerts/{alert['id']}",
                            headers=headers
                        )

                        st.rerun()

        

    # ---------------- CHECK ALERTS ----------------
    if view == "Triggered Alerts":

        st.subheader("Triggered Alerts")

        if st.button("Check Alerts"):
            require_login()

            status, data = safe_request(
                "GET",
                f"{API_URL}/alerts/check",
                headers=headers
            )

            if status == 200:

                alerts = data.get("data", [])

                if not alerts:
                    st.info("No alerts triggered")

                else:

                    st.success(f"{len(alerts)} Alerts Triggered 🚀")

                    import pandas as pd

                    df = pd.DataFrame(alerts)

                    df = df.rename(columns={
                        "symbol": "Symbol",
                        "metric": "Metric",
                        "current_value": "Current Value",
                        "threshold": "Threshold"
                    })

                    st.dataframe(df, use_container_width=True)

            else:
                show_error(data)

        

# ================================
#  COMPANY EXPLORER 
# ================================
elif st.session_state.page == "Company Explorer":

    st.title("📊 Company Explorer")

    #  SEARCH
    symbol_input = st.text_input(
            "Enter Company Symbol (e.g., INFY, AAPL)",
            value=st.session_state.get("selected_company", ""),
            key="company_search_box"
        )

    if st.button("Search Company", use_container_width=True):

        if symbol_input.strip() != "":
            st.session_state["selected_company"] = symbol_input.upper()
            st.rerun()

    symbol = st.session_state.get("selected_company")

    if symbol:

        # =========================
        #  FETCH DATA
        # =========================
        detail_status, detail_data = safe_request(
            "GET",
            f"{API_URL}/company/{symbol}/full-details",
            headers=headers
        )

        price_status, price_data = safe_request(
            "GET",
            f"{API_URL}/company/{symbol}/price-history?period=1Y",
            headers=headers
        )

        left, right = st.columns([2,1])

        # =========================
        #  LEFT SIDE → GRAPH
        # =========================
        with left:

            if price_status == 200:

                df = pd.DataFrame(price_data["data"])

                if not df.empty:

                    df["date"] = pd.to_datetime(df["date"])

                    import plotly.graph_objects as go

                    #  PRICE
                    first_price = df["close"].iloc[0]
                    last_price = df["close"].iloc[-1]

                    change = last_price - first_price
                    percent = (change / first_price) * 100

                    st.metric(
                        label=f"{symbol} Price",
                        value=round(last_price, 2),
                        delta=f"{round(percent,2)}%"
                    )

                    # =========================
                    #  GRAPH
                    # =========================
                    fig = go.Figure()

                    # Candlestick
                    fig.add_trace(go.Candlestick(
                        x=df["date"],
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                        increasing_line_color="green",
                        decreasing_line_color="red",
                        visible=True
                    ))

                    # Line
                    fig.add_trace(go.Scatter(
                        x=df["date"],
                        y=df["close"],
                        mode="lines",
                        line=dict(color="blue", width=2),
                        visible=False
                    ))

                    # Area
                    fig.add_trace(go.Scatter(
                        x=df["date"],
                        y=df["close"],
                        mode="lines",
                        fill="tozeroy",
                        line=dict(color="green", width=2),
                        fillcolor="rgba(0,255,0,0.1)",
                        visible=False
                    ))

                    # =========================
                    #  SMALL BUTTONS (TOP RIGHT)
                    # =========================
                    fig.update_layout(
                        updatemenus=[
                            dict(
                                type="buttons",
                                direction="left",
                                x=0.98,
                                y=0.98,
                                xanchor="right",
                                yanchor="top",
                                bgcolor="rgba(255,255,255,0.5)",
                                bordercolor="gray",
                                borderwidth=1,
                                pad={"r": 2, "t": 2},
                                font=dict(size=10),
                                buttons=[
                                    dict(label="🕯️", method="update", args=[{"visible": [True, False, False]}]),
                                    dict(label="📈", method="update", args=[{"visible": [False, True, False]}]),
                                    dict(label="🌊", method="update", args=[{"visible": [False, False, True]}]),
                                ]
                            )
                        ]
                    )

                    #  STYLE
                    fig.update_layout(
                        template="plotly_white",
                        height=450,
                        margin=dict(l=10, r=10, t=20, b=10),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=False),
                    )

                    fig.update_layout(xaxis_rangeslider_visible=False)

                    #  TIME FILTER BUTTONS
                    fig.update_layout(
                        xaxis=dict(
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=1, label="1D", step="day", stepmode="backward"),
                                    dict(count=7, label="1W", step="day", stepmode="backward"),
                                    dict(count=1, label="1M", step="month", stepmode="backward"),
                                    dict(count=6, label="6M", step="month", stepmode="backward"),
                                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                                    dict(step="all", label="ALL")
                                ])
                            )
                        )
                    )

                    #  ONLY ONE GRAPH (FIXED)
                    st.plotly_chart(fig, use_container_width=True)

                    # =========================
                    #  OHLC
                    # =========================
                    latest = df.iloc[-1]

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Open", round(latest["open"],2))
                    col2.metric("High", round(latest["high"],2))
                    col3.metric("Low", round(latest["low"],2))
                    col4.metric("Close", round(latest["close"],2))

                else:
                    st.warning("No price data")

            else:
                st.error("Price API failed")

        # =========================
        #  RIGHT SIDE → DETAILS
        # =========================
        with right:

            if detail_status == 200:

                d = detail_data["data"]

                st.subheader(d["company_name"])
                st.caption(f"{d['symbol']} • {d['sector']}")

                st.divider()

                table_data = {
                    "Metric": [
                        "PE Ratio","EPS","Revenue","Profit","EBITDA",
                        "Debt","Cash","Revenue Growth","Profit Margin",
                        "ROE","ROA","Market Cap"
                    ],
                    "Value": [
                        d.get("pe_ratio"), d.get("eps"), d.get("revenue"),
                        d.get("profit"), d.get("ebitda"), d.get("debt"),
                        d.get("cash"), d.get("revenue_growth"),
                        d.get("profit_margin"), d.get("roe"),
                        d.get("roa"), d.get("market_cap")
                    ]
                }

                df_table = pd.DataFrame(table_data)

                st.dataframe(
                    df_table,
                    use_container_width=True,
                    hide_index=True,
                    height=min(500, 40 * len(df_table) + 40)
                )

            else:
                st.error("Company details failed")