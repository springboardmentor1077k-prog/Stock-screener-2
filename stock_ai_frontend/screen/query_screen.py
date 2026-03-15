import streamlit as st
import requests
import time

st.title("🔎 Query Screen")

# -----------------------
# Query Suggestions
# -----------------------

suggestions = [
    "show companies with PE ratio < 20",
    "show companies with revenue > 1000",
    "show companies with market cap > 50000"
]

st.subheader("Query Suggestions")

for s in suggestions:
    if st.button(s):
        st.session_state["query"] = s

# -----------------------
# Query Input
# -----------------------

query = st.text_input(
    "Enter your query",
    value=st.session_state.get("query", "")
)

# -----------------------
# Submit Query
# -----------------------

if st.button("Submit Query"):

    with st.spinner("Running AI Screener..."):

        url = "http://127.0.0.1:8000/query"
        params = {"user_query": query}

        response = requests.post(url, params=params)
        data = response.json()

        # store results globally
        st.session_state["results"] = data

        if data["status"] == "success":
            st.success("Query executed successfully")
        else:
            st.error(data["message"])
