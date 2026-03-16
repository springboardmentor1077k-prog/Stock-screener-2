# import streamlit as st
# from backend.database_back import get_connection
# import os
# import sys


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# def fetch_username(user_id):
#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute(
#         "SELECT username FROM users WHERE user_id = %s",
#         (user_id,)
#     )

#     result = cursor.fetchone()

#     conn.close()

#     if result:
#         return result[0]
    
#     return None


# user_id = st.session_state.get("user_id")

# if not user_id:
#     st.warning("Please login first")
#     st.switch_page("login.py")

# username = fetch_username(user_id)

# st.markdown(f"##  Welcome **{username}**")
# st.write("Here is your portfolio.")