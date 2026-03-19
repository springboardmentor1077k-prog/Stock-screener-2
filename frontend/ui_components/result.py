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
        
        sort_column = st.selectbox("Sort by", options=df.columns[2:])
        
        sort_order = st.radio(
            "Order",
            ["Ascending", "Descending"],
            horizontal=True
            )
        
        ascending = True if sort_order == "Ascending" else False

        df = df.sort_values(by=sort_column, ascending=ascending)



        df.index = df.index + 1
        
        st.dataframe(df, use_container_width=True)

        st.write("View Details")

        for i,company in enumerate(results):
            

            col1, col2, col3 = st.columns([5,2,2])

            with col1:
                st.write(
                    f"**{company['company_symbol']}** — {company['company_name']}"
                )

            with col2:
                if st.button("View More",key=f"view_{company['company_symbol']}"):
                    st.session_state.selected_company = company["company_symbol"]
                    st.switch_page("pages/Company_details.py")
                    
            with col3:
                if st.button("Add to Portfolio",key=f"portfolio_{company['company_symbol']}_{i}"
        ):
                    st.session_state.selected_company = company["company_symbol"]
                    # st.success(f"{company['company_symbol']} added to portfolio")
                    # st.session_state.portfolio_message = f"{company['company_symbol']} added to portfolio"
                    st.switch_page("pages/Portfolio.py")
                    
'''                
requests.post(
    "http://localhost:9000/add_portfolio",
    json={"symbol": company["company_symbol"]}
'''
                    
        
                    
                    