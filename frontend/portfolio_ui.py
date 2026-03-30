import streamlit as st
import pandas as pd
import requests

def render_portfolio(token: str, api_base: str):
    st.markdown('<div class="hero-title" style="text-align:left; font-size:2.8rem !important; padding-top:0;">Analytics Portfolio</div>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -10px; margin-bottom: 30px;'>Track your holdings and dynamically execute trades with real-time P&L.</p>", unsafe_allow_html=True)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{api_base}/portfolio/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        summary = data["summary"]
        
        # Summary Section
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Invested", f"₹{summary['total_invested']:,.2f}")
        col2.metric("Current Value", f"₹{summary['total_current_value']:,.2f}")
        
        c = "normal" if summary['total_pnl'] >= 0 else "inverse"
        col3.metric("Unrealized P&L", f"₹{summary['total_pnl']:,.2f}", delta_color=c)
        col4.metric("Growth %", f"{summary['total_pct_change']}%", delta=f"{summary['total_pct_change']}%", delta_color=c)

        st.markdown("---")
        
        # Holdings Table
        if data["holdings"]:
            df = pd.DataFrame(data["holdings"])
            
            def colorize(val):
                color = '#10B981' if val > 0 else '#EF4444' if val < 0 else 'white'
                return f'color: {color}'
            
            styled = df.style.map(colorize, subset=['pnl', 'pct_change'])
            st.dataframe(styled, width='stretch', hide_index=True)
        else:
            st.info("Your portfolio is empty. Execute a trade below to start.")
            
        # Trade Form
        st.markdown("### ⚡ Add / Update / Remove")
        with st.form("trade_form"):
            c1, c2, c3, c4 = st.columns(4)
            symbol = c1.text_input("Symbol")
            act = c2.selectbox("Action", ["BUY", "SELL"])
            qty = c3.number_input("Qty", min_value=1)
            pr = c4.number_input("Price (₹)", min_value=1.0)
            
            if st.form_submit_button("Execute Ledger Action", type="primary", width='stretch'):
                rq = requests.post(f"{api_base}/portfolio/trade?action_type={act}", json={"symbol": symbol, "quantity": qty, "price": pr}, headers=headers)
                if rq.status_code == 200:
                    st.success("Trade Recorded and Averaged Correctly!")
                    st.rerun()
                else:
                    st.error(rq.json().get("detail", "Trade Failed"))
    else:
        st.error("Failed to fetch portfolio data. Is the backend running?")
