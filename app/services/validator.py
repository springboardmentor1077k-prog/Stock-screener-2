ALLOWED_FIELDS = {
    "sector",
    "pe_ratio",
    "peg_ratio",
    "debt_fcf",
    "promoter_holding",
    "revenue",
    "ebitda"
}

def validate_fields(dsl):
    for cond in dsl.conditions:
        if cond.field not in ALLOWED_FIELDS:
            raise ValueError(f"Unsupported field: {cond.field}")