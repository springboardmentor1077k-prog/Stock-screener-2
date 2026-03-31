def compile_dsl_to_sql(dsl_query: dict, sort_by=None, order="descending"):

    conditions = dsl_query.get("conditions", [])
    logic = dsl_query.get("logic", "AND")
    time_filter = dsl_query.get("time_filter")
    limit = dsl_query.get("limit")
    ALLOWED_OPERATORS = ["=", ">", "<", ">=", "<=", "!="]

    # Only join growth table if price_growth is used
    join_growth = any(cond["field"] == "price_growth" for cond in conditions)
    
    # -----------------------------
    # BASE SELECT
    # -----------------------------
    if join_growth:
        select_clause = """
        SELECT
            s.id as company_id,
            s.symbol,
            s.company_name,
            s.sector,
            f.pe_ratio,
            f.market_cap,
            f.revenue,
            f.ebitda,
            f.profit_margin,
            growth.price_growth
        """
    else:
        select_clause = """
        SELECT
            s.id as company_id,
            s.symbol,
            s.company_name,
            s.sector,
            f.pe_ratio,
            f.market_cap,
            f.revenue,
            f.ebitda,
            f.profit_margin
        """

    base_query = select_clause + """
    FROM symbols s
    JOIN fundamentals f ON s.id = f.company_id
    """

    params = []
    where_clauses = []

    # -----------------------------
    # CONDITIONS
    # -----------------------------
    for cond in conditions:

        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        if operator not in ALLOWED_OPERATORS:
            continue

        if field == "price_growth":
            where_clauses.append(f"growth.price_growth {operator} ?")
            params.append(value)

        elif field == "sector":
            where_clauses.append(f"s.sector {operator} ?")
            params.append(value)

        else:
            where_clauses.append(f"f.{field} {operator} ?")
            params.append(value)

    # -----------------------------
    # GROWTH JOIN
    # -----------------------------
    if join_growth:

        if time_filter == "last_year":
            date_filter = "WHERE date >= date('now','-1 year')"
        elif time_filter == "last_6_months":
            date_filter = "WHERE date >= date('now','-6 months')"
        elif time_filter == "last_4_quarters":
            date_filter = "WHERE date >= date('now','-12 months')"
        elif time_filter == "recent_quarters":
            date_filter = "WHERE date >= date('now','-3 months')"
        else:
            date_filter = ""

        base_query += f"""
        JOIN (
            SELECT company_id, MAX(price_growth) as price_growth
            FROM price_growth
            {date_filter}
            GROUP BY company_id
        ) growth ON growth.company_id = s.id
        """
            
    # -----------------------------
    # WHERE
    # -----------------------------
    if where_clauses:
        base_query += " WHERE " + f" {logic} ".join(where_clauses)

    # -----------------------------
    #  CLEAN ORDER BY (FINAL FIX)
    # -----------------------------
    ALLOWED_SORT_FIELDS = [
        "pe_ratio",
        "market_cap",
        "revenue",
        "profit_margin",
        "ebitda"
    ]

    if sort_by in ALLOWED_SORT_FIELDS:
        direction = "DESC" if order == "descending" else "ASC"
        base_query += f" ORDER BY f.{sort_by} {direction}"


        # APPLY LIMIT IF EXISTS
    if limit:
        base_query += f" LIMIT {limit}"

    return base_query, params