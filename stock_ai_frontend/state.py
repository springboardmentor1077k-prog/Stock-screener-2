import streamlit as st

def initialize_state():

    if "query" not in st.session_state:
        st.session_state["query"] = ""

    if "results" not in st.session_state:
        st.session_state["results"] = None

    if "selected_company" not in st.session_state:
        st.session_state["selected_company"] = None

    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = []

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []
