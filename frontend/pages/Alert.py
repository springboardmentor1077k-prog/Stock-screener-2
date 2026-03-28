import streamlit as st
import requests
from ui_components.navbar import logout_button
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)



token = st.session_state.get("token")

if not token:
    st.error("Please login")
    st.stop()

headers = {
    "Authorization": f"Bearer {token}"
}

st.title("Alerts")




try:
    res = requests.get(
        "http://127.0.0.1:7000/check-alerts",    
        headers=headers,
        timeout=5
    )

    if res.status_code == 200:
        data = res.json()

        triggered = data.get("triggered", [])

        if triggered:
            for alert in triggered:
                companies = ", ".join(alert["companies"])

                st.success(
                    f"Alert conditions are met.\n\n"
                    f"Companies: {companies}"
                )

                st.toast(f"Alert triggered for {companies}")

        else:
            st.success("All good! No alerts triggered right now.")

    elif res.status_code == 401:
        st.warning("Session expired. Please login again.")

    else:
        st.info("Alerts are not available right now. Please try again later.")

except requests.exceptions.ConnectionError:
    st.info("Unable to connect to server. Please check backend is running.")

except requests.exceptions.Timeout:
    st.info("Server is taking too long. Try again in a moment.")

except Exception as e:
    logger.error(f"Backend error: {str(e)}")
    st.error("Something went wrong. Please try again.")



# CREATE ALERT (NL INPUT)

st.markdown("---")
st.subheader("Create Alert")

query = st.text_input(
    "Enter alert condition",
    placeholder="e.g. pe < 15 AND peg > 1"
)

if st.button("Create Alert"):
    if not query.strip():
        st.warning("Please enter a valid condition")

    else:
        try:
            res = requests.post(
                "http://127.0.0.1:7000/add-alert",
                json={"query": query},
                headers=headers,
                timeout=5
            )

            if res.status_code == 200:
                st.success("Alert created successfully")
                st.rerun()

            elif res.status_code == 400:
                logger.warning(f"{res.json().get('detail', 'Invalid query format')}")
                st.warning("Try with a proper format")

            else:
                
                st.error("Failed to create alert. Please try again.")

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to server. Is backend running")
            st.error("Internal server error")

        except requests.exceptions.Timeout:
            
            st.error("Server is taking too long...... Try again")

        except Exception as e:
            logger.error("Unexpected error occurred"+ str(e))
            st.error("Try again")
          


# VIEW ALERTS

st.markdown("---")
st.subheader("Your Alerts")

try:
    res = requests.get("http://127.0.0.1:7000/get-alerts")

    if res.status_code == 200:
        alerts = res.json().get("data", [])

        if not alerts:
            st.info("No alerts created yet")

        else:
            for alert in alerts:

                cond_text = " AND ".join(
                    [
                        f"{c['metric'].upper()} {c['operator']} {c['value']}"
                        for c in alert["conditions"]
                    ]
                )

                if alert["company_name"]:
                    cond_text = f"{alert['company_name']} {cond_text}"

                col1, col2 = st.columns([6, 1])

                with col1:
                    st.write(cond_text)

                with col2:
                    if st.button("Delete", key=f"del_{alert['id']}"):
                        
                        try:
                            res = requests.delete(
                            f"http://127.0.0.1:7000/delete-alert/{alert['id']}")

                            if res.status_code == 200:
                                logger.info(f"Deleted alert {alert['id']}")
                                st.success("Deleted successfully")
                                st.rerun()
                            else:
                                logger.warning(f"Delete failed: {res.text}")
                                st.error("Delete failed")

                        except Exception as e:
                            logger.error(f"Delete API error: {str(e)}")
                            st.error("Unable to connect to server")
                            




except Exception as e:
    logger.error(f"Fetch alerts error: {str(e)}")
    st.warning("Unable to load alerts")
    
logout_button()