from fastapi import params


FIELD_TABLE_MAP = {
    "sector": ("s", "sector"),
    "pe_ratio": ("f", "pe_ratio"),
    "peg_ratio": ("f", "peg_ratio"),
    "debt_fcf": ("f", "debt_fcf"),
    "promoter_holding": ("f", "promoter_holding"),
    "revenue": ("f", "revenue"),
    "ebitda": ("f", "ebitda")
}

def compile_dsl_to_sql(dsl):
    base_query = """
    SELECT s.symbol, s.company_name, f.pe_ratio, f.revenue
    FROM symbols s
    JOIN fundamentals f ON s.id = f.company_id
    """

    where_clauses = []
    params = {}

    for idx, cond in enumerate(dsl.conditions):
        table_alias, column = FIELD_TABLE_MAP[cond.field]
        param_key = f"value_{idx}"
        where_clauses.append(
            f"{table_alias}.{column} {cond.operator} :{param_key}"
        )
        params[param_key] = cond.value

    if where_clauses:
        base_query += " WHERE " + f" {dsl.logic} ".join(where_clauses)

    base_query += " LIMIT :limit"
    params["limit"] = dsl.limit

    print("Generated SQL:", base_query)
    print("SQL Params:", params)

    return base_query, params