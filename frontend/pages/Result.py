# import streamlit as st
# import requests
# from ui_components.navbar import logout_button
# from ui_components.result import render_results_table

# BACKEND_URL = "http://localhost:9000/query"

# nl_query = st.session_state.get("nl_query")

# if not nl_query:
#     st.error("No query found. Please go back and try again.")
#     st.stop()

# # -------- CALL API ONLY ONCE --------
# if "results" not in st.session_state or st.session_state.get("last_query") != nl_query:

#     st.session_state.last_query = nl_query

#     with st.spinner("Processing your query... Please wait..."):
#         try:
#             response = requests.post(
#                 BACKEND_URL,
#                 json={"nl_query": nl_query},
#                 timeout=10
#             )

#             if response.status_code == 200:
#                 data = response.json()
#                 st.session_state.results = data
#                 st.session_state.error = None

#             elif response.status_code == 422:
#                 st.session_state.results = None
#                 st.session_state.error = response.json().get("detail", {})

#             elif response.status_code == 429:
#                 st.session_state.results = None
#                 st.session_state.error = {"message": "Too many requests"}

#             else:
#                 st.session_state.results = None
#                 st.session_state.error = {"message": "Unexpected server error"}

#         except requests.exceptions.Timeout:
#             st.session_state.results = None
#             st.session_state.error = {"message": "Request timed out"}

#         except Exception:
#             st.session_state.results = None
#             st.session_state.error = {"message": "Backend connection failed"}

# # -------- DISPLAY SECTION --------
# data = st.session_state.get("results")
# error = st.session_state.get("error")

# if error:
#     st.warning(error.get("message", "Something went wrong"))

#     if "suggestion" in error:
#         st.info(error["suggestion"])

# elif data:
#     count = data.get("count", 0)

#     if count == 0:
#         st.success("No companies matched your query.")
#     else:
#         st.success(f"Found {count} matching companies.")

#     render_results_table(data)

# # -------- NAVBAR --------
# logout_button()