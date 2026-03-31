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
    "ebitda": ("fundamentals", "f"),
    "debt_free_cash": ("fundamentals", "f"),
    
    "revenue": ("historical_metrics", "h"),
    "net_profit": ("historical_metrics", "h"),
    
}

def is_growth_field(field):
    return field.endswith("_growth")




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
    use_historical = "time_filter" in node

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
        operator = cond["operator"]
        value = cond["value"]
        
        if is_growth_field(field):
            # base_metric = field.replace("_growth", "")
            table_name, alias = ("historical_metrics", "h")

            required_tables.add((table_name, alias))

            sql_parts.append(f"h.growth {operator} %s")
            values.append(value)
            continue

        if field not in FIELD_TABLE_MAP:
            raise ValueError(f"Unsupported field: {field}")
        
        # operator = cond["operator"]
        # value = cond["value"]
        if use_historical and field in ["ebitda", "debt_free_cash"]:
            table_name, alias = ("historical_metrics", "h")
        else:
            table_name, alias = FIELD_TABLE_MAP[field]
        
        required_tables.add((table_name, alias))

        sql_parts.append(f"{alias}.{field} {operator} %s")
        values.append(value)

    return f" {logic} ".join(sql_parts), values, required_tables





def build_safe_query(dsl):

    fields = set()

    def collect(node):
        for cond in node.get("conditions", []):
            if "conditions" in cond:
                collect(cond)
            else:
                fields.add(cond["field"])

    collect(dsl)

    growth_fields = [f for f in fields if is_growth_field(f)]

   
    # GROWTH QUERY
   
    if growth_fields:

        base_metric = growth_fields[0].replace("_growth", "")

        where_sql, values, tables = compile_conditions(dsl)

       
        select_fields = [
            "s.company_symbol",
            "s.company_name",
            f"h.{base_metric}",
            "h.growth"
        ]

        # include filter fields (like pe)
        for cond in dsl["conditions"]:
            field = cond.get("field")

            if not is_growth_field(field) and field in FIELD_TABLE_MAP:
                table, alias = FIELD_TABLE_MAP[field]
                select_fields.append(f"{alias}.{field}")

        select_fields = list(set(select_fields))

        query = f"""
        SELECT DISTINCT ON (s.company_symbol)
            {", ".join(select_fields)}
        FROM symbol s
        JOIN (
            SELECT
                symbol_id,
                {base_metric},
                financial_year,
                quarter,
                reported_date,

                LAG({base_metric}) OVER (
                    PARTITION BY symbol_id
                    ORDER BY financial_year, quarter
                ) AS prev_value,

                CASE 
                    WHEN LAG({base_metric}) OVER (
                        PARTITION BY symbol_id
                        ORDER BY financial_year, quarter
                    ) IS NULL THEN NULL
                    ELSE (
                        ({base_metric} - LAG({base_metric}) OVER (
                            PARTITION BY symbol_id
                            ORDER BY financial_year, quarter
                        ))
                        / NULLIF(LAG({base_metric}) OVER (
                            PARTITION BY symbol_id
                            ORDER BY financial_year, quarter
                        ), 0)
                    ) * 100
                END AS growth
            FROM historical_metrics
        ) h ON s.symbol_id = h.symbol_id
        """

        # joins
        for table_name, alias in tables:
            if alias != "h":
                query += f" JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += " WHERE " + where_sql
        query += " AND h.growth IS NOT NULL"

        # time filter
        if "time_filter" in dsl:
            quarters = dsl["time_filter"]["value"]
            query += f"""
            AND h.reported_date >= CURRENT_DATE - INTERVAL '{quarters * 3} months'
            """

        query += f" LIMIT {dsl.get('limit', 50)}"

        return query, values

   
    # FUNDAMENTALS
   
    elif dsl["entity"] == "fundamentals":

        where_sql, values, tables = compile_conditions(dsl)

        fields = set(cond["field"] for cond in dsl["conditions"] if "field" in cond)

        metrics = []
        for field in fields:
            table_name, alias = FIELD_TABLE_MAP[field]
            metrics.append(f"{alias}.{field}")

        query = f"""
        SELECT DISTINCT ON (s.company_symbol)
            s.company_symbol, s.company_name, {", ".join(metrics)}
        FROM symbol s
        """

        for table_name, alias in tables:
            query += f" JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += " WHERE " + where_sql
        query += f" LIMIT {dsl.get('limit', 50)}"

        return query, values

   
    # SYMBOL (MIXED)
   
    elif dsl["entity"] == "symbol":

        where_sql, values, tables = compile_conditions(dsl)

        fields = set(cond["field"] for cond in dsl["conditions"] if "field" in cond)

        metrics = []
        for field in fields:
            table_name, alias = FIELD_TABLE_MAP[field]
            metrics.append(f"{alias}.{field}")

        query = f"""
        SELECT DISTINCT ON (s.company_symbol)
            s.company_symbol, s.company_name, {", ".join(metrics)}
        FROM symbol s
        """

        for table_name, alias in tables:
            query += f" JOIN {table_name} {alias} ON s.symbol_id = {alias}.symbol_id "

        query += " WHERE " + where_sql

        if "time_filter" in dsl and any(t[1] == "h" for t in tables):
            quarters = dsl["time_filter"]["value"]
            query += f"""
            AND h.reported_date >= CURRENT_DATE - INTERVAL '{quarters * 3} months'
            """

        query += f" LIMIT {dsl.get('limit', 50)}"

        return query, values