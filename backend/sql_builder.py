def build_safe_query(dsl):

    base_query = f"SELECT * FROM {dsl['entity']} WHERE "
    conditions = []
    values = []

    for cond in dsl["conditions"]:
        conditions.append(f"{cond['field']} {cond['operator']} %s")
        values.append(cond["value"])

    final_query = base_query + f" {dsl['logic']} ".join(conditions)
    final_query += f" LIMIT {dsl.get('limit',50)}"

    return final_query, values