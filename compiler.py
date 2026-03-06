def compile_dsl_to_sql(dsl_dict: dict):
    # Base query targeting the fundamentals table we created
    base_query = "SELECT * FROM fundamentals WHERE "
    conditions_list = []
    params = []
    
    # Iterate through each condition in the DSL
    for cond in dsl_dict.get("conditions", []):
        # Using parameterized queries (?) to prevent SQL Injection
        conditions_list.append(f"{cond['field']} {cond['operator']} ?")
        params.append(cond['value'])
    
    # Join conditions using the specified logical operator (AND / OR)
    logic_operator = f" {dsl_dict.get('logic', 'AND')} "
    final_query = base_query + logic_operator.join(conditions_list)
    
    return final_query, params