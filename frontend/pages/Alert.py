import streamlit as st
import requests
from ui_components.navbar import logout_button
import logging
from ui_components.footer import header

header()


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



# CREATE ALERT

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
                "http://127.0.0.1:7000/alerts/add-alert",
                json={"query": query},
                headers=headers,
                timeout=5
            )
            
            st.write(res.json())

            if res.status_code == 200:
                st.success("Alert created successfully")
                st.rerun()

            elif res.status_code == 400:
                st.warning("Try with a proper format")

            else:
                st.error("Failed to create alert")

        except Exception as e:
            logger.error(str(e))
            st.error("Server error")



# VIEW ALERTS

st.markdown("---")
st.subheader("Your Alerts")

try:
   
    res = requests.get(
        "http://127.0.0.1:7000/alerts/get-alerts",
        headers=headers,
        timeout=5
    )

    if res.status_code == 200:
        alerts = res.json().get("data", [])

        if not alerts:
            st.info("No alerts created yet")

        else:
         
            status_map = {}

            try:
                res_status = requests.get(
                    "http://127.0.0.1:7000/alerts/check-alerts",
                    headers=headers,
                    timeout=5
                )

                if res_status.status_code == 200:
                    status_data = res_status.json().get("alerts", [])

                    for s in status_data:
                        status_map[s["alert_id"]] = {
                            "triggered": s["triggered"],
                            "companies": s["companies"]
                        }

            except Exception as e:
                logger.error(f"Status fetch failed: {str(e)}")

            # 🔹 DISPLAY ALERTS
            for idx, alert in enumerate(alerts, start=1):

                cond_text = " AND ".join(
                    [
                        f"{c['field'].upper()} {c['operator']} {c['value']}"
                        for c in alert["conditions"]
                    ]
                )

                if alert["company_name"]:
                    cond_text = f"{alert['company_name']} {cond_text}"

                alert_status = status_map.get(alert["alert_id"], {})
                is_triggered = alert_status.get("triggered", False)
                companies = ", ".join(
                    [c["name"] for c in alert_status.get("companies", [])]
                )

                col1, col2 = st.columns([6, 1])

                with col1:
                    if is_triggered:
                        st.success(f"✅ {idx}. {cond_text}")

                        
                        st.toast(f" Alert {idx} triggered -> {companies}")

                    else:
                        st.markdown(f"⚪ {idx}. {cond_text}")

                with col2:
                    if st.button("Delete", key=f"del_{alert['id']}"):
                        try:
                            res = requests.delete(
                                f"http://127.0.0.1:7000/alerts/delete-alert/{alert['id']}",
                                headers=headers
                            )

                            if res.status_code == 200:
                                st.success("Deleted successfully")
                                st.rerun()
                            else:
                                st.error("Delete failed")

                        except Exception as e:
                            logger.error(str(e))
                            st.error("Server error")

    else:
        st.warning("Failed to fetch alerts")

except Exception as e:
    logger.error(str(e))
    st.warning("Unable to load alerts")


logout_button()
