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

def validate_dsl(dsl):

    if dsl["entity"] not in ALLOWED_ENTITIES:
        return "INVALID_ENTITY"

    if dsl["logic"] not in ALLOWED_LOGIC:
        return "INVALID_LOGIC"

    for cond in dsl["conditions"]:

        if cond["field"] not in ALLOWED_FIELDS:
            return "INVALID_FIELD"

        if cond["operator"] not in ALLOWED_OPERATORS:
            return "INVALID_OPERATOR"

        if not isinstance(cond["value"], (int, float)):
            return "INVALID_VALUE_TYPE"

    return None