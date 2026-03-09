# SQL Compiler
# Converts DSL JSON into safe SQL query + parameters

FIELD_MAPPING = {
    "symbol": ("symbols", "s.symbol"),
    "company_name": ("symbols", "s.company_name"),
    "sector": ("symbols", "s.sector"),
    "pe_ratio": ("fundamentals", "f.pe_ratio"),
    "revenue": ("fundamentals", "f.revenue")
}


def compile_dsl_to_sql(dsl: dict):

    base_query = """
    SELECT s.symbol, s.company_name
    FROM symbols s
    JOIN fundamentals f ON s.id = f.company_id
    """

    filters = dsl.get("filters", [])
    logic = dsl.get("logic", "AND")

    where_clauses = []
    params = []

    for f in filters:

        field = f["field"]
        operator = f["operator"]
        value = f["value"]

        # normalize sector values
        if field == "sector" and isinstance(value, str):
            value = value.capitalize()

        if field not in FIELD_MAPPING:
            raise ValueError(f"Unsupported field: {field}")

        table, column = FIELD_MAPPING[field]

        where_clauses.append(f"{column} {operator} %s")
        params.append(value)

    if where_clauses:
        where_sql = " WHERE " + f" {logic} ".join(where_clauses)
    else:
        where_sql = ""

    sql_query = base_query + where_sql

    return sql_query, params