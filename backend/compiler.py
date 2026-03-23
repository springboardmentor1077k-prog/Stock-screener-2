import json

# Allowed fields exactly as dictated by prompt
ALLOWED_FIELDS = ["pe_ratio", "revenue", "ebitda", "debt_to_equity"]
ALLOWED_OPERATORS = ["=", "!=", "<", "<=", ">", ">="]

TABLE_MAPPING = {
    "pe_ratio": ("fundamentals", "pe_ratio"),
    "revenue": ("fundamentals", "revenue"),
    "ebitda": ("fundamentals", "ebitda"),
    "debt_to_equity": ("fundamentals", "debt_to_equity")
}

def validate_dsl(dsl_data):
    """
    Takes parsed JSON DSL and validates it strictly to prevent injection and errors.
    Returns (True, "") if valid, (False, "reason") if invalid.
    """
    if "conditions" not in dsl_data or not isinstance(dsl_data["conditions"], list):
        return False, "DSL must contain a 'conditions' array"
        
    if len(dsl_data["conditions"]) == 0:
        return False, "Conditions array cannot be empty"
        
    for condition in dsl_data["conditions"]:
        field = condition.get("field")
        op = condition.get("operator")
        val = condition.get("value")
        
        if field not in ALLOWED_FIELDS:
            return False, f"Invalid field used: {field}. Allowed: {ALLOWED_FIELDS}"
            
        if op not in ALLOWED_OPERATORS:
            return False, f"Invalid operator: {op}. Allowed: {ALLOWED_OPERATORS}"
            
        if not isinstance(val, (int, float)):
            return False, f"Invalid value type for {field}, must be number."

    return True, ""


def compile_sql_from_dsl(dsl_data, sort_by="pe_ratio", sort_order="asc", limit=10, page=1):
    """
    Takes VALIDATED DSL and returns (safe_sql_string, parameters_list)
    """
    conditions_list = dsl_data.get("conditions", [])
    logic_operator = dsl_data.get("logic", "AND").upper()
    
    if logic_operator not in ["AND", "OR"]:
        logic_operator = "AND"
        
    # Base parameterized query joining symbols and fundamentals
    sql_base = """
        SELECT s.symbol, s.company_name, s.sector, f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity
        FROM symbols s
        JOIN fundamentals f ON s.id = f.company_id
        WHERE 
    """
    
    where_clauses = []
    parameters = []
    
    for cond in conditions_list:
        table_name, col_name = TABLE_MAPPING[cond["field"]]
        operator = cond["operator"]
        value = cond["value"]
        
        # using strictly %s as placeholder parameter for database safety
        where_clauses.append(f"f.{col_name} {operator} %s")
        parameters.append(value)
        
    if not where_clauses:
        final_sql = sql_base + " 1=1 "
    else:
        final_sql = sql_base + f" {logic_operator} ".join(where_clauses)
    
    # Optional sorting and pagination
    if sort_by not in ALLOWED_FIELDS:
        sort_by = "pe_ratio"
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "asc"
        
    _, sort_col = TABLE_MAPPING[sort_by]
    offset = (page - 1) * limit
    
    final_sql += f" ORDER BY f.{sort_col} {sort_order.upper()} LIMIT %s OFFSET %s"
    parameters.extend([limit, offset])
        
    return final_sql, parameters
