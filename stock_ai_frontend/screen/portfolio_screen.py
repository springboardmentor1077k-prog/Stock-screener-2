import streamlit as st

st.title("Portfolio")

st.write("Track your investments here")

company = st.text_input("Add company to portfolio")

if st.button("Add"):

    st.success(f"{company} added to portfolio")
