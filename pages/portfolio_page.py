import streamlit as st
from app.portfolio import add_to_portfolio, get_portfolio

def portfolio_page():
    st.title("📁 Portfolio")

    symbol = st.text_input("Stock Symbol", key="portfolio_symbol")
    shares = st.number_input("Shares", min_value=1, key="portfolio_shares")

    if st.button("Add to Portfolio", key="portfolio_btn"):
        if symbol:
            add_to_portfolio(symbol, shares)
            st.success("Added to Portfolio!")
        else:
            st.warning("Enter stock symbol")

    data = get_portfolio()

    if data:
        st.write("### Your Portfolio")
        st.write(data)
    else:
        st.info("No portfolio data yet")