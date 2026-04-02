import streamlit as st
import requests
import random
import string

# 🔐 Password generator
def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(12))

# 📊 Password strength
def check_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*" for c in password):
        score += 1
    return score

# 🔴 LOGOUT FUNCTION (NEW)
def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# 🔐 AUTH SCREEN
def auth_screen():
    st.title("🔐 Authentication")

    option = st.radio("Select", ["Login", "Register"])

    email = st.text_input("Email")

    show_password = st.checkbox("Show Password")

    password = st.text_input(
        "Password",
        type="default" if show_password else "password"
    )

    # REGISTER
    if option == "Register":
        confirm_password = st.text_input(
            "Confirm Password",
            type="default" if show_password else "password"
        )

        # Suggest password
        if st.button("Suggest Strong Password"):
            st.success(generate_password())

        # Strength check
        if password:
            strength = check_strength(password)
            if strength <= 1:
                st.error("Weak Password")
            elif strength == 2:
                st.warning("Medium Password")
            else:
                st.success("Strong Password")

        if st.button("Create Account"):
            if password != confirm_password:
                st.error("Passwords do not match")
            else:
                res = requests.post(
                    "http://127.0.0.1:8000/register",
                    json={"email": email, "password": password}
                )

                if res.status_code == 200:
                    st.success("Registered Successfully")
                else:
                    st.error("Registration Failed")

    # LOGIN
    else:
        if st.button("Login"):
            res = requests.post(
                "http://127.0.0.1:8000/login",
                json={"email": email, "password": password}
            )

            if res.status_code == 200:
                data = res.json()  # 🔥 IMPORTANT

                st.success("Login Successful")

                # ✅ STORE SESSION
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = data.get("user_id")

            else:
                st.error("Invalid Credentials")
                