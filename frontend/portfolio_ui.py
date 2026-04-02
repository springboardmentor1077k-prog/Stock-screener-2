import streamlit as st
import pandas as pd
import requests
import datetime

def init_session_state(user_id):
    if "portfolio_user_id" not in st.session_state or st.session_state.portfolio_user_id != user_id:
        st.session_state.portfolio_user_id = user_id
        st.session_state.portfolio_summary = None
        st.session_state.portfolio_holdings = None
        st.session_state.portfolio_last_refresh = None
        st.session_state.portfolio_edit_symbol = None
        st.session_state.portfolio_remove_symbol = None

def fetch_data(token: str, api_base: str, user_id: int):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        summary_res = requests.get(f"{api_base}/portfolio/{user_id}/summary", headers=headers, timeout=10)
        holdings_res = requests.get(f"{api_base}/portfolio/{user_id}", headers=headers, timeout=10)
        
        if summary_res.status_code == 200 and holdings_res.status_code == 200:
            st.session_state.portfolio_summary = summary_res.json()
            st.session_state.portfolio_holdings = holdings_res.json()
            st.session_state.portfolio_last_refresh = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True, ""
        else:
            return False, f"API Error: Summary {summary_res.status_code}, Holdings {holdings_res.status_code}"
    except Exception as e:
        return False, str(e)

def render_portfolio(token: str, api_base: str, user_id: int):
    init_session_state(user_id)
    
    # Section 1: Page Header
    st.markdown('<div class="hero-title" style="text-align:left; font-size:2.8rem !important; padding-top:0;">My Portfolio</div>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -10px; margin-bottom: 20px;'>Track your holdings and monitor your profits and losses in real time</p>", unsafe_allow_html=True)
    
    col_timestamp, col_refresh = st.columns([4, 1])
    with col_timestamp:
        if st.session_state.portfolio_last_refresh:
            st.caption(f"Last Refreshed: {st.session_state.portfolio_last_refresh}")
    with col_refresh:
        if st.button("🔄 Refresh Data", width='stretch'):
            with st.spinner("Refreshing data..."):
                try:
                    requests.post(f"{api_base}/portfolio/cache/clear", headers={"Authorization": f"Bearer {token}"})
                except:
                    pass
                st.session_state.portfolio_edit_symbol = None
                st.session_state.portfolio_remove_symbol = None
                success, err = fetch_data(token, api_base, user_id)
                if success:
                    st.success("Refreshed successfully!")
                else:
                    st.error(f"Failed to refresh: {err}")
    
    # Initial data fetch
    if st.session_state.portfolio_summary is None:
        with st.spinner("Fetching portfolio data..."):
            success, err = fetch_data(token, api_base, user_id)
            if not success:
                st.error(f"Error fetching data: {err}")
                return
                
    summary = st.session_state.portfolio_summary
    holdings = st.session_state.portfolio_holdings
    
    st.markdown("---")
    
    # Section 2: Portfolio Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    # Default values safely
    ti = summary.get('total_invested', 0) if summary else 0
    cv = summary.get('total_current_value', 0) if summary else 0
    pnl_val = summary.get('total_pnl', 0) if summary else 0
    pct_val = summary.get('overall_percentage_change', 0) if summary else 0
    
    c_status = "normal" if pnl_val >= 0 else "inverse"
    
    c1.metric("Total Invested", f"₹{ti:,.2f}")
    c2.metric("Current Value", f"₹{cv:,.2f}")
    c3.metric("Total P&L", f"₹{pnl_val:,.2f}", delta=f"₹{pnl_val:,.2f}", delta_color=c_status)
    c4.metric("Overall % Change", f"{pct_val}%", delta=f"{pct_val}%", delta_color=c_status)
    
    st.markdown("---")
    
    # Section 3: Holdings Table
    st.markdown("### Your Holdings")
    
    if holdings and len(holdings) > 0:
        # Table Header Grid
        cols = st.columns([1.2, 0.8, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.8])
        headers = ["Symbol", "Quantity", "Buy Price (₹)", "Current Price (₹)", "Total Invested (₹)", "Value (₹)", "P&L (₹)", "%", "Actions"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
            
        st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        # Rows
        for i, item in enumerate(holdings):
            sym = item.get("symbol", "")
            qty = item.get("quantity", 0)
            bp = float(item.get("buy_price", 0))
            cp = float(item.get("current_price", 0))
            pnl = float(item.get("profit_or_loss", 0))
            pct = float(item.get("percentage_change", 0))
            price_fetched = item.get("price_fetched", False)
            
            # Derived fields
            total_invested = float(item.get("total_invested", qty * bp))
            current_value = float(item.get("current_value", qty * cp))
            
            # Price fetched indicator
            indicator = "🟢 " if price_fetched else "🔴 "
            
            # Theme-aware text color
            txt_color = "#F8FAFC" if st.session_state.get('theme') == 'dark' else "#1E293B"
            row = st.columns([1.2, 0.8, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.8])
            row[0].write(f"**{sym}**")
            row[1].write(f"{qty}")
            row[2].write(f"₹{bp:,.2f}")
            row[3].write(f"{indicator}₹{cp:,.2f}")
            row[4].write(f"₹{total_invested:,.2f}")
            row[5].write(f"₹{current_value:,.2f}")
            
            # P&L color logic
            pnl_color = "#10B981" if pnl >= 0 else "#EF4444"
            row[6].markdown(f"<p style='color:{pnl_color}; margin:0; font-weight:600;'>₹{pnl:,.2f}</p>", unsafe_allow_html=True)
            row[7].markdown(f"<p style='color:{pnl_color}; margin:0; font-weight:600;'>{pct}%</p>", unsafe_allow_html=True)
            
            # Action Buttons - Strictly Horizontal Group
            with row[8]:
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("📝 Edit", key=f"edit_btn_{sym}_{i}", use_container_width=True):
                    st.session_state.portfolio_remove_symbol = None
                    st.session_state.portfolio_edit_symbol = sym if st.session_state.portfolio_edit_symbol != sym else None
                    st.rerun()
                if btn_col2.button("🗑️ Remove", key=f"rem_btn_{sym}_{i}", use_container_width=True):
                    st.session_state.portfolio_edit_symbol = None
                    st.session_state.portfolio_remove_symbol = sym if st.session_state.portfolio_remove_symbol != sym else None
                    st.rerun()
                
            st.markdown(f"<hr style='margin: 0.2rem 0; border-color: rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
            
    else:
        st.info("You have no holdings yet. Add your first stock below!")
        
    # Section 5 & 6: Action Forms (Rendered below table based on state)
    if st.session_state.portfolio_edit_symbol:
        st.markdown("---")
        st.markdown(f"### Edit Holding: {st.session_state.portfolio_edit_symbol}")
        item = next((h for h in holdings if h["symbol"] == st.session_state.portfolio_edit_symbol), None)
        if item:
            with st.form(key="edit_holding_form"):
                e1, e2 = st.columns(2)
                new_qty = e1.number_input("Update Quantity", min_value=1, value=int(item["quantity"]), step=1)
                new_bp = e2.number_input("Update Buy Price per share (₹)", min_value=1.0, value=float(item["buy_price"]), step=1.0)
                
                col_save, col_cancel = st.columns(2)
                submit_edit = col_save.form_submit_button("Save Changes", type="primary", width='stretch')
                cancel_edit = col_cancel.form_submit_button("Cancel", width='stretch')
                
                if submit_edit:
                    with st.spinner("Saving changes..."):
                        payload = {"user_id": user_id, "symbol": item["symbol"], "new_quantity": new_qty, "new_buy_price": new_bp}
                        rq = requests.put(f"{api_base}/portfolio/update", json=payload, headers={"Authorization": f"Bearer {token}"})
                        if rq.status_code == 200:
                            st.success(rq.json().get("message", "Holding updated successfully!"))
                            st.session_state.portfolio_edit_symbol = None
                            fetch_data(token, api_base, user_id)
                            st.rerun()
                        else:
                            st.error(f"Error updating holding: {rq.json().get('detail', 'Unknown error')}")
                            
                if cancel_edit:
                    st.session_state.portfolio_edit_symbol = None
                    st.rerun()

    if st.session_state.portfolio_remove_symbol:
        st.markdown("---")
        st.warning(f"Are you sure you want to remove {st.session_state.portfolio_remove_symbol} from your portfolio?")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Yes, Remove", type="primary", width='stretch'):
            with st.spinner("Removing holding..."):
                payload = {"user_id": user_id, "symbol": st.session_state.portfolio_remove_symbol}
                rq = requests.request("DELETE", f"{api_base}/portfolio/remove", json=payload, headers={"Authorization": f"Bearer {token}"})
                if rq.status_code == 200:
                    st.success(f"Successfully removed {st.session_state.portfolio_remove_symbol} from portfolio.")
                    st.session_state.portfolio_remove_symbol = None
                    fetch_data(token, api_base, user_id)
                    st.rerun()
                else:
                    st.error(f"Error removing holding: {rq.json().get('detail', 'Unknown error')}")
                    
        if col_no.button("No, Cancel", width='stretch'):
            st.session_state.portfolio_remove_symbol = None
            st.rerun()

    st.markdown("---")
    
    # Section 4: Add New Stock Form
    st.markdown("### Add New Stock")
    with st.form("add_stock_form"):
        c1, c2, c3 = st.columns(3)
        symbol = c1.text_input("Stock Symbol", placeholder="e.g. TCS, INFY, RELIANCE")
        qty = c2.number_input("Quantity", min_value=1, step=1)
        price = c3.number_input("Buy Price per share (₹)", min_value=1.0, step=1.0)
        
        submit_add = st.form_submit_button("Submit Transaction", type="primary", width='stretch')
        if submit_add:
            if not symbol:
                st.error("Please enter a stock symbol.")
            else:
                with st.spinner("Adding stock..."):
                    payload = {"user_id": user_id, "symbol": symbol, "quantity": qty, "buy_price": price}
                    rq = requests.post(f"{api_base}/portfolio/add", json=payload, headers={"Authorization": f"Bearer {token}"})
                    if rq.status_code == 200:
                        st.success(rq.json().get("message", "Stock added successfully!"))
                        st.session_state.portfolio_edit_symbol = None
                        st.session_state.portfolio_remove_symbol = None
                        fetch_data(token, api_base, user_id)
                        st.rerun()
                    else:
                        st.error(f"Error adding stock: {rq.json().get('detail', 'Unknown error')}")

    # Section 7: Footer Disclaimer
    st.write("---")
    st.markdown("<p style='color: #64748B; font-size: 0.8rem; text-align: center;'>🔒 Your portfolio data is private and accessible only to you. P&L figures are estimated based on live market data.</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; font-size: 0.75rem; text-align: center; margin-top: 5px; font-weight: 500;'>AI Stock Screener v1.0 | Springboard Mentorship Program 2026</p>", unsafe_allow_html=True)
