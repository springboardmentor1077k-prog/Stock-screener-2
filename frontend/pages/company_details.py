import streamlit as st
from ui_components.navbar import logout_button
import random
import requests
import pandas as pd

company_name = st.session_state.get("selected_company")

company_name = st.session_state.get("selected_company")


if not company_name:
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.get('token')}"
        }

        res = requests.post(
            "http://127.0.0.1:7000/get-portfolio",
            headers=headers,
            timeout=5
        )

        if res.status_code == 200:
            portfolio = res.json().get("data", [])

            if portfolio:
                # ✅ pick first company
                company_name = portfolio[0]["symbol"]

                # store back in session
                st.session_state["selected_company"] = company_name

                st.info(f"Showing portfolio company: {company_name}")

            else:
                st.warning("No companies in portfolio. Please buy a stock first.")
                st.stop()

        else:
            st.error("Unable to fetch portfolio.")
            st.stop()

    except Exception as e:
        st.error("Error fetching portfolio")
        st.stop()

# st.title(f"Company Details: {company_name}")

response = requests.post(
    "http://127.0.0.1:7000/company-details",
    json={"symbol": company_name}
)

data = response.json()

if data:
    st.title(data["name"])

    st.markdown("---")

    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Founded", data["founded"])

    with col2:
        st.metric("Type", data["type"])

    with col3:
        market_cap = data["market_cap"]
        st.metric("Market Cap", f"₹ {market_cap/1e12:.2f} T")


    st.write(f"**Sector:** {data['sector']}")

    st.markdown("---")


    st.subheader("About Company")
    st.write(data["description"])



st.markdown("---")
st.subheader("Financial Metrics")

f = data["fundamentals"]

# Convert to table format
metrics_table = {
    "Metric": [
        "P/E Ratio",
        "PEG Ratio",
        "Promoter Holding (%)",
        "EBITDA",
        "Free Cash Flow"
    ],
    "Value": [
        f.get("pe"),
        f.get("peg"),
        f.get("promoter_holding", "N/A"),
        f"₹ {f.get('ebitda', 0):,}" if f.get("ebitda") else "N/A",
        f"₹ {f.get('debt_free_cash') or 0:,}"
    ]
}

df_metrics = pd.DataFrame(metrics_table)
df_metrics.index += 1
st.table(df_metrics)



#prices
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
st.write(f"Total Cost: ₹ {total_price:,.2f}")

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