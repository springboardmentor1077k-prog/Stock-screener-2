import streamlit as st

def show_cards(results):

    for r in results:
        st.markdown(f"""
        ### {r[2]} ({r[1]})
        - PE Ratio: {r[4]}
        - Price: {r[6]}
        - Market Cap: {r[5]}
        """)