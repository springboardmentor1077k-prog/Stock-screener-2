import streamlit as st
import yfinance as yf
# import json
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
            e_growth = info.get("earningsGrowth", None)
            peg = None
            
            
            #the peg ratio is nothing but (PE/earning_growth)
            if pe and e_growth and e_growth != 0:
                peg = pe / (e_growth * 100)
            
            
            sector = info.get("sector", "N/A")
            promoter_holding = 50.00  # default for now
            
            
            st.subheader("Stock Details")
            st.write("Company Name:", company_name)
            st.write("Current Price:", current_price)
            st.write("PE Ratio:", pe)
            st.write("PEG Ratio:", peg)
            st.write("Sector:", sector)
            
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # insert the data into symbol table
            
            cursor.execute("""
                INSERT INTO symbol (company_name, company_symbol, sector)
                VALUES (%s, %s, %s)
                ON CONFLICT (company_symbol) DO NOTHING
                RETURNING symbol_id;
            """, (company_name, stock.upper(), sector))
            
            
            result = cursor.fetchone()
            
            
            if result:
                symbol_id = result[0]
            else:
                cursor.execute(
                    "SELECT symbol_id FROM symbol WHERE company_symbol = %s",
                    (stock.upper(),)
                )
                symbol_id = cursor.fetchone()[0]
                
        # insert the data into fundamental table
                
            cursor.execute("""
                INSERT INTO fundamentals
                (symbol_id, pe, peg, promoter_holding)
                VALUES (%s, %s, %s, %s);
            """, (symbol_id, pe, peg, promoter_holding))

            conn.commit()
            cursor.close()
            conn.close()
            
            st.success("Data stored successfully")
            
            
            
        except Exception as e:
            st.error("Invalid symbol or data not available")
            st.write(e)