import streamlit as st
from ui_components.navbar import logout_button
import random
import requests

company_name = st.session_state.get("selected_company")

if not company_name:
    st.error("No company selected.")
    st.stop()

st.title(f"Company Details: {company_name}")

current_price = round(random.uniform(1000, 3000), 2)

st.subheader("Buy Stock")

st.write(f"Current Price: ₹ {current_price}")


buy_qty = st.number_input(
    "Select Quantity",
    min_value=1,
    max_value=10,
    step=1,
    key="buy_qty"
)

# Total price
total_price = current_price * buy_qty
st.write(f"🧾 Total Cost: ₹ {total_price:,.2f}")

# Buy button
if st.button("Buy Stock"):
    payload = {
        "symbol": company_name,   
        "quantity": buy_qty,
        "buy_price": current_price
    }

    headers = {
        "Authorization": f"Bearer {st.session_state.get('token')}"
    }

    res = requests.post(
        "http://127.0.0.1:7000/buy-stock",
        json=payload,
        headers=headers
    )

    if res.status_code == 200:
        st.success("Stock purchased successfully")
    else:
        st.error("Purchase failed try again")


logout_button()