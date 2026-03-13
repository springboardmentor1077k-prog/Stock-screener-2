import streamlit as st
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="AI Stock Screener", layout="centered")

st.title("AI Stock Screener")

# State management for suggested queries
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

def set_query(text):
    st.session_state.query_text = text

# 1. Query Input Box
query = st.text_input("Enter your query (e.g. Show me IT stocks)", value=st.session_state.query_text)

# 2. Suggested Queries (Buttons)
st.write("**Suggested Queries:**")
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("PE < 15"):
        set_query("Show companies with pe_ratio < 15")
        st.rerun()
with col2:
    if st.button("Market Cap > 50K"):
        set_query("Show companies with market_cap > 50000")
        st.rerun()

# 3. Search / Run Button
if st.button("Search / Run", type="primary"):
    if query:
        # 4. Loading State
        with st.spinner("⏳ Loading results..."):
            try:
                # 5. Connect to your FastAPI backend
                response = requests.post("http://localhost:8000/query", json={"query": query})
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Results fetched successfully")
                    
                    # 6. Results Table
                    results = data.get("data", data.get("results", []))
                    if results:
                        # Converting JSON to a neat Table using Pandas
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No matching stocks found.")
                else:
                    st.error(f"❌ Error: {response.json().get('message', 'Invalid query')}")
            except Exception as e:
                st.error("❌ Failed to connect to backend. Is FastAPI running?")
    else:
        st.warning("Please enter a query first.")