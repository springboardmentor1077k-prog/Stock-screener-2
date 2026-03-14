import streamlit as st

company_name = st.session_state.get("selected_company")

if not company_name:
    st.error("No company selected.")
    st.stop()

st.title(f"Company Details: {company_name}")