import streamlit as st
from ui_components.navbar import logout_button

logout_button()

company_name = st.session_state.get("selected_company")

if not company_name:
    st.error("No company selected.")
    st.stop()

st.title(f"Company Details: {company_name}")