ALLOWED_FIELDS = [
    "pe_ratio",
    "sector",
    "revenue"
]

ALLOWED_OPERATORS = [
    "<",
    ">",
    "=",
    "<=",
    ">="
]


def validate_dsl(dsl):

    for cond in dsl.conditions:

        if cond.field not in ALLOWED_FIELDS:
            raise ValueError("Invalid field")

        if cond.operator not in ALLOWED_OPERATORS:
            raise ValueError("Invalid operator")

    return True
