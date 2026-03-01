# backend/dsl_validator.py

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
    if "entity" not in dsl:
        return error("MISSING_ENTITY", "Entity is required")

    entity = str(dsl["entity"]).lower()

    if entity not in ALLOWED_ENTITIES:
        return error("INVALID_ENTITY", f"Unsupported entity: {entity}")

    # ---------- Conditions ----------
    if "conditions" not in dsl:
        return error("MISSING_CONDITIONS", "Conditions are required")

    if not isinstance(dsl["conditions"], list) or len(dsl["conditions"]) == 0:
        return error("INVALID_CONDITIONS", "Conditions must be a non-empty list")

    # ---------- Logic ----------
    if "logic" not in dsl:
        return error("MISSING_LOGIC", "Logical operator is required")

    logic = str(dsl["logic"]).upper()

    if logic not in ALLOWED_LOGIC:
        return error("INVALID_LOGIC", f"Unsupported logic: {logic}")

    # ---------- Validate Each Condition ----------
    for cond in dsl["conditions"]:

        if not isinstance(cond, dict):
            return error("INVALID_CONDITION_FORMAT", "Each condition must be an object")

        # Field
        if "field" not in cond:
            return error("MISSING_FIELD", "Condition missing field")

        field = str(cond["field"]).lower()

        if field not in ALLOWED_FIELDS:
            return error("INVALID_FIELD", f"Unsupported metric: {field}")

        # Operator
        if "operator" not in cond:
            return error("MISSING_OPERATOR", "Condition missing operator")

        operator = cond["operator"]

        if operator not in ALLOWED_OPERATORS:
            return error("INVALID_OPERATOR", f"Unsupported operator: {operator}")

        # Value
        if "value" not in cond:
            return error("MISSING_VALUE", "Condition missing value")

        value = cond["value"]

        if not isinstance(value, (int, float)):
            return error("INVALID_VALUE_TYPE", "Value must be numeric")

    # ---------- Limit ----------
    if "limit" in dsl:
        limit = dsl["limit"]

        if not isinstance(limit, int):
            return error("INVALID_LIMIT_TYPE", "Limit must be integer")

        if limit <= 0 or limit > MAX_LIMIT:
            return error("INVALID_LIMIT_RANGE", f"Limit must be between 1 and {MAX_LIMIT}")

    return None


def error(code: str, message: str):
    return {
        "status": "error",
        "code": code,
        "message": message
    }