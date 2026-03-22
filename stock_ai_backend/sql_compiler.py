FIELD_MAPPING = {
    "pe_ratio": "pe_ratio",
    "sector": "sector",
    "revenue": "revenue"
}


def compile_sql(dsl):

    where_clauses = []
    params = []

    for cond in dsl.conditions:

        column = FIELD_MAPPING.get(cond.field)

        where_clauses.append(f"{column} {cond.operator} %s")
        params.append(cond.value)

    where_sql = f" {dsl.logic} ".join(where_clauses)

    sql = f"""
    SELECT company_name
    FROM companies
    WHERE {where_sql}
    """

    return sql, params
