import streamlit as st
import pandas as pd

st.title("📊 Result Screen")

# -----------------------
# State Management
# -----------------------

if "results" not in st.session_state:
    st.warning("Run a query first from Query Screen")
    st.stop()

data = st.session_state["results"]

if data["status"] != "success":
    st.error(data["message"])
    st.stop()

results = data["results"]

# -----------------------
# Result Summary
# -----------------------

st.subheader("Result Summary")

st.write(f"Total companies found: **{data['count']}**")

# -----------------------
# Convert to DataFrame
# -----------------------

df = pd.DataFrame(results)

# -----------------------
# Result Limiting
# -----------------------

limit = st.slider("Number of results", 1, len(df), len(df))

df = df.head(limit)

# -----------------------
# Sorting Control
# -----------------------

if len(df.columns) > 0:

    sort_column = st.selectbox("Sort by", df.columns)

    df = df.sort_values(by=sort_column)

# -----------------------
# Result Table
# -----------------------

st.subheader("Result Table")

selected = st.dataframe(df, use_container_width=True)

# -----------------------
# Row Interaction
# -----------------------

st.subheader("Select Company")

company = st.selectbox(
    "Select a company for details",
    df["company_name"]
)

if st.button("View Company Details"):

    st.session_state["selected_company"] = company
    st.success(f"{company} selected")
