import streamlit as st

def init_state():
    if "results" not in st.session_state:
        st.session_state["results"] = None

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []

    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = []

    if "alerts" not in st.session_state:
        st.session_state["alerts"] = []

# -------- RESULTS --------
def set_results(results):
    st.session_state["results"] = results

def get_results():
    return st.session_state.get("results", None)

# -------- WATCHLIST --------
def add_to_watchlist(company):
    if company not in st.session_state["watchlist"]:
        st.session_state["watchlist"].append(company)

def get_watchlist():
    return st.session_state["watchlist"]

# -------- PORTFOLIO --------
def add_to_portfolio(company, quantity, price):
    st.session_state["portfolio"].append({
        "company_name": company,
        "quantity": quantity,
        "buy_price": price
    })

def get_portfolio():
    return st.session_state["portfolio"]

# ✏️ UPDATE HOLDING
def update_portfolio(index, quantity, price):
    st.session_state["portfolio"][index]["quantity"] = quantity
    st.session_state["portfolio"][index]["buy_price"] = price

# ❌ DELETE HOLDING
def delete_portfolio(index):
    st.session_state["portfolio"].pop(index)

# -------- ALERTS --------
def add_alert(alert):
    st.session_state["alerts"].append(alert)

def get_alerts():
    return st.session_state["alerts"]
