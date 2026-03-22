
import streamlit as st
from screen.query_screen import show_query_screen
from screen.result_screen import show_result_screen

st.set_page_config(page_title="Stock Screener", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Query", "Results"])

if page == "Query":
    show_query_screen()

elif page == "Results":
    show_result_screen()
