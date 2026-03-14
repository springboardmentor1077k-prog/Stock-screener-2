import pandas as pd
import streamlit as st


'''
Sort the order in which the user wants
like assending (default)
desc rev the array'''


def render_results_table(data):

    if "data" in data and data["data"]:

        results = data["data"]

        st.subheader("Matching Companies for your Query")
        
        # st.write("")

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

        st.dataframe(df, use_container_width=True)

        st.write("View Details")

        for company in results:

            col1, col2 = st.columns([4,1])

            with col1:
                st.write(
                    f"**{company['company_symbol']}** — {company['company_name']}"
                )

            with col2:
                if st.button("View More",key=f"view_{company['company_symbol']}"):
                    st.session_state.selected_company = company["company_symbol"]
                    st.switch_page("pages/company_details.py")
                    