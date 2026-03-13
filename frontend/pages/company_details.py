import streamlit as st

st.title("Company details")

company_symbol = st.session_state.get("selected_company")

if not company_symbol:
    st.error("No company selected.")
    st.stop()

st.title(f"Company Details: {company_symbol}")