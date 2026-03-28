import streamlit as st
import requests
import logging as log
import time
import os
import sys
from ui_components.result import render_results_table
from ui_components.navbar import logout_button


if "results" not in st.session_state:
    st.session_state.results = None
    

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))




log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BACKEND_URL = "http://localhost:9000/query"

if "loading" not in st.session_state:
    st.session_state.loading = False
 
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0
    
count_down = 5 
current_time = time.time()
time_since_last = current_time - st.session_state.last_request_time

button_disabled = (
    st.session_state.loading or
    time_since_last < count_down
)

st.title("AI Powered Stock Screener")

nl_query = st.text_input("Enter your prompt here")

st.markdown("""
### Some Frequently Asked Queries

- Show companies with PE more than 15  
- Show companies with PE less than 20 and promoter holding greater than 10
""")

submit_btn = st.button(
    "Submit",
    disabled=st.session_state.loading
)




if submit_btn:

    if nl_query.strip() == "":
        st.warning("Please enter a query.")
    else:
        st.session_state.loading = True
        st.session_state.last_request_time = time.time()

        with st.spinner("Processing your query... Please wait..."):
            try:
                response = requests.post(
                    BACKEND_URL,
                    json={"nl_query": nl_query},
                    timeout=10
                )

                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.results = data
                    log.info("Query processed successfully")
                    results = data.get("data", [])
                    count = data.get("count", 0)

                    if count == 0:
                        st.warning("No companies matched your query.")
                    else:
                        st.success(f"Found {count} matching companies.")
                        st.session_state.results = data

            
                elif response.status_code == 422:
                    st.session_state.results = None
                    error_detail = response.json().get("detail", {})

                    st.warning(
                        error_detail.get(
                            "message",
                            "We could not understand your query. Please retype."
                        )
                    )

                    if "suggestion" in error_detail:
                        st.info(error_detail["suggestion"])


                elif response.status_code == 429:
                    st.error("Too many requests. Please wait before retrying.")

                else:
                    log.error(f"HTTP Error {response.status_code}: {response.text}")
                    st.error("Unexpected server error.")

            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")

            except Exception as e:
                log.error(f"Backend connection failed: {str(e)}")
                st.error("Backend connection failed.")

        st.session_state.loading = False
        
if st.session_state.results is not None:
    render_results_table(st.session_state.results)
    

if time_since_last < count_down:
    remaining = int(count_down - time_since_last)
    st.info(f"Please wait {remaining} seconds before submitting.")
    
    
logout_button()