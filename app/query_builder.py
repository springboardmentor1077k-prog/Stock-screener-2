def build_query(dsl: dict):
    base_query = "SELECT * FROM stocks"
    conditions = []
    values = []

    for f in dsl["filters"]:
        conditions.append(f"{f['field']} {f['operator']} %s")
        values.append(f["value"])

    where_clause = " AND ".join(conditions)
    query = base_query

    if where_clause:
        query += " WHERE " + where_clause

    query += f" ORDER BY {dsl['sort_by']} {dsl['order']}"
    query += " LIMIT %s"
    values.append(dsl["limit"])

    return query, values