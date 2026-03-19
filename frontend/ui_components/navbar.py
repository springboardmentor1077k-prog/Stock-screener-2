import streamlit as st

def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.query_params.clear()
        st.switch_page("login.py")