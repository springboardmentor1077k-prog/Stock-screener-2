# Field to database column mapping

FIELD_TO_COLUMN = {
    "pe_ratio": "companies.pe_ratio",
    "debt_to_equity": "companies.debt_to_equity",
    "revenue_growth": "financials.revenue_growth"
}

ALLOWED_OPERATORS = {"<", ">", "<=", ">=", "="}


# SQL Compiler Function

def compile_dsl_to_sql(dsl):

    conditions = dsl["conditions"]
    logic = dsl.get("logic", "AND")

    sql_parts = []
    params = []

    for condition in conditions:

        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]

        if field not in FIELD_TO_COLUMN:
            raise ValueError("Invalid field")

        if operator not in ALLOWED_OPERATORS:
            raise ValueError("Invalid operator")

        column = FIELD_TO_COLUMN[field]

        sql_parts.append(f"{column} {operator} %s")
        params.append(value)

    where_clause = f" {logic} ".join(sql_parts)

    sql_query = f"SELECT * FROM companies WHERE {where_clause}"

    return sql_query, params


# Example DSL queries

test_queries = [

    {
        "conditions": [
            {"field": "pe_ratio", "operator": "<", "value": 15}
        ],
        "logic": "AND"
    },

    {
        "conditions": [
            {"field": "pe_ratio", "operator": "<", "value": 20},
            {"field": "debt_to_equity", "operator": "<", "value": 0.5}
        ],
        "logic": "AND"
    },

    {
        "conditions": [
            {"field": "pe_ratio", "operator": "<", "value": 20},
            {"field": "revenue_growth", "operator": ">", "value": 10}
        ],
        "logic": "OR"
    }

]


for dsl in test_queries:

    sql, params = compile_dsl_to_sql(dsl)

    print("\nGenerated SQL:")
    print(sql)

    print("Parameters:")
    print(params)
