import streamlit as st

def set_results(results):
    st.session_state["results"] = results

def get_results():
    return st.session_state.get("results", None)
