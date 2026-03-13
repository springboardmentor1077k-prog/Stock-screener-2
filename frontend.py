import streamlit as st
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="AI Stock Screener", layout="centered")

st.title("AI Stock Screener")

# State management initialization
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

def set_query(text):
    st.session_state.query_text = text

# 1. Query Input Box
query = st.text_input("Enter your query (e.g. Show me IT stocks)", value=st.session_state.query_text)

# 2. Suggested Queries
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
        with st.spinner("⏳ Processing your request... Please wait."):
            try:
                # Backend API Call
                response = requests.post("http://localhost:8000/query", json={"query": query})
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("data", data.get("results", []))
                    
                    if results:
                        st.success("✅ Results fetched successfully")
                        st.session_state.results_df = pd.DataFrame(results)
                    else:
                        st.session_state.results_df = pd.DataFrame()
                        st.info("No matching stocks found.")
                else:
                    st.error(f"❌ Error: {response.json().get('message', 'Unable to interpret your query')}")
            except Exception as e:
                st.error("❌ Failed to connect to backend. Is FastAPI running?")
    else:
        st.warning("Please enter a query first.")

# ---------------------------------------------------------
# NEW FEATURES: Sorting & Statistical Summary
# ---------------------------------------------------------
df = st.session_state.results_df

if not df.empty:
    st.markdown("---")
    st.subheader("📊 Search Results")
    
    # Sorting Options
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_column = st.selectbox("Sort By Column:", options=df.columns.tolist())
    with sort_col2:
        sort_order = st.radio("Sorting Order:", ["Ascending", "Descending"], horizontal=True)
    
    # Apply Sorting
    is_ascending = True if sort_order == "Ascending" else False
    sorted_df = df.sort_values(by=sort_column, ascending=is_ascending)
    
    # Display Main Table
    st.dataframe(sorted_df, use_container_width=True)
    
    # Statistical Summary (Expandable to keep UI clean)
    with st.expander("📈 View Statistical Summary"):
        st.write("Here is the statistical summary of the fetched results:")
        # describe() function automatic ga mean, min, max, count anni isthundi
        st.dataframe(sorted_df.describe(), use_container_width=True)