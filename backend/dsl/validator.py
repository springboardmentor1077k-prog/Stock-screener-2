ALLOWED_FIELDS = {
    "sector",
    "pe_ratio",
    "revenue",
    "symbol"
}

ALLOWED_OPERATORS = {
    "=",
    "<",
    ">",
    "<=",
    ">="
}

ALLOWED_LOGIC = {
    "AND",
    "OR"
}


def validate_dsl(dsl: dict):

    if "filters" not in dsl:
        raise ValueError("DSL missing filters")

    if "logic" not in dsl:
        raise ValueError("DSL missing logic")

    if dsl["logic"] not in ALLOWED_LOGIC:
        raise ValueError("Invalid logic operator")

    for f in dsl["filters"]:

        field = f.get("field")
        operator = f.get("operator")

        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: {field}")

        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator: {operator}")