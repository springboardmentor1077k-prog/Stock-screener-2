FIELD_TABLE_MAP = {
    "pe_ratio": ("fundamentals", "pe_ratio"),
    "peg_ratio": ("fundamentals", "peg_ratio"),
    "debt_fcf": ("fundamentals", "debt_fcf"),
    "revenue": ("fundamentals", "revenue"),
    "ebitda": ("fundamentals", "ebitda"),
    "promoter_holding": ("fundamentals", "promoter_holding")
}


def compile_dsl_to_sql(dsl):

    base_query = """
    SELECT fundamentals.*
    FROM fundamentals
    """

    conditions = []
    params = []

    for condition in dsl.conditions:

        table, column = FIELD_TABLE_MAP[condition.field]

        clause = f"{table}.{column} {condition.operator} ?"

        conditions.append(clause)

        params.append(condition.value)

    if conditions:
        where_clause = f" {dsl.logic} ".join(conditions)
        base_query += f" WHERE {where_clause}"

    return base_query, params