import streamlit as st
from app.alerts import add_alert, get_alerts

def alerts_page():
    st.title("🚨 Alerts")

    symbol = st.text_input("Stock Symbol", key="alert_symbol")
    condition = st.selectbox("Condition", ["<", ">"], key="alert_condition")
    threshold = st.number_input("Value", key="alert_value")

    if st.button("Add Alert", key="alert_btn"):
        if symbol:
            add_alert(symbol, condition, threshold)
            st.success("Alert added!")
        else:
            st.warning("Enter stock symbol")

    data = get_alerts()

    if data:
        st.write("### Your Alerts")
        st.write(data)
    else:
        st.info("No alerts yet")