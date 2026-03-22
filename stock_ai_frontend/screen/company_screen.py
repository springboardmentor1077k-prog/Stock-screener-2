import streamlit as st

st.title("Company Details")

company = st.text_input("Enter company name")

if st.button("Get Details"):

    st.write("Company financial data will appear here")
