import streamlit as st
import yfinance as yf
import json
import psycopg2 as ps





def get_connection():
    return ps.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )



       



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
            
            company_name = info.get("longName", "N/A")
            current_price = info.get("currentPrice", None)
            pe = info.get("trailingPE", None)
            peg = info.get("pegRatio", None)
            sector = info.get("sector", "N/A")
            
           
            
            
            
        except Exception as e:
            st.error("Invalid symbol or data not available")
            st.write(e)