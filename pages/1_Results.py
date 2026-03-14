import streamlit as st

st.title("Results")

# Check if results exist
if "result_state" not in st.session_state or st.session_state.result_state is None:
    st.warning("No results available. Please run a search first.")
    st.stop()

results = st.session_state.result_state.get("data", [])

if len(results) == 0:
    st.info("No results found")
else:
    st.dataframe(results)