import streamlit as st

st.title("Stock Alerts")

company = st.text_input("Company")

condition = st.text_input("Alert Condition")

if st.button("Create Alert"):

    st.success("Alert created successfully")
