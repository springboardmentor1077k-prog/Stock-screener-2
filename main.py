import streamlit as st
import requests
import yfinance as yf

BACKEND_URL = "http://localhost:8000/query"

st.title("AI Powered Stock Screener")

nl_query = st.text_input("Enter your prompt here")

if st.button("Submit Query"):

    if nl_query.strip() == "":
        st.warning("Please enter a query.")
    else:
        try:
            response = requests.post(
                BACKEND_URL,
                params={"nl_query": nl_query}
            )

            if response.status_code == 200:
                data = response.json()
                st.success("DSL Generated Successfully")
                st.json(data["dsl"])
            else:
                st.error(response.json()["detail"])

        except Exception as e:
            st.error("Backend connection failed")