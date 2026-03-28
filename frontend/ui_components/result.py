import pandas as pd
import streamlit as st


def render_results_table(data):

    if "data" in data and data["data"]:

        results = data["data"]

        st.subheader("Matching Companies for your Query")

        table_data = []

        for company in results:
            row = {
                "Symbol": company.get("company_symbol"),
                "Company Name": company.get("company_name"),
            }

            for key, value in company.items():
                if key not in ["company_symbol", "company_name"]:
                    row[key.upper()] = value

            table_data.append(row)

        df = pd.DataFrame(table_data)

        # -------- SORTING --------
        sort_column = st.selectbox("Sort by", options=df.columns[2:])

        sort_order = st.radio(
            "Order",
            ["Ascending", "Descending"],
            horizontal=True
        )

        ascending = True if sort_order == "Ascending" else False

        df = df.sort_values(by=sort_column, ascending=ascending).reset_index(drop=True)

        # -------- PAGINATION --------
        page_size = 3

        if "last_query" not in st.session_state or st.session_state.last_query != str(data):
            st.session_state.page = 1
            st.session_state.last_query = str(data)

        if "page" not in st.session_state:
            st.session_state.page = 1

        total_rows = len(df)
        total_pages = (total_rows // page_size) + (1 if total_rows % page_size else 0)

        start = (st.session_state.page - 1) * page_size
        end = start + page_size

        df_page = df.iloc[start:end]

        # Reset index for display
        df_page.index = range(start + 1, min(end, total_rows) + 1)

        # -------- DISPLAY TABLE --------
        st.dataframe(df_page, use_container_width=True)

        # -------- PAGINATION CONTROLS --------
        col1, col2, col3 = st.columns([6, 1, 1])

        with col2:
            if st.button("⬅️", disabled=st.session_state.page == 1):
                st.session_state.page -= 1
                st.rerun()

        with col3:
            if st.button("➡️", disabled=st.session_state.page == total_pages):
                st.session_state.page += 1
                st.rerun()

        st.write(f"Page {st.session_state.page} of {total_pages}")

        st.write("### View Details")

        for idx, row in df_page.iterrows():

            col1, col2 = st.columns([5, 2])

            with col1:
                st.write(
                f"**{row['Symbol']}** — {row['Company Name']}"
                )

            with col2:
                if st.button("View More", key=f"view_{row['Symbol']}"):
                    st.session_state.selected_company = row["Symbol"]
                    st.switch_page("pages/Company_details.py")