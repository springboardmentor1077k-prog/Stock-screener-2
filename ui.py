import streamlit as st
from app.llm import nl_to_dsl
from app.dsl_validator import validate_dsl
from app.query_builder import build_query
from app.execution_engine import execute_query

from components.navbar import render_navbar
from pages.results import show_results
from pages.portfolio_page import portfolio_page
from pages.watchlist_page import watchlist_page
from pages.alerts_page import alerts_page


def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def run_ui():

    # 🔥 LOAD CSS
    load_css()

    # 🔥 NAVBAR
    render_navbar()

    # 🔥 SIDEBAR NAVIGATION
    page = st.sidebar.selectbox(
        "Select Page",
        ["Screener", "Portfolio", "Watchlist", "Alerts"]
    )

    # 🟢 SCREENER PAGE
    if page == "Screener":

        st.markdown("<h1>📊 AI Stock Screener</h1>", unsafe_allow_html=True)

        st.markdown("### 🔍 Enter your query")
        query = st.text_input("")

        if st.button("Run Screener"):
            try:
                dsl = nl_to_dsl(query)

                validate_dsl(dsl)

                sql, values = build_query(dsl)

                results = execute_query(sql, values)

                show_results(results)

            except Exception as e:
                st.error(str(e))

    # 🟢 PORTFOLIO PAGE
    elif page == "Portfolio":
        portfolio_page()

    # 🟢 WATCHLIST PAGE
    elif page == "Watchlist":
        watchlist_page()

    # 🟢 ALERTS PAGE
    elif page == "Alerts":
        alerts_page()