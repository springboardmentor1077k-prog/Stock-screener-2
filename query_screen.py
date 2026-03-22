import streamlit as st
import requests
from state import set_results

def show_query_screen():
    st.title("📊 Stock Screener")

    query = st.text_input("Enter your query")

    if st.button("Search"):
        if query:
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/query",
                    params={"user_query": query}
                )

                data = response.json()

                # DEBUG (you can remove later)
                st.write("Response:", data)

                # Save results
                set_results(data.get("results", []))

                st.success("Query executed successfully")

            except:
                st.error("Backend not running")