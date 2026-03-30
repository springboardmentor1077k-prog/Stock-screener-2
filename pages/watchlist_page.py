import streamlit as st
from app.watchlist import add_to_watchlist, get_watchlist

def watchlist_page():
    st.title("⭐ Watchlist")

    symbol = st.text_input("Stock Symbol", key="watchlist_symbol")

    if st.button("Add to Watchlist", key="watchlist_btn"):
        if symbol:
            add_to_watchlist(symbol)
            st.success("Added to Watchlist!")
        else:
            st.warning("Enter stock symbol")

    data = get_watchlist()

    if data:
        st.write("### Your Watchlist")
        st.write(data)
    else:
        st.info("No watchlist data yet")