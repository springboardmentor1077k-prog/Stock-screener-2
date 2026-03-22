import streamlit as st
from state import get_results

def show_result_screen():
    st.title("📈 Results")

    results = get_results()

    # DEBUG (you can remove later)
    st.write("Stored Results:", results)

    if results:
        st.table(results)
    else:
        st.warning("No results found. Please run a query first.")