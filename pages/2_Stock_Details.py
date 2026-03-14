import streamlit as st

st.title("Stock Details")

if "selected_item_state" not in st.session_state:
    st.info("No stock selected")
else:
    stock = st.session_state.selected_item_state
    st.json(stock)