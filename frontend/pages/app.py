import streamlit as st
import requests
import logging as log

st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BACKEND_URL = "http://localhost:9000/query"

if "loading" not in st.session_state:
    st.session_state.loading = False
    


st.title("AI Powered Stock Screener")

nl_query = st.text_input("Enter your prompt here")
#st.write("Sending:", {"nl_query": nl_query})
submit_btn = st.button(
    "Submit",
    disabled=st.session_state.loading
)

if submit_btn:

    if nl_query.strip() == "":
        st.warning("Please enter a query.")
    else:
        st.session_state.loading = True

        with st.spinner("Processing your query... Please wait"):
            try:
                response = requests.post(
                    BACKEND_URL,
                    json={"nl_query": nl_query}
                )

                if response.status_code == 200:
                    data = response.json()
                    log.info("Generated Successfully")
                    st.json(data["dsl"])
                    log.info("Query processed successfully")
                else:
                    log.error(f"HTTP Error {response.status_code}: {response.text}")
                    #st.error(f"Request failed with status code {response.status_code}")

            except Exception:
                log.info("Backend connection failed")

        st.session_state.loading = False