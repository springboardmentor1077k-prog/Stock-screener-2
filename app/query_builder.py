# app/query_builder.py

def build_query(dsl: dict):

    base_query = "SELECT * FROM stocks"
    conditions = []
    values = []

    for i, f in enumerate(dsl["filters"]):
        conditions.append(f"{f['field']} {f['operator']} %s")
        values.append(f["value"])

    query = base_query

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY {dsl['sort_by']} {dsl['order']}"
    query += f" LIMIT %s"
    values.append(dsl["limit"])

    return query, values