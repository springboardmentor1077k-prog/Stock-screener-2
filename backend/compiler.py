import json

# Master dictionary for safe SQL column translation
# This completely prevents SQL injection via column names
TABLE_MAPPING = {
    "symbol": ("symbols", "symbol"),
    "company_name": ("symbols", "company_name"),
    "sector": ("symbols", "sector"),
    "pe_ratio": ("fundamentals", "pe_ratio"),
    "revenue": ("fundamentals", "revenue"),
    "ebitda": ("fundamentals", "ebitda"),
    "debt_to_equity": ("fundamentals", "debt_to_equity")
}

# Supported operators mapped directly to PostgreSQL equivalents
OPERATOR_MAP = {
    "=": "=",
    "!=": "!=",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
    "IN": "IN",
    "NOT IN": "NOT IN",
    "LIKE": "LIKE",
    "ILIKE": "ILIKE",
    "IS NULL": "IS NULL",
    "IS NOT NULL": "IS NOT NULL"
}

def validate_dsl(dsl_data):
    """
    Validates DSL rigidly. Cannot be bypassed.
    Returns (True, "") if OK, else (False, error).
    """
    if not isinstance(dsl_data, dict):
        return False, "DSL must be a dictionary."

    # Validate condition tree if present
    if "where" in dsl_data:
        v_ok, v_err = _validate_condition_tree(dsl_data["where"])
        if not v_ok:
            return False, v_err
            
    # Validate select projections if present
    if "select" in dsl_data:
        if not isinstance(dsl_data["select"], list):
            return False, "'select' must be a list of fields."
        for field in dsl_data["select"]:
            if field not in TABLE_MAPPING:
                return False, f"Invalid select field: {field}"

    return True, ""


def _validate_condition_tree(node):
    if "conditions" not in node or not isinstance(node["conditions"], list):
        return False, "Node must have a 'conditions' list."
        
    for cond in node["conditions"]:
        if "logic" in cond: # Nested branch
            ok, err = _validate_condition_tree(cond)
            if not ok: return False, err
        else: # Leaf condition
            field = cond.get("field")
            op = cond.get("operator")
            val = cond.get("value")
            
            if field not in TABLE_MAPPING:
                return False, f"Unknown field: {field}"
            if str(op).upper() not in OPERATOR_MAP:
                return False, f"Invalid operator: {op}"
                
            # IN / NOT IN require arrays
            if str(op).upper() in ["IN", "NOT IN"] and not isinstance(val, list):
                return False, f"Operator {op} requires a list of values."
                
    return True, ""


def _compile_condition_tree(node, parameters):
    """Recursively processes a node in the AST into SQL + appended params."""
    logic = node.get("logic", "AND").upper()
    if logic not in ["AND", "OR"]:
        logic = "AND"
        
    clauses = []
    for cond in node.get("conditions", []):
        if "logic" in cond:
            # Recursively descend into nested logic
            sub_sql = _compile_condition_tree(cond, parameters)
            if sub_sql.strip():
                clauses.append(f"({sub_sql})")
        else:
            # Base leaf
            field = cond["field"]
            table, column = TABLE_MAPPING[field]
            table_alias = "s" if table == "symbols" else "f"
            
            operator = str(cond["operator"]).upper()
            sql_op = OPERATOR_MAP[operator]
            val = cond.get("value")
            
            col_ref = f"{table_alias}.{column}"
            
            if sql_op in ["IS NULL", "IS NOT NULL"]:
                clauses.append(f"{col_ref} {sql_op}")
            elif sql_op in ["IN", "NOT IN"]:
                # psycopg2 supports %s with tuple for IN clauses
                clauses.append(f"{col_ref} {sql_op} %s")
                parameters.append(tuple(val))
            else:
                clauses.append(f"{col_ref} {sql_op} %s")
                parameters.append(val)
                
    if not clauses:
        return ""
        
    return f" {logic} ".join(clauses)


def compile_sql_from_dsl(dsl_data, default_limit=10, default_page=1):
    """
    Given a validated DSL JSON, deterministicly returns safe SQL and param array.
    """
    parameters = []
    
    # 1. SELECT Construction
    select_fields = dsl_data.get("select", [])
    if not select_fields:
        # Default projection
        sql_select = "SELECT s.symbol, s.company_name, s.sector, f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity"
    else:
        select_fragments = []
        for field in select_fields:
            table, column = TABLE_MAPPING[field]
            alias = "s" if table == "symbols" else "f"
            select_fragments.append(f"{alias}.{column}")
        sql_select = "SELECT " + ", ".join(select_fragments)
        
    # 2. FROM Construction (Always join base relation securely)
    sql_from = "FROM symbols s JOIN fundamentals f ON s.id = f.company_id"
    
    # 3. WHERE Construction (Recursive)
    sql_where = ""
    if "where" in dsl_data:
        where_expr = _compile_condition_tree(dsl_data["where"], parameters)
        if where_expr.strip():
            sql_where = f"WHERE {where_expr}"
            
    # 4. ORDER BY Construction
    sql_order = ""
    order_by_list = dsl_data.get("order_by", [])
    if order_by_list:
        order_frags = []
        for ob in order_by_list:
            if ob["field"] in TABLE_MAPPING:
                table, col = TABLE_MAPPING[ob["field"]]
                alias = "s" if table == "symbols" else "f"
                direction = "DESC" if str(ob.get("direction", "ASC")).upper() == "DESC" else "ASC"
                order_frags.append(f"{alias}.{col} {direction}")
        if order_frags:
            sql_order = "ORDER BY " + ", ".join(order_frags)
            
    # 5. Pagination
    limit = int(dsl_data.get("limit", default_limit))
    page = int(dsl_data.get("page", default_page))
    offset = (page - 1) * limit
    
    sql_limit = "LIMIT %s OFFSET %s"
    parameters.extend([limit, offset])
    
    # Stitch Final SQL safely
    final_sql = f"{sql_select} {sql_from} {sql_where} {sql_order} {sql_limit}".strip()
    
    # Fix extraneous spaces
    final_sql = " ".join(final_sql.split())
    
    return final_sql, parameters

