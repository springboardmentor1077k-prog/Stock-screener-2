import streamlit as st

def header():
    st.markdown(
        """
        <div style="
            background-color: #1f2937;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 15px;
        ">
            <p style="
                color: #fbbf24;
                font-size: 14px;
                margin: 0;
                font-weight: 500;
            ">
                This application is just for educational purpose, must be used after taking proper knowledge about finances
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )