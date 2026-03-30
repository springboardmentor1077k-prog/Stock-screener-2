import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any

# ==========================================
# CONFIGURATION
# ==========================================
API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(page_title="AI Stock Screener", page_icon="📈", layout="wide")

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
# Store results so they don't disappear when interacting with the UI
if "results" not in st.session_state:
    st.session_state.results = []
if "status" not in st.session_state:
    st.session_state.status = None
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "count" not in st.session_state:
    st.session_state.count = 0

# ==========================================
# API CALL HANDLER
# ==========================================
def fetch_screener_results(user_query: str) -> None:
    """Sends query to FastAPI backend and stores response in session state."""
    
    # Duplicate click protection
    if st.session_state.is_loading:
        return
        
    st.session_state.is_loading = True
    
    try:
        response = requests.post(
            API_URL, 
            json={"query": user_query},
            timeout=10 # Prevent hanging indefinitely
        )
        
        # Check if the server crashed or endpoint is wrong
        if response.status_code != 200:
            st.error(f"Server Error {response.status_code}: Could not connect to backend.")
            st.session_state.status = "error"
            st.session_state.is_loading = False
            return
            
        data: Dict[str, Any] = response.json()
        
        # Validate that the expected JSON structure exists
        if "status" not in data or "results" not in data:
            st.error("Invalid response format received from API.")
            st.session_state.status = "error"
            st.session_state.is_loading = False
            return
            
        # Update session state with successful data
        st.session_state.status = data.get("status")
        st.session_state.results = data.get("results", [])
        st.session_state.count = data.get("count", 0)
        
        # Display the custom message if the backend reported an internal error
        if st.session_state.status == "error":
            st.error(data.get("message", "An unknown error occurred."))
            
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Is the FastAPI backend running on port 8000?")
        st.session_state.status = "error"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.session_state.status = "error"
    finally:
        st.session_state.is_loading = False

# ==========================================
# UI RENDERING
# ==========================================
st.title("📈 AI Stock Screener")
st.markdown("Enter a natural language query to filter global equities.")

with st.form("query_form"):
    user_input = st.text_input("Search", placeholder='e.g., "show me tech stocks with PE ratio less than 15"')
    
    # Disable button if a request is already running
    submitted = st.form_submit_button("Search", disabled=st.session_state.is_loading)

if submitted:
    if not user_input.strip():
        st.warning("Please enter a valid query before searching.")
    else:
        with st.spinner("Processing AI Request..."):
            fetch_screener_results(user_input)

# Display Results from Session State
if st.session_state.status == "success":
    st.success(f"Successfully retrieved {st.session_state.count} results!")
    
    if st.session_state.count > 0:
        # Render clean dataframe
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No companies matched your criteria.")
