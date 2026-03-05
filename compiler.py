from sqlalchemy import text

FIELD_MAP = {
    "pe_ratio": {"table": "fundamentals", "column": "pe_ratio", "alias": "f"},
    "eps": {"table": "fundamentals", "column": "eps", "alias": "f"},
    "revenue": {"table": "fundamentals", "column": "revenue", "alias": "f"},
    "debt": {"table": "fundamentals", "column": "debt", "alias": "f"},
    "revenue_growth": {"table": "fundamentals", "column": "revenue_growth", "alias": "f"},
    "price_change_1y": {"table": "fundamentals", "column": "price_change_1y", "alias": "f"},
    "market_cap": {"table": "fundamentals", "column": "market_cap", "alias": "f"},
    "sector": {"table": "symbols", "column": "sector", "alias": "s"},
    "reported_date": {"table": "fundamentals", "column": "reported_date", "alias": "f"}
}

SAFE_OPERATORS = {"<", "<=", ">", ">=", "="}
SAFE_FIELDS = set(FIELD_MAP.keys())


def compile_node(node, param_index=0):
    clauses = []
    params = {}

    for condition in node.conditions:

        #  If nested DSLNode
        if hasattr(condition, "conditions"):
            nested_clause, nested_params, param_index = compile_node(
                condition,
                param_index
            )
            clauses.append(f"({nested_clause})")
            params.update(nested_params)
            continue

        #  Normal Condition
        # Validate field
        if condition.field not in SAFE_FIELDS:
            raise ValueError(f"Invalid field: {condition.field}")

        field_info = FIELD_MAP[condition.field]

        param_name = f"value_{param_index}"
        param_index += 1

        alias = field_info["alias"]
        column = field_info["column"]
        
        # Validate operator
        if condition.operator not in SAFE_OPERATORS:
            raise ValueError(f"Invalid operator: {condition.operator}")

        clause = f"{alias}.{column} {condition.operator} :{param_name}"
        clauses.append(clause)

        params[param_name] = condition.value

    where_clause = f" {node.logic} ".join(clauses)

    return where_clause, params, param_index


def detect_tables(node):
    tables = set()

    for condition in node.conditions:

        # If nested DSLNode → recurse
        if hasattr(condition, "conditions"):
            nested_tables = detect_tables(condition)
            tables.update(nested_tables)
            continue

        # Normal condition
        tables.add(FIELD_MAP[condition.field]["table"])

    return tables

def apply_time_filter(where_clause, params, time_filter):

    if not time_filter:
        return where_clause, params

    if time_filter.type == "last_n_quarters":
        quarters = int(time_filter.value)
        months = quarters * 3

        where_clause += " AND f.reported_date >= (CURRENT_DATE - (:months || ' month')::interval)"
        params["months"] = months

    elif time_filter.type == "year":
        where_clause += " AND EXTRACT(YEAR FROM f.reported_date) = :year"
        params["year"] = time_filter.value

    elif time_filter.type == "range":
        where_clause += " AND f.reported_date BETWEEN :from_date AND :to_date"
        params["from_date"] = time_filter.from_date
        params["to_date"] = time_filter.to_date

    return where_clause, params



def build_sql_from_dsl(dsl):

    where_clause, params, _ = compile_node(dsl.root)
    
    if not where_clause:
        raise ValueError("Empty WHERE clause not allowed")

    where_clause, params = apply_time_filter(
        where_clause,
        params,
        dsl.time_filter
    )
    
    
    tables_used = detect_tables(dsl.root)

    join_clause = ""

    if "fundamentals" in tables_used:
        join_clause += """
            JOIN fundamentals f
                ON s.id = f.symbol_id
                AND f.reported_date = (
                    SELECT MAX(f2.reported_date)
                    FROM fundamentals f2
                    WHERE f2.symbol_id = s.id
                )
        """
    query = f"""
          SELECT s.symbol,
                s.sector,
                f.pe_ratio,
                f.eps,
                f.market_cap,
                f.revenue_growth,
                f.price_change_1y
          FROM symbols s
          {join_clause}
          WHERE {where_clause}
      """
    
    # Sorting
    if dsl.sort_field and dsl.sort_field in FIELD_MAP:
        field_info = FIELD_MAP[dsl.sort_field]
        alias = field_info["alias"]
        column = field_info["column"]
        query += f" ORDER BY {alias}.{column} {dsl.sort_order.upper()}"

    if dsl.limit:
        if dsl.limit > 100:
            raise ValueError("Limit exceeds allowed maximum")

        query += " LIMIT :limit"
        params["limit"] = dsl.limit
    
    return text(query), params