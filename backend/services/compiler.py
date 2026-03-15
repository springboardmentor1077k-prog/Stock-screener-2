def compile_dsl_to_sql(dsl_query: dict):

    conditions = dsl_query.get("conditions", [])
    logic = dsl_query.get("logic", "AND")

    base_query = """
    SELECT
        s.symbol,
        s.company_name,
        s.sector,
        f.pe_ratio,
        f.peg_ratio,
        f.market_cap,
        f.revenue,
        f.ebitda,
        f.profit_margin
    FROM fundamentals f
    JOIN symbols s
    ON f.company_id = s.id
    """

    where_clauses = []
    params = []

    for cond in conditions:

        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        # sector belongs to symbols table
        if field == "sector":
            where_clauses.append(f"s.sector {operator} ?")
        else:
            where_clauses.append(f"f.{field} {operator} ?")

        params.append(value)

    if where_clauses:
        base_query += " WHERE " + f" {logic} ".join(where_clauses)

    return base_query, params