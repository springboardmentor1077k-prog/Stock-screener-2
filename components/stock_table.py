import streamlit as st
import pandas as pd

def show_table(results):

    if not results:
        st.warning("No results found")
        return

    df = pd.DataFrame(results, columns=[
        "id", "symbol", "name", "sector",
        "pe_ratio", "market_cap", "price", "volume"
    ])

    st.dataframe(df, use_container_width=True)