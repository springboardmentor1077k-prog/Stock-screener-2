def build_safe_query(dsl: dict):

    entity = dsl["entity"]


    
    if entity == "fundamentals":

        base_query = "SELECT * FROM fundamentals WHERE "
        values = []
        conditions_sql = []

        for cond in dsl["conditions"]:
            field = cond["field"]
            operator = cond["operator"]
            value = cond["value"]

            conditions_sql.append(f"{field} {operator} %s")
            values.append(value)

        logic = dsl.get("logic", "AND")
        where_clause = f" {logic} ".join(conditions_sql)

        sql = base_query + where_clause

        if "limit" in dsl:
            sql += " LIMIT %s"
            values.append(dsl["limit"])

        return sql, values


    
   
    
    elif entity == "historical_metrics":

        metric = dsl["metric"]
        period = dsl["period"]
        direction = dsl["direction"]

        operator = ">" if direction == "increase" else "<"

        sql = f"""
        SELECT symbol_id
        FROM (
            SELECT symbol_id,
                   {metric},
                   LAG({metric}) OVER (
                       PARTITION BY symbol_id
                       ORDER BY financial_year, quarter
                   ) AS prev_value
            FROM historical_metrics
        ) t
        WHERE prev_value IS NOT NULL
          AND {metric} {operator} prev_value
        GROUP BY symbol_id
        HAVING COUNT(*) >= %s
        """

        values = [period - 1]

        return sql, values


    else:
        raise Exception("Unsupported entity in SQL builder")