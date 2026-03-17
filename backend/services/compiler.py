def compile_dsl_to_sql(dsl_query: dict):

    conditions = dsl_query.get("conditions", [])
    logic = dsl_query.get("logic", "AND")
    time_filter = dsl_query.get("time_filter")

    base_query = """
    SELECT
        s.id as company_id,
        s.symbol,
        s.company_name,
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

    params = []
    where_clauses = []

    # -----------------------------
    # CONDITION FILTERS
    # -----------------------------
    for cond in conditions:

        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        if field == "sector":
            where_clauses.append(f"s.sector {operator} ?")
        else:
            where_clauses.append(f"f.{field} {operator} ?")

        params.append(value)

    # -----------------------------
    # TIME FILTER SUPPORT
    # -----------------------------
    if time_filter:

        base_query += """
        JOIN historical_metrics h
        ON s.id = h.company_id
        """

        if time_filter == "last_year":
            where_clauses.append(
                "h.date >= date('now','-1 year')"
            )

        elif time_filter == "last_4_quarters":
            where_clauses.append(
                "h.date >= date('now','-12 months')"
            )

        elif time_filter == "recent_quarters":
            where_clauses.append(
                "h.date >= date('now','-6 months')"
            )

    # -----------------------------
    # WHERE CLAUSE
    # -----------------------------
    if where_clauses:
        base_query += " WHERE " + f" {logic} ".join(where_clauses)

    return base_query, params