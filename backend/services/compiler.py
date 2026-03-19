def compile_dsl_to_sql(dsl_query: dict, sort_by=None, order="descending"):

    conditions = dsl_query.get("conditions", [])
    logic = dsl_query.get("logic", "AND")
    time_filter = dsl_query.get("time_filter")

    ALLOWED_OPERATORS = ["=", ">", "<", ">=", "<=", "!="]

    join_growth = False

    # detect growth usage
    for cond in conditions:
        if cond["field"] == "price_growth":
            join_growth = True

    if time_filter:
        join_growth = True

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
        base_query += """
        JOIN (
            SELECT
                company_id,
                date,
                COALESCE(
                    (close - LAG(close) OVER (
                        PARTITION BY company_id ORDER BY date
                    )) * 1.0 /
                    LAG(close) OVER (
                        PARTITION BY company_id ORDER BY date
                    ),
                    0
                ) AS price_growth
            FROM historical_metrics
        ) growth
        ON growth.company_id = s.id
        """

    # -----------------------------
    # TIME FILTER
    # -----------------------------
    if time_filter:
        if time_filter == "last_year":
            where_clauses.append("growth.date >= date('now','-1 year')")
        elif time_filter == "last_6_months":
            where_clauses.append("growth.date >= date('now','-6 months')")

    # -----------------------------
    # WHERE
    # -----------------------------
    if where_clauses:
        base_query += " WHERE " + f" {logic} ".join(where_clauses)

    # -----------------------------
    # LATEST DATE FILTER
    # -----------------------------
    if join_growth and any(c["field"] == "price_growth" for c in conditions):
        if "WHERE" in base_query:
            base_query += """
            AND growth.date = (
                SELECT MAX(date)
                FROM historical_metrics h2
                WHERE h2.company_id = s.id
            )
            """
        else:
            base_query += """
            WHERE growth.date = (
                SELECT MAX(date)
                FROM historical_metrics h2
                WHERE h2.company_id = s.id
            )
            """

    # -----------------------------
    # ✅ CLEAN ORDER BY (FINAL FIX)
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
        
    return base_query, params