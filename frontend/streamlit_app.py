import streamlit as st
import requests
import pandas as pd

# -------------------------------
# PAGE CONFIG
# -------------------------------

st.set_page_config(
    page_title="AI Stock Screener",
    layout="wide"
)

# -------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------

if "query" not in st.session_state:
    st.session_state.query = ""

if "results" not in st.session_state:
    st.session_state.results = []

if "message" not in st.session_state:
    st.session_state.message = ""

# -------------------------------
# PAGE TITLE
# -------------------------------

st.title("AI Stock Screener")

st.markdown("### Enter Natural Language Query")

# -------------------------------
# QUERY INPUT
# -------------------------------

query_input = st.text_input(
    "Query",
    value=st.session_state.query,
    placeholder="Show companies with PE ratio less than 20"
)

# -------------------------------
# SEARCH FUNCTION
# -------------------------------

def run_query(query):

    try:

        with st.spinner("Searching companies..."):

            response = requests.post(
                "http://127.0.0.1:8000/query",
                json={"query": query}
            )

            data = response.json()

            if "results" in data:

                results = data["results"].get("data", [])

                if len(results) == 0:
                    st.session_state.results = []
                    st.session_state.message = "No companies satisfy the condition"

                else:
                    st.session_state.results = results
                    st.session_state.message = ""

            else:
                st.session_state.results = []
                st.session_state.message = "No companies satisfy the condition"

    except Exception as e:

        st.session_state.results = []
        st.session_state.message = "Backend connection error"


# -------------------------------
# SEARCH BUTTON
# -------------------------------

if st.button("Search"):

    st.session_state.query = query_input

    if query_input.strip() != "":
        run_query(query_input)

    else:
        st.session_state.results = []
        st.session_state.message = "Please enter a query"


# -------------------------------
# QUERY SUGGESTIONS
# -------------------------------

st.markdown("### Suggested Queries")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("technology companies with pe ratio < 30"):
        st.session_state.query = "technology companies with pe ratio < 30"
        run_query(st.session_state.query)

with col2:
    if st.button("companies with revenue > 100B"):
        st.session_state.query = "companies with revenue > 100B"
        run_query(st.session_state.query)

with col3:
    if st.button("companies with promoter holding > 50%"):
        st.session_state.query = "companies with promoter holding > 50%"
        run_query(st.session_state.query)


# -------------------------------
# DISPLAY MESSAGE
# -------------------------------

if st.session_state.message != "":
    st.warning(st.session_state.message)


# -------------------------------
# DISPLAY RESULTS
# -------------------------------

if len(st.session_state.results) > 0:

    st.markdown("### Results")

    df = pd.DataFrame(st.session_state.results)

    st.dataframe(
        df,
        use_container_width=True
    )


    with st.spinner("Searching companies..."):
        response = requests.post(...)