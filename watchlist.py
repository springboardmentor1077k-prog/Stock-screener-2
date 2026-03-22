import streamlit as st

st.title("Watchlist")

company = st.text_input("Add company to watchlist")

if st.button("Add to Watchlist"):

    st.success(f"{company} added to watchlist")