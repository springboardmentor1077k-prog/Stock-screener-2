ALLOWED_FIELDS = {"pe_ratio", "market_cap", "sector", "price", "volume"}
ALLOWED_OPERATORS = {">", "<", ">=", "<=", "="}
ALLOWED_ORDER = {"asc", "desc"}

def validate_dsl(dsl: dict):
    if "filters" not in dsl:
        raise ValueError("Missing filters")

    for f in dsl["filters"]:
        if f["field"] not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: {f['field']}")

        if f["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator: {f['operator']}")

    if dsl.get("order") not in ALLOWED_ORDER:
        raise ValueError("Invalid sort order")

    if not isinstance(dsl.get("limit"), int) or dsl["limit"] > 100:
        raise ValueError("Limit must be integer <= 100")

    return True