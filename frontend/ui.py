import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Advanced AI Screener", layout="wide")

if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- SIDEBAR (AUTHENTICATION) ---
with st.sidebar:
    st.title("🔐 Secure Login")
    
    if st.session_state['token'] is None:
        st.write("Please log in to access the Advanced AI.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                res = requests.post(f"{API_BASE}/login", json={"username": username, "password": password})
                if res.status_code == 200:
                    st.session_state['token'] = res.json().get("access_token")
                    st.session_state['user'] = username
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Login Failed"))
        
        with col2:
            if st.button("Register"):
                res = requests.post(f"{API_BASE}/register", json={"username": username, "password": password})
                if res.status_code == 200:
                    st.success("Registered! Now Login.")
                else:
                    st.error(res.json().get("detail", "Registration Failed"))
    else:
        st.success(f"Logged in as: {st.session_state['user']}")
        if st.button("Logout"):
            st.session_state['token'] = None
            st.session_state['user'] = None
            st.rerun()

# --- TOP LEVEL UI ---
st.title("🤖 Enterprise AI Stock Screener")
st.markdown("This application converts requests into strict JSON DSL, compiled via Parameterized SQL for absolute security.")

# --- MAIN SCREENER CORE ---
if st.session_state['token'] is None:
    st.warning("You must securely log in via the sidebar to access the terminal.")
else:
    st.write("### Natural Language Query Interface")
    user_query = st.text_input("Enter your command:", placeholder="e.g. Show companies with PE ratio < 15 and revenue > 1000")
    
    if st.button("Search Database", type="primary"):
        if not user_query:
            st.warning("Please enter a query!")
        else:
            with st.spinner("Parsing Language → DSL → Validating → Parameterized SQL → Redis Cache..."):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(f"{API_BASE}/ask_ai", json={"query": user_query}, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("🧠 Pipeline Executed! Passed strict DSL validation.")
                    
                    if "data" in data and len(data["data"]) > 0:
                        df = pd.DataFrame(data["data"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Query successfully ran, but no companies matched this criteria (or the database is completely empty!).")
                    
                    with st.expander("🛠️ See Background Work (Compiler Output)", expanded=False):
                        st.json(data)
                        
                elif response.status_code == 401:
                    st.error("Authentication expired or invalid. Please re-login.")
                else:
                    try:
                        st.error(f"Error {response.status_code}: {response.json().get('detail')}")
                    except:
                        st.error(f"Error {response.status_code}: {response.text}")
