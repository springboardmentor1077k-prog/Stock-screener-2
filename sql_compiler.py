def compile_to_sql(dsl):

    # ✅ KEEP YOUR BASE QUERY (unchanged logic, only enhanced with computed fields)
    base_query = """
    SELECT *,
           ((revenue - prev_revenue) / NULLIF(prev_revenue, 0)) * 100 AS growth_percent,
           (net_profit * 1.2) AS ebitda
    FROM companies
    """

    params = []
    conditions = []

    for cond in dsl.conditions:
        column = cond.field

        # ✅ SAFE COLUMN MAPPING (based on your DB)
        if column == "pe_ratio":
            column = "pe_ratio"
        elif column == "net_profit":
            column = "net_profit"
        elif column == "revenue":
            column = "revenue"
        elif column == "sector":
            column = "sector"
        elif column == "market_cap":
            column = "market_cap"

        # ✅ ADD CONDITION
        conditions.append(f"{column} {cond.operator} %s")
        params.append(cond.value)

    # ✅ BUILD FINAL QUERY
    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    return query, params