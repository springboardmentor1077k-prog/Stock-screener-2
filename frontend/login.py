import streamlit as st
import requests

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://localhost:8000"

if "mode" not in st.session_state:
    st.session_state.mode = "Login"

if "token" not in st.session_state:
    st.session_state.token = None



if st.session_state.mode == "Login":
    st.title("Login to Stock Screener")
else:
    st.title("Registration Page")

# FORM

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.session_state.mode == "Register":
    name = st.text_input("Full Name")

# BUTTON ACTION

if st.session_state.mode == "Login":

    if st.button("Login"):
        response = requests.post(
            f"{BACKEND_URL}/login",
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.success("Login Successful ")
            st.switch_page("pages/Query.py")
        else:
            st.error("Invalid mail or password")

else:

    if st.button("Register"):
        response = requests.post(
            f"{BACKEND_URL}/register",
            json={
                "email": email,
                "name": name,
                "password": password
            }
        )

        if response.status_code == 200:
            st.success("Registration Successful")
        else:
            st.error("Registration failed")

# MODE SELECTOR AT BOTTOM

st.markdown("---")

selected = st.radio(
    "Select Mode",
    ["Login", "Register"],
    index=0 if st.session_state.mode == "Login" else 1,
    horizontal=True
)

if selected != st.session_state.mode:
    st.session_state.mode = selected
    st.rerun()