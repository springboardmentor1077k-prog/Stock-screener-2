from backend.dsl.schema import ALLOWED_FIELDS, ALLOWED_OPERATORS, ALLOWED_LOGIC


def validate_dsl(dsl: dict):

    if "filters" not in dsl:
        raise ValueError("DSL must contain filters")

    for f in dsl["filters"]:

        field = f.get("field")
        operator = f.get("operator")
        value = f.get("value")

        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Unsupported field: {field}")

        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")

        if value is None:
            raise ValueError("Filter value cannot be empty")

    logic = dsl.get("logic", "AND")

    if logic not in ALLOWED_LOGIC:
        raise ValueError("Invalid logic operator")