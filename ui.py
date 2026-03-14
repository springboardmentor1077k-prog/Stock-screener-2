import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(layout="wide")

# ---------- STATE MANAGEMENT ----------
if "query_state" not in st.session_state:
    st.session_state.query_state = ""

if "result_state" not in st.session_state:
    st.session_state.result_state = None

if "loading_state" not in st.session_state:
    st.session_state.loading_state = False


# ---------- CSS ----------
st.markdown("""
<style>

.block-container{
padding-top:2rem;
padding-left:3rem;
padding-right:3rem;
}

.hero{
text-align:center;
margin-top:60px;
margin-bottom:40px;
}

.hero h1{
font-size:52px;
font-weight:700;
}

.hero span{
color:#2b59ff;
}

.hero p{
color:#6b7280;
font-size:18px;
}

.searchbox{
max-width:800px;
margin:auto;
}

.searchbox .stButton button{
height:38px;
margin-top:0px;
}

.card{
background:white;
border:1px solid #e5e7eb;
border-radius:14px;
padding:22px;
margin-top:20px;
box-shadow:0px 2px 6px rgba(0,0,0,0.04);
}

.market{
background:white;
border:1px solid #e5e7eb;
border-radius:14px;
padding:22px;
}

</style>
""", unsafe_allow_html=True)


# ---------- SIDEBAR ----------
st.sidebar.title("Stock Screener")

st.sidebar.markdown("""
Screener  
Portfolio  
Watchlist  
Alerts
""")


# ---------- HERO ----------
st.markdown("""
<div class="hero">
<h1>Find your next <span>Investment</span></h1>
<p>Scan 15,000+ tickers with natural language queries or use institutional-grade screening tools.</p>
</div>
""", unsafe_allow_html=True)


# ---------- SEARCH ----------
st.markdown('<div class="searchbox">', unsafe_allow_html=True)

with st.form("search_form"):

    col1, col2 = st.columns([6,1])

    with col1:
        query = st.text_input(
            "",
            value=st.session_state.query_state,
            placeholder="Try 'pe ratio less than 20'",
            label_visibility="collapsed"
        )

    with col2:
        search = st.form_submit_button("Search", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


# ---------- API CALL ----------
if search and query:

    st.session_state.query_state = query
    st.session_state.loading_state = True

    with st.spinner("Fetching results..."):

        try:
            response = requests.post(
                API_URL,
                json={"query": query}
            )

            if response.status_code == 200:

                result = response.json()
                st.session_state.result_state = result

            else:
                st.session_state.result_state = {
                    "error": "Server returned an error"
                }

        except requests.exceptions.ConnectionError:

            st.session_state.result_state = {
                "error": "Cannot connect to backend API"
            }

        except Exception as e:

            st.session_state.result_state = {
                "error": "Unexpected error occurred"
            }

    st.session_state.loading_state = False


# ---------- RESULT RENDER ----------
if st.session_state.result_state:

    result = st.session_state.result_state

    if "error" in result:

        st.error(result["error"])

    else:

        data = result.get("data", [])

        if len(data) == 0:

            st.info("No results found for your query.")

        else:

            st.markdown("### Screening Results")

            df = pd.DataFrame(data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
# ---------- MAIN GRID ----------
left, right = st.columns([3,1], gap="large")


# ---------- EXPERT SCREENERS ----------
with left:

    st.subheader("Expert Screeners")

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="card">
        <h4>Value Discovery</h4>
        <p>Identifies profitable companies trading below their historical average P/E.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
        <h4>Momentum Chasers</h4>
        <p>Stocks breaking out of consolidation patterns on high volume.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="card">
        <h4>Dividend Aristocrats</h4>
        <p>Companies increasing dividends for more than 25 consecutive years.</p>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="card">
        <h4>Tech Disruptors</h4>
        <p>Early stage technology companies with strong YoY growth.</p>
        </div>
        """, unsafe_allow_html=True)


# ---------- MARKET PANEL ----------
with right:

    st.subheader("Market Pulse")

    st.markdown("""
    <div class="market">
    <p><b>S&P 500</b> &nbsp;&nbsp; +0.82%</p>
    <p><b>NASDAQ 100</b> &nbsp;&nbsp; +1.14%</p>
    <p><b>DOW JONES</b> &nbsp;&nbsp; -0.06%</p>
    <p><b>RUSSELL 2000</b> &nbsp;&nbsp; +1.05%</p>
    </div>
    """, unsafe_allow_html=True)