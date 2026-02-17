import streamlit as st
import yfinance as yf

st.title("AI POWERED STOCK SCREENER AND ADVISOR")

st.write("The data available is of 1day with a time interval of 5 min")

stock = st.text_input("Enter Stock Symbol (Example:INFY)")
if st.button("Click"):

    if stock == "":
        st.warning("Please enter a stock symbol")
    else:
        try:
            ticker = yf.Ticker(stock.upper())
            
            info = ticker.info
            hist = ticker.history(period="1d", interval="5m")

            st.subheader("Stock Details")
            st.write("Company Name:", info.get("longName", "N/A"))
            st.write("Current Price:", info.get("currentPrice", "N/A"))
            st.write("PE Ratio:", info.get("trailingPE", "N/A"))
        except Exception as e:
            st.error("Invalid symbol or data not available")
            st.write(e)