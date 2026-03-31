import streamlit as st
from ui_components.navbar import logout_button
import random
import requests
import pandas as pd
from ui_components.footer import header
import yfinance as yf

header()

company_name = st.session_state.get("selected_company")

company_name = st.session_state.get("selected_company")


if not company_name:
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.get('token')}"
        }

        res = requests.post(
            "http://127.0.0.1:7000/portfolio/get-portfolio",
            headers=headers,
            timeout=300
        )

        if res.status_code == 200:
            portfolio = res.json().get("data", [])

            if portfolio:
               
                company_name = portfolio[0]["symbol"]

                st.session_state["selected_company"] = company_name

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
    "http://127.0.0.1:7000/company/company-details",
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
        st.metric("Market Cap", f"₹{market_cap/1e12:.2f} T")


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
        f.get("promoter_holding"),
        f.get("ebitda"),          
        f.get("debt_free_cash")   
    ]
}

df_metrics = pd.DataFrame(metrics_table)

df_metrics.index = range(1, len(df_metrics) + 1)
st.dataframe(df_metrics, width="stretch")


#prices
def get_live_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    return float(data["Close"].iloc[-1])



current_price = round(float(get_live_price(company_name)), 4)



    
st.subheader("Buy Stock")

if current_price:
    current_price = round(float(current_price), 4)
    
else:
     current_price = 1500.7200
    
st.write(f"Current Price: ₹ {current_price:.4f}")
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
        "http://127.0.0.1:7000/trade/buy-stock",
        json=payload,
        headers=headers
    )

    if res.status_code == 200:
        st.success("Stock purchased successfully")
    else:
        st.error("Purchase failed try again")


logout_button()
