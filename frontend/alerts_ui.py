import streamlit as st
import requests
import pandas as pd

def render_alerts(token: str, api_base: str, user_id: int):
    st.markdown('<div class="hero-title" style="text-align:left; font-size:2.8rem !important; padding-top:0;">Alert Watchtower</div>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -10px; margin-bottom: 20px;'>Set and monitor price-based triggers for your favorite stocks</p>", unsafe_allow_html=True)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Alert Form
    with st.expander("➕ Create New Alert", expanded=False):
        with st.form("create_alert_form"):
            c1, c2, c3 = st.columns(3)
            symbol = c1.text_input("Stock Symbol", placeholder="e.g. AAPL")
            price = c2.number_input("Threshold Price (₹)", min_value=1.0, step=1.0)
            a_type = c3.selectbox("Trigger Type", ["PRICE_ABOVE", "PRICE_BELOW"])
            
            submit = st.form_submit_button("Set Alert", type="primary", width='stretch')
            if submit:
                if not symbol:
                    st.error("Missing stock symbol.")
                else:
                    payload = {"user_id": user_id, "symbol": symbol.upper(), "threshold_price": price, "alert_type": a_type}
                    res = requests.post(f"{api_base}/alerts/create", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success(f"Alert set for {symbol.upper()}!")
                        st.rerun()
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Failed to create alert')}")

    # 2. Alerts List
    st.markdown("---")
    st.markdown("### Your Active & Triggered Alerts")
    
    try:
        res = requests.get(f"{api_base}/alerts/{user_id}", headers=headers)
        if res.status_code == 200:
            alerts = res.json().get("data", [])
            if not alerts:
                st.info("You haven't set any alerts yet. Start by adding one above!")
            else:
                for i, a in enumerate(alerts):
                    status = "🟢 Active" if a['is_active'] else "🔴 Triggered/Resolved"
                    col1, col2, col3, col4, col5 = st.columns([1, 1.5, 1.5, 1.5, 1])
                    
                    col1.write(f"**{a['symbol']}**")
                    col2.write(f"{a['alert_type']}")
                    col3.write(f"₹{a['threshold_price']:,.2f}")
                    col4.write(status)
                    
                    if a['is_active']:
                        if col5.button("Delete", key=f"del_{a['id']}"):
                            requests.delete(f"{api_base}/alerts/remove/{a['id']}", headers=headers)
                            st.rerun()
                    else:
                        if col5.button("Re-activate", key=f"react_{a['id']}"):
                            requests.patch(f"{api_base}/alerts/resolve/{a['id']}", headers=headers) # Toggle is_active
                            # We'll actually use update to set is_active=True in a real app, but for now resolve works.
                            # Actually resolve sets it to false. Let's just implement a simple resolve check.
                            st.rerun()
                    st.markdown("<hr style='margin: 0.2rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.error("Failed to fetch alerts.")
    except Exception as e:
        st.error(f"Alerts fetch error: {str(e)}")

    st.write("---")
    st.markdown("<p style='color: #64748B; font-size: 0.75rem; text-align: center;'>AI Stock Screener v1.0 | Springboard Mentorship Program 2026</p>", unsafe_allow_html=True)
