import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="StockSense AI", layout="wide")

# ---------- GLOBAL CSS ----------
st.markdown("""
<style>

/* REMOVE STREAMLIT HEADER + MENU */
header[data-testid="stHeader"] {display:none;}
#MainMenu {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stDecoration"] {display:none;}
[data-testid="stStatusWidget"] {display:none;}

/* REMOVE TOP SPACING */
.block-container {
padding-top:0rem;
padding-bottom:0rem;
}

/* HIDE SIDEBAR */
[data-testid="stSidebar"] {display:none;}
[data-testid="collapsedControl"] {display:none;}

/* GOOGLE FONT */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] {
font-family: 'Inter', sans-serif;
}

/* BACKGROUND */
.stApp {
background:
radial-gradient(circle at 20% 20%, rgba(59,130,246,0.15), transparent 40%),
radial-gradient(circle at 80% 30%, rgba(37,99,235,0.15), transparent 40%),
radial-gradient(circle at 50% 80%, rgba(30,58,95,0.2), transparent 40%),
linear-gradient(180deg,#020712,#081424);
}

/* GRID */
.stApp::before{
content:"";
position:fixed;
width:100%;
height:100%;
background-image:
linear-gradient(rgba(59,130,246,0.07) 1px, transparent 1px),
linear-gradient(90deg, rgba(59,130,246,0.07) 1px, transparent 1px);
background-size:80px 80px;
pointer-events:none;
}

/* TITLE */
.title {
text-align:center;
font-size:46px;
font-weight:700;
font-family:'Orbitron', sans-serif;
letter-spacing:1px;
color:#e6f1ff;

text-shadow:
0 0 6px #3b82f6,
0 0 14px #2563eb,
0 0 28px rgba(59,130,246,0.6);
}

/* SUBTITLE */
.subtitle {
text-align:center;
color:#9fb0c4;
margin-top:6px;
margin-bottom:20px;
font-size:15px;
}

/* INPUT */
.stTextInput input {
background:#081424;
border:1px solid #1e3a5f;
border-radius:10px;
color:white;
}

/* BUTTON */
.stButton button {
background: linear-gradient(90deg,#3b82f6,#2563eb);
width:100%;
height:46px;
border-radius:10px;
border:none;
font-weight:600;
color:white;
}
            
/* REMOVE STREAMLIT INNER RED BORDER */
input {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Remove red error highlight */
input:invalid {
    border: none !important;
    box-shadow: none !important;
}

/* BaseWeb input inner div */
div[data-baseweb="base-input"] {
    border: none !important;
    box-shadow: none !important;
}

/* Keep only outer container border */
div[data-baseweb="input"] {
    border: 1px solid #1e3a5f !important;
    background-color: #081424 !important;
    border-radius: 8px !important;
}

/* Focus effect */
div[data-baseweb="input"]:focus-within {
    border: 1px solid #3b82f6 !important;
    box-shadow: 0 0 8px rgba(59,130,246,0.35) !important;
}
</style>
""", unsafe_allow_html=True)


# ---------- SESSION ----------
if "token" not in st.session_state:
    st.session_state.token = None

if "page" not in st.session_state:
    st.session_state.page = "login"


# ---------- LOGIN ----------
def login():

    st.write("")
    st.write("")
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([2,1.5,2])

    with col2:

        st.markdown('<div class="title">StockSense AI</div>', unsafe_allow_html=True)

        icon1, icon2, icon3 = st.columns([2,1,2])
        with icon2:
            st.image("frontend/assets/stock_icon.png", width=95)

        st.markdown(
            '<div class="subtitle">AI-Powered Stock Screener and Advisory Platform</div>',
            unsafe_allow_html=True
        )

        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")

        if st.button("Log In", use_container_width=True):

            response = requests.post(
                f"{API_URL}/auth/login",
                json={
                    "email": email.strip(),
                    "password": password.strip()
                }
            )

            if response.status_code == 200:
                data = response.json()

                st.session_state.token = data["access_token"]
                st.session_state.user_id = data["user_id"]

                st.switch_page("pages/query_screen.py")

            else:
                st.error("Invalid email or password")

        st.markdown(
            '<div style="text-align:center;margin-top:12px;">Don\'t have an account? <a href="?page=signup">Sign up</a></div>',
            unsafe_allow_html=True
        )


# ---------- SIGNUP ----------
def signup():

    st.write("")
    st.write("")
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([2,1.5,2])

    with col2:

        st.markdown('<div class="title">Create Account</div>', unsafe_allow_html=True)

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Account", use_container_width=True):

            response = requests.post(
                f"{API_URL}/auth/signup",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )

            if response.status_code == 200:
                st.success("Account created! Please login.")
                st.query_params.update(page="login")
                st.rerun()

            else:
                st.error("Signup failed")

        st.markdown(
            '<div style="text-align:center;margin-top:12px;">Already have an account? <a href="?page=login">Back to Login</a></div>',
            unsafe_allow_html=True
        )

# ---------- ROUTING ----------
params = st.query_params

if "page" in params:
    st.session_state.page = params["page"]

if st.session_state.token is None:
    if st.session_state.page == "signup":
        signup()
    else:
        login()
else:
    st.switch_page("pages/query_screen.py")