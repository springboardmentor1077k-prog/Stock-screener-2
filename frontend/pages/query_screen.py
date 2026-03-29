import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="StockSense AI", layout="wide")

# ---------- GLOBAL STYLE ----------
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

/* ---------- BRAND ---------- */

.brand{
font-family:'Orbitron', sans-serif;
font-size:40px;
font-weight:700;
letter-spacing:1.5px;
color:#eaf2ff;
text-shadow:0 0 10px rgba(59,130,246,0.35);
}

/* ---------- NAV BUTTONS ---------- */

div[data-testid="stButton"] button{
font-size:15px;
font-weight:500;
padding:10px 14px;
border-radius:10px;
border:1px solid rgba(59,130,246,0.45);
background:rgba(37,99,235,0.06);
color:#dbeafe;
}

/* ---------- SEARCH BOX ---------- */

div[data-baseweb="input"]{

border:1px solid rgba(59,130,246,0.35) !important;
border-radius:14px !important;
background:#0b1629 !important;

}

/* INPUT TEXT */

div[data-baseweb="input"] input{

height:58px !important;
font-size:18px !important;

padding-top:0px !important;
padding-bottom:0px !important;

display:flex;
align-items:center;

background:#0b1629 !important;
color:white !important;

outline:none !important;
box-shadow:none !important;

}

/* REMOVE RED BORDER */

div[data-baseweb="input"]:focus-within{
border:1px solid rgba(59,130,246,0.35) !important;
box-shadow:none !important;
}

/* ---------- ANALYZE BUTTON ---------- */

button[kind="primary"]{

background:#4f67d6 !important;
border:none !important;
color:white !important;

font-weight:600;
height:48px;

border-radius:12px;

}

/* ---------- SECTION TITLES ---------- */

.section-title{
font-size:20px;
font-weight:600;
margin-bottom:10px;
color:#dbeafe;
}

</style>
""", unsafe_allow_html=True)


# ---------- AUTH ----------
if "token" not in st.session_state or st.session_state.token is None:
    st.warning("Please login first.")
    st.stop()


# ---------- SESSION ----------
if "query_history" not in st.session_state:
    st.session_state.query_history = []


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
    st.button("Discover", use_container_width=True)

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


# ---------- HERO ----------
st.markdown(
"""
<h1 style='text-align:center;font-size:40px;'>Intelligence in every trade</h1>

<p style='text-align:center;color:#9fb0c4;font-size:15px'>
Ask financial questions and screen companies instantly
</p>
""",
unsafe_allow_html=True
)


# ---------- SEARCH ----------
col1, col2, col3 = st.columns([1,2.5,1])

with col2:

    query = st.text_input(
        "",
        placeholder="Search companies with PE ratio less than 25"
    )

    run_query = st.button(
        "⚡ Analyze Market",
        use_container_width=True,
        type="primary"
    )


# ---------- BACKEND ----------
def run_query_backend(q):

    with st.spinner("Analyzing market..."):

        response = requests.post(
            f"{API_URL}/query",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            json={"query": q}
        )

        if response.status_code == 200:

            data = response.json()

            st.session_state.query_results = data["data"]
            st.session_state.last_query = q

            if q not in st.session_state.query_history:
                st.session_state.query_history.insert(0, q)

            st.switch_page("pages/result_screen.py")

        else:
            st.error("Query failed")


if run_query and query:
    run_query_backend(query)


st.write("")


# ---------- SUGGESTIONS + HISTORY ----------
left, spacer, right = st.columns([1,0.15,1])


with left:

    st.markdown("<div class='section-title'>𖡊 Suggested Queries</div>", unsafe_allow_html=True)

    suggestions = [
        "Show IT companies with PE ratio less than 25",
        "Find companies with revenue greater than 40000",
        "List companies with EBITDA greater than 15000",
        "Show companies in the IT sector"
    ]

    for s in suggestions:

        if st.button(s, use_container_width=True):
            run_query_backend(s)


with right:

    st.markdown("<div class='section-title'>⏱ Recent Searches</div>", unsafe_allow_html=True)

    if not st.session_state.query_history:

        st.write("No searches yet")
        st.write("Your previous queries will appear here")

    else:

        for q in st.session_state.query_history[:5]:

            if st.button(f"🔎 {q}", use_container_width=True):
                run_query_backend(q)