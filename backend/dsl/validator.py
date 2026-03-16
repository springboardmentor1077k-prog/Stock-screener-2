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

ALLOWED_TIME_TYPES = {
    "quarter"
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

    # -------------------------
    # TIME FILTER VALIDATION
    # -------------------------

    if "time_filter" in dsl:

        tf = dsl["time_filter"]

        if "type" not in tf or "value" not in tf:
            raise ValueError("Invalid time_filter structure")

        if tf["type"] not in ALLOWED_TIME_TYPES:
            raise ValueError("Unsupported time filter type")

        # Validate quarter format
        if tf["type"] == "quarter":

            if "-Q" not in tf["value"]:
                raise ValueError("Quarter must be in format YYYY-QX")

            year, quarter = tf["value"].split("-Q")

            if not year.isdigit():
                raise ValueError("Invalid year in quarter")

            if quarter not in {"1", "2", "3", "4"}:
                raise ValueError("Quarter must be 1,2,3 or 4")