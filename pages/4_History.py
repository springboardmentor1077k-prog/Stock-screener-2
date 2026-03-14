import streamlit as st

st.title("Query History")

if "query_history" not in st.session_state:
    st.session_state.query_history = []

for q in st.session_state.query_history:
    st.write(q)