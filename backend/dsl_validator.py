FIELD_RANGES = {
    "pe": (0, 1500),
    "peg": (0, 100),
    "promoter_holding": (0, 100),
    "ebitda": (-1_000_000_000_000, 1_000_000_000_000),
    "debt_free_cash": (-1_000_000_000_000, 1_000_000_000_000),
    "revenue": (-1_000_000_000_000, 1_000_000_000_000),
    "net_profit": (-1_000_000_000_000, 1_000_000_000_000),
}


ALL_FIELDS = list(FIELD_RANGES.keys())

ALLOWED_ENTITIES = [
    "symbol",
    "fundamentals",
    "historical_metrics",
    "portfolio",
    "alert"
]

FUNDAMENTAL_FIELDS = [
    "pe",
    "peg",
    "promoter_holding",
    "ebitda",
    "debt_free_cash"
      
]

HISTORICAL_FIELDS = [
    "revenue",
    "ebitda",
    "net_profit",
    "debt_free_cash",
    "pe"
]

ALLOWED_OPERATORS = ["=", "!=", ">", "<", ">=", "<="]
ALLOWED_LOGIC = ["AND", "OR"]
ALLOWED_DIRECTIONS = ["increase", "decrease"]

MAX_LIMIT = 200

#Recursive condition
def validate_conditions(node, allowed_fields):

    logic = str(node.get("logic", "AND")).upper()
    if logic not in ALLOWED_LOGIC:
        return error("INVALID_LOGIC", f"Unsupported logic: {logic}")

    conditions = node.get("conditions")
    if not isinstance(conditions, list) or len(conditions) == 0:
        return error("INVALID_CONDITIONS", "Conditions must be a non-empty list")

    for cond in conditions:

        # Nested block
        if "conditions" in cond:
            nested_error = validate_conditions(cond, allowed_fields)
            if nested_error:
                return nested_error
            continue

        field = str(cond.get("field", "")).lower()
        operator = cond.get("operator")
        value = cond.get("value")

        if field not in allowed_fields:
            return error("INVALID_FIELD", f"{field} not allowed")

        if operator not in ALLOWED_OPERATORS:
            return error("INVALID_OPERATOR", f"Unsupported operator: {operator}")

        if not isinstance(value, (int, float)):
            return error("INVALID_VALUE_TYPE", "Value must be numeric")

        if field in FIELD_RANGES:
            min_val, max_val = FIELD_RANGES[field]
            if value < min_val or value > max_val:
                return range_error(field, min_val, max_val, value)

    return None



def validate_dsl(dsl: dict):

    if not isinstance(dsl, dict):
        return error("INVALID_STRUCTURE", "DSL must be a JSON object")

    entity = dsl.get("entity")
    if not entity:
        return error("MISSING_ENTITY", "Entity is required")

    entity = str(entity).lower()

    if entity not in ALLOWED_ENTITIES:
        return error("INVALID_ENTITY", f"Unsupported entity: {entity}")


    # FUNDAMENTALS MODE

    if entity == "fundamentals":
        return validate_conditions(dsl, FUNDAMENTAL_FIELDS)


    # SYMBOL MODE (MIXED TABLES)

    elif entity == "symbol":
        return validate_conditions(dsl, ALL_FIELDS)


    # HISTORICAL GROWTH MODE

    elif entity == "historical_metrics":

        analysis = dsl.get("analysis")
        if analysis != "growth":
            return error(
                "INVALID_ANALYSIS",
                "Enter only financial metrics"
            )

        metric = dsl.get("metric")
        if metric not in HISTORICAL_FIELDS:
            return error(
                "INVALID_METRIC",
                f"{metric} not allowed"
            )

        period = dsl.get("period")
        if not isinstance(period, int) or period <= 0:
            return error(
                "INVALID_PERIOD",
                "Period must be a positive integer"
            )

        direction = dsl.get("direction")
        if direction not in ALLOWED_DIRECTIONS:
            return error(
                "INVALID_DIRECTION",
                "Direction must be increase or decrease"
            )
            
    # LIMIT VALIDATION

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

def range_error(field, min_val, max_val, value):

    if value > max_val:
        suggestion = f"Try a value ≤ {max_val}"
    else:
        suggestion = f"Try a value ≥ {min_val}"

    return {
        "status": "error",
        "code": "VALUE_OUT_OF_RANGE",
        "message": f"{field.upper()} must be between {min_val} and {max_val}",
        "suggestion": suggestion
    }


def error(code: str, message: str):
    return {
        "status": "error",
        "code": code,
        "message": message
    }