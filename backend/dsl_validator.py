FIELD_RANGES = {
    "pe": (0, 1500),
    "peg": (0, 100),
    "promoter_holding": (0, 100),
    "ebitda": (-1_000_000_000_000, 1_000_000_000_000),
    "debt_free_cash": (-1_000_000_000_000, 1_000_000_000_000)
}

ALLOWED_ENTITIES = [
    "symbol",
    "fundamentals",
    "historical_metrics",
    "portfolio",
    "alert"
]

ALLOWED_FIELDS = [
    "pe",
    "peg",
    "promoter_holding",
    "ebitda",
    "debt_free_cash",
    "created_on"
]

ALLOWED_OPERATORS = ["=", "!=", ">", "<", ">=", "<="]
ALLOWED_LOGIC = ["AND", "OR"]

MAX_LIMIT = 200


def validate_dsl(dsl: dict):
    """
    Validates DSL strictly.
    Returns None if valid.
    Returns structured error dict if invalid.
    """

    # ---------- Basic Structure ----------
    if not isinstance(dsl, dict):
        return error("INVALID_STRUCTURE", "DSL must be a JSON object")

    # ---------- Entity ----------
    entity = dsl.get("entity")
    if not entity:
        return error("MISSING_ENTITY", "Entity is required")

    entity = str(entity).lower()
    if entity not in ALLOWED_ENTITIES:
        return error("INVALID_ENTITY", f"Unsupported entity: {entity}")

    # ---------- Conditions ----------
    conditions = dsl.get("conditions")
    if not isinstance(conditions, list) or len(conditions) == 0:
        return error("INVALID_CONDITIONS", "Conditions must be a non-empty list")

    # ---------- Logic ----------
    logic = str(dsl.get("logic", "")).upper()
    if logic not in ALLOWED_LOGIC:
        return error("INVALID_LOGIC", f"Unsupported logic: {logic}")

    # ---------- Validate Each Condition ----------
    for cond in conditions:

        if not isinstance(cond, dict):
            return error("INVALID_CONDITION_FORMAT", "Each condition must be an object")

        # Field
        field = str(cond.get("field", "")).lower()
        if field not in ALLOWED_FIELDS:
            return error("INVALID_FIELD", f"Unsupported metric: {field}")

        # Operator
        operator = cond.get("operator")
        if operator not in ALLOWED_OPERATORS:
            return error("INVALID_OPERATOR", f"Unsupported operator: {operator}")

        # Value
        value = cond.get("value")
        if not isinstance(value, (int, float)):
            return error("INVALID_VALUE_TYPE", "Value must be numeric")

        # ---------- Range Validation ----------
        if field in FIELD_RANGES:
            min_val, max_val = FIELD_RANGES[field]

            if value < min_val or value > max_val:

                suggestion = None

                if value > max_val:
                    suggestion = f"Try a value less than or equal to {max_val}."
                elif value < min_val:
                    suggestion = f"Try a value greater than or equal to {min_val}."

                return {
                    "status": "error",
                    "code": "VALUE_OUT_OF_RANGE",
                    "message": f"{field.upper()} must be between {min_val} and {max_val}.",
                    "suggestion": suggestion
                }

    # ---------- Limit ----------
    if "limit" in dsl:
        limit = dsl["limit"]

        if not isinstance(limit, int):
            return error("INVALID_LIMIT_TYPE", "Limit must be integer")

        if limit <= 0 or limit > MAX_LIMIT:
            return error(
                "INVALID_LIMIT_RANGE",
                f"Limit must be between 1 and {MAX_LIMIT}"
            )

    return None


def error(code: str, message: str):
    return {
        "status": "error",
        "code": code,
        "message": message
    }