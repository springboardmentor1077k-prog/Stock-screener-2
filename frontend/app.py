import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/v1/query"

# Page config
st.set_page_config(
    page_title="AI Stock Screener",
    page_icon="📈",
    layout="wide"
)

# Initialize session state variables
if 'previous_results' not in st.session_state:
    st.session_state.previous_results = None
    
if 'previous_query' not in st.session_state:
    st.session_state.previous_query = ""
    
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
    
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
    
if 'results_per_page' not in st.session_state:
    st.session_state.results_per_page = 10

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .history-item {
        padding: 0.5rem;
        border-radius: 0.25rem;
        background-color: #f8f9fa;
        margin: 0.25rem 0;
        cursor: pointer;
        border-left: 3px solid #007bff;
    }
    .history-item:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
with col2:
    st.title("AI Stock Screener")
    st.markdown("*Natural language search for stock market data*")

# Sidebar for history and settings
with st.sidebar:
    st.header("📜 Search History")
    
    if st.session_state.search_history:
        for i, history_item in enumerate(reversed(st.session_state.search_history[-5:])):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"🔍 {history_item['query'][:30]}...", key=f"hist_{i}"):
                    st.session_state.previous_query = history_item['query']
                    st.session_state.previous_results = history_item['results']
                    st.rerun()
            with col2:
                st.caption(f"{history_item['count']} results")
        st.divider()
    else:
        st.info("No search history yet")
    
    st.header("⚙️ Settings")
    st.session_state.results_per_page = st.slider(
        "Results per page", 
        min_value=5, 
        max_value=50, 
        value=st.session_state.results_per_page,
        step=5
    )
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.search_history = []
        st.session_state.previous_results = None
        st.session_state.previous_query = ""
        st.rerun()

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    # Query input with previous query preserved
    query = st.text_input(
        "🔍 Enter your query:",
        value=st.session_state.previous_query,
        placeholder="e.g., IT companies with PE ratio less than 20",
        key="query_input"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    submit_button = st.button("🚀 Search", type="primary", use_container_width=True)

# Suggestions
with st.expander("💡 Example Queries", expanded=True):
    suggestions = [
        "IT companies with PE ratio below 20",
        "Companies with PEG ratio less than 1",
        "Companies with promoter holding above 50",
        "Stocks with debt to FCF less than 0.5",
        "Companies with revenue greater than 10000"
    ]
    
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(f"📌 {suggestion}", key=f"sugg_{i}", use_container_width=True):
                st.session_state.previous_query = suggestion
                st.rerun()

# Display previous results if they exist and no new search is triggered
if st.session_state.previous_results is not None and not submit_button:
    results = st.session_state.previous_results
    current_query = st.session_state.previous_query
    
    st.success(f"📊 Showing previous results for: **{current_query}**")
    
    # Display results
    if len(results) == 0:
        st.warning("No results found")
    else:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Results", len(results))
        with col2:
            st.metric("Current Page", st.session_state.current_page)
        with col3:
            st.metric("Results/Page", st.session_state.results_per_page)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Pagination
        start_idx = (st.session_state.current_page - 1) * st.session_state.results_per_page
        end_idx = start_idx + st.session_state.results_per_page
        paginated_df = df.iloc[start_idx:end_idx]
        
        # Display table
        st.dataframe(
            paginated_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Pagination controls
        total_pages = (len(results) + st.session_state.results_per_page - 1) // st.session_state.results_per_page
        
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("◀ First", disabled=st.session_state.current_page == 1):
                    st.session_state.current_page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀ Prev", disabled=st.session_state.current_page == 1):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col3:
                st.write(f"Page {st.session_state.current_page} of {total_pages}")
            
            with col4:
                if st.button("Next ▶", disabled=st.session_state.current_page == total_pages):
                    st.session_state.current_page += 1
                    st.rerun()
            
            with col5:
                if st.button("Last ▶", disabled=st.session_state.current_page == total_pages):
                    st.session_state.current_page = total_pages
                    st.rerun()

# Handle new search
if submit_button and query:
    with st.spinner("🤖 AI is analyzing your query..."):
        try:
            response = requests.post(
                API_URL,
                json={
                    "query": query,
                    "limit": 50  # Fetch more for pagination
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "success":
                    results = data["data"]
                    
                    # Save to session state
                    st.session_state.previous_results = results
                    st.session_state.previous_query = query
                    st.session_state.current_page = 1
                    
                    # Add to history
                    st.session_state.search_history.append({
                        "query": query,
                        "count": len(results),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "results": results
                    })
                    
                    st.rerun()  # Rerun to show results with proper state
                
                else:
                    st.error(f"❌ Server error: {data.get('message', 'Unknown error')}")
            else:
                st.error(f"❌ API Error: Status code {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure FastAPI is running on http://127.0.0.1:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.caption("🔄 State is preserved across interactions. Results persist until you perform a new search.")