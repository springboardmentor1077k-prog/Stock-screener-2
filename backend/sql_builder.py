FIELD_TABLE_MAP = {
    "pe": ("fundamentals", "f"),
    "peg": ("fundamentals", "f"),
    "promoter_holding": ("fundamentals", "f"),

    "revenue": ("historical_metrics", "h"),
    "ebitda": ("historical_metrics", "h"),
    "net_profit": ("historical_metrics", "h"),
    "debt_free_cash": ("historical_metrics", "h"),
}
def compile_conditions(node):

    logic = node.get("logic", "AND")
    conditions = node.get("conditions", [])

    sql_parts = []
    values = []
    required_tables = set()

    for cond in conditions:

        # Nested block
        if "conditions" in cond:
            nested_sql, nested_vals, nested_tables = compile_conditions(cond)
            sql_parts.append(f"({nested_sql})")
            values.extend(nested_vals)
            required_tables.update(nested_tables)
            continue

        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        table_name, alias = FIELD_TABLE_MAP[field]
        required_tables.add((table_name, alias))

        sql_parts.append(f"{alias}.{field} {operator} %s")
        values.append(value)

    return f" {logic} ".join(sql_parts), values, required_tables

def build_safe_query(dsl):

    
    # FUNDAMENTALS MODE
    
    if dsl["entity"] == "fundamentals":

        where_sql, values, tables = compile_conditions(dsl)

        # Always start from symbol
        query = "SELECT s.symbol FROM symbol s "

        # Join required tables only
        for table_name, alias in tables:
            query += f"JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += "WHERE " + where_sql

        # Optional time filter
        if "time_filter" in dsl:
            if dsl["time_filter"]["type"] == "last_n_quarters":
                query += " AND h.reported_date >= CURRENT_DATE - INTERVAL '1 year'"

        query += f" LIMIT {dsl.get('limit', 50)}"

        return query, values

    
    # HISTORICAL GROWTH MODE
    
    elif dsl["entity"] == "historical_metrics":

        metric = dsl["metric"]
        period = dsl["period"]
        direction = dsl["direction"]

        operator = ">" if direction == "increase" else "<"

        query = f"""
        SELECT s.symbol
        FROM symbol s
        JOIN (
            SELECT symbol_id,
                   {metric},
                   LAG({metric}) OVER (
                       PARTITION BY symbol_id
                       ORDER BY financial_year, quarter
                   ) AS prev_value
            FROM historical_metrics
        ) h ON s.symbol_id = h.symbol_id
        WHERE prev_value IS NOT NULL
          AND h.{metric} {operator} prev_value
        GROUP BY s.symbol
        HAVING COUNT(*) >= %s
        LIMIT {dsl.get('limit', 50)}
        """

        return query, [period - 1]

    else:
        raise ValueError("Unsupported entity")