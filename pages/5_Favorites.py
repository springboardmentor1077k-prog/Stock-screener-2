import streamlit as st

st.title("Favorite Stocks")

if "favorites" not in st.session_state:
    st.session_state.favorites = []

st.write(st.session_state.favorites)