# app/dsl_validator.py

ALLOWED_FIELDS = ["pe_ratio", "market_cap", "price", "volume"]
ALLOWED_OPERATORS = ["<", ">", "=", "<=", ">="]

def validate_dsl(dsl: dict):

    if "filters" not in dsl:
        raise Exception("Invalid DSL: missing filters")

    for f in dsl["filters"]:

        if f["field"] not in ALLOWED_FIELDS:
            raise Exception(f"Invalid field: {f['field']}")

        if f["operator"] not in ALLOWED_OPERATORS:
            raise Exception(f"Invalid operator: {f['operator']}")

        if not isinstance(f["value"], (int, float)):
            raise Exception("Invalid value type")

    if dsl.get("limit", 0) > 100:
        raise Exception("Limit too large")