import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from ui_components.navbar import logout_button

logout_button()

token = st.session_state.get("token")

if not token:
    token = st.query_params.get("token")
    
    if token:
        st.session_state["token"] = token

if not token:
    st.error("Please login")
    st.switch_page("login.py")
    # st.stop()

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.post(
    "http://127.0.0.1:7000/get-portfolio",
    headers=headers
)

data = response.json()



def create_chart(df):
    if df.empty:
        return None

    # Prepare data
    df["Invested"] = df["quantity"] * df["buy_price"]
    pie_data = df.groupby("symbol")["Invested"].sum()

    # Create plot
    fig, ax = plt.subplots(figsize=(4, 4))

    ax.pie(
        pie_data,
        labels=pie_data.index,
        autopct="%1.1f%%",
        textprops={'fontsize': 8}
    )

    ax.set_title("Portfolio Analysis")

    return fig


if data.get("status") == "success":
    user_name = data["username"]
    st.title(f"Welcome {user_name}")
    st.write("This is your protfolio details")
    

    portfolio = data["data"]
    df = pd.DataFrame(portfolio)
    df["Invested in Stocks"] = df["quantity"] * df["buy_price"]
    df["current_price"] = df["buy_price"] * 1.1   # temporary
    st.table(df)
    
    total_invested = df["Invested in Stocks"].sum()
    
    df["current_value"] = df["quantity"] * df["current_price"]
    current_value = df["current_value"].sum()
    
    
    pl = current_value - total_invested
    pl_percent = (pl / total_invested) * 100 if total_invested else 0
    
    col1, col2 = st.columns([3, 2])
    
    
    with col1:
    
        st.subheader("Portfolio Summary")
        st.metric("Total Invested", f"₹ {total_invested:,.2f}")
        st.metric("Current Value", f"₹ {current_value:,.2f}")

        st.metric(
        "Profit / Loss",
        f"₹ {pl:,.2f}",
        f"{pl_percent:.2f}%"
        )
    with col2:
        st.subheader("Distribution")
        fig = create_chart(df)
        if fig:
            st.pyplot(fig)