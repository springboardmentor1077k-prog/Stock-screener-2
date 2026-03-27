import streamlit as st
import requests
import pandas as pd

def show_alerts():
    # ❌ DON'T use st.title here
    st.subheader("🔔 Alerts")

    try:
        response = requests.get("http://127.0.0.1:8000/alerts/")

        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])

            if alerts:
                df = pd.DataFrame(alerts)

                # ✅ Better UI layout
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.dataframe(df, use_container_width=True)

                with col2:
                    st.metric("Total Alerts", len(df))

            else:
                st.info("No alerts available")

        else:
            st.error(f"API Error: {response.status_code}")

    except Exception as e:
        st.error(f"Error: {e}")