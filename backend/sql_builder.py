FUNDAMENTAL_FIELDS = {"pe", "peg", "promoter_holding"}

HISTORICAL_FIELDS = {
    "revenue",
    "ebitda",
    "net_profit",
    "debt_free_cash"
}



FIELD_TABLE_MAP = {
    "pe": ("fundamentals", "f"),
    "peg": ("fundamentals", "f"),
    "promoter_holding": ("fundamentals", "f"),

    "revenue": ("historical_metrics", "h"),
    "ebitda": ("historical_metrics", "h"),
    "net_profit": ("historical_metrics", "h"),
    "debt_free_cash": ("historical_metrics", "h"),
}


def detect_query_tables(dsl):

    fields = set()

    def collect(node):
        for cond in node.get("conditions", []):
            if "conditions" in cond:
                collect(cond)
            else:
                fields.add(cond["field"])

    collect(dsl)

    needs_fundamental = any(f in FUNDAMENTAL_FIELDS for f in fields)
    needs_historical = any(f in HISTORICAL_FIELDS for f in fields)

    return needs_fundamental, needs_historical



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

        field = cond.get("field")

        if field not in FIELD_TABLE_MAP:
            raise ValueError(f"Unsupported field: {field}")
        
        operator = cond["operator"]
        value = cond["value"]

        table_name, alias = FIELD_TABLE_MAP[field]
        required_tables.add((table_name, alias))

        sql_parts.append(f"{alias}.{field} {operator} %s")
        values.append(value)

    return f" {logic} ".join(sql_parts), values, required_tables




def build_safe_query(dsl):

    if dsl["entity"] == "fundamentals":

        where_sql, values, tables = compile_conditions(dsl)

        query = "SELECT s.company_name FROM symbol s "

        # Join tables depending on metrics used
        for table_name, alias in tables:
            query += f"JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += " WHERE " + where_sql

        # time filter
        if "time_filter" in dsl and any(t[0] == "historical_metrics" for t in tables):

            tf = dsl["time_filter"]

            if tf["type"] == "last_n_quarters":

                quarters = tf["value"]

                query += f"""
                AND h.reported_date >=
                CURRENT_DATE - INTERVAL '{quarters * 3} months'
                """




        query += f" LIMIT {dsl.get('limit', 50)}"

        return query, values
    
    elif dsl["entity"] == "symbol":

        where_sql, values, tables = compile_conditions(dsl)

        query = "SELECT s.company_name FROM symbol s "

    # join required tables
        for table_name, alias in tables:
            query += f"JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += " WHERE " + where_sql

    # time filter
        if "time_filter" in dsl:

            tf = dsl["time_filter"]

            if tf["type"] == "last_n_quarters":

                quarters = tf["value"]

                query += f"""
                AND h.reported_date >=
                CURRENT_DATE - INTERVAL '{quarters*3} months'
                """

        query += f" LIMIT {dsl.get('limit',50)}"

        return query, values