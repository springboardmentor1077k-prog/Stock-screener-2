import json
import time
import logging

# Task 2: SQL Compilation Cache
SQL_CACHE = {}
SQL_CACHE_TIMEOUT = 120 # 2 minutes

def get_sql_cache_size():
    return len(SQL_CACHE)

def clear_sql_cache():
    SQL_CACHE.clear()

# Master dictionary for safe SQL column translation
# This completely prevents SQL injection via column names
TABLE_MAPPING = {
    "symbol": ("symbols", "symbol"),
    "company_name": ("symbols", "company_name"),
    "sector": ("symbols", "sector"),
    "pe_ratio": ("fundamentals", "pe_ratio"),
    "revenue": ("fundamentals", "revenue"),
    "ebitda": ("fundamentals", "ebitda"),
    "debt_to_equity": ("fundamentals", "debt_to_equity"),
    "revenue_growth": ("historical_metrics", "revenue_growth"),
    "eps_growth": ("historical_metrics", "eps_growth")
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

    # Validate time_filter if present
    if "time_filter" in dsl_data:
        tf = dsl_data["time_filter"]
        if not isinstance(tf, dict):
            return False, "time_filter must be a dictionary."
        if tf.get("type") != "last_m_quarters":
            return False, "time_filter type must be 'last_m_quarters' for now."
        val = tf.get("value")
        if not isinstance(val, int) or val < 1 or val > 12:
            return False, "time_filter value must be a positive integer between 1 and 12."

    return True, ""


def _validate_condition_tree(node):
    if "conditions" not in node or not isinstance(node["conditions"], list) or len(node["conditions"]) == 0:
        return False, "Node must have a 'conditions' list containing at least one item."
        
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
            
            # Use proper table aliases
            if table == "symbols":
                table_alias = "s"
            elif table == "historical_metrics":
                table_alias = "h"
            else:
                table_alias = "f"
            
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


def compile_sql_from_dsl(dsl_data, default_limit=100, default_page=1):
    """
    Given a validated DSL JSON, deterministicly returns safe SQL and param array.
    
    # =========================================================================
    # PERFORMANCE OPTIMIZATION (Task 2: EXPLAIN ANALYZE)
    # =========================================================================
    # To test the performance characteristics of this dynamically generated query 
    # directly inside PostgreSQL, simply prepend EXPLAIN ANALYZE to the output:
    # 
    # Example:
    # EXPLAIN ANALYZE
    # SELECT s.symbol, s.company_name, s.sector, f.pe_ratio, h.revenue_growth
    # FROM symbols s 
    # JOIN fundamentals f ON s.id = f.company_id 
    # LEFT JOIN historical_metrics h ON s.id = h.company_id 
    # WHERE f.pe_ratio < 15 AND (h.quarter >= current_date - interval '12 months' OR h.quarter IS NULL)
    # ORDER BY f.pe_ratio ASC LIMIT 100 OFFSET 0;
    # =========================================================================
    """
    cache_key = json.dumps(dsl_data, sort_keys=True) # Ensure consistent keying
    now = time.time()
    
    if cache_key in SQL_CACHE:
        timestamp, cached_result = SQL_CACHE[cache_key]
        if now - timestamp < SQL_CACHE_TIMEOUT:
            logging.info("SQL Compiler cache hit")
            return cached_result[0], list(cached_result[1])
        else:
            del SQL_CACHE[cache_key]

    parameters = []
    
    # 1. SELECT Construction
    select_fields = dsl_data.get("select", [])
    
    # Check if we have a time filter
    has_time_filter = "time_filter" in dsl_data
    requires_historical = has_time_filter
    
    # Check if conditions use historical
    if "where" in dsl_data:
        # Simple string check for 'historical_metrics' mapped fields
        def _check_historical_fields(node):
            for cond in node.get("conditions", []):
                if "logic" in cond:
                    if _check_historical_fields(cond): return True
                else:
                    field = cond.get("field")
                    if field in TABLE_MAPPING and TABLE_MAPPING[field][0] == "historical_metrics":
                        return True
            return False
        if _check_historical_fields(dsl_data["where"]):
            requires_historical = True

    if not select_fields:
        # Default projection
        sql_select = "SELECT s.symbol, s.company_name, s.sector, f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity"
        if requires_historical:
            sql_select = "SELECT DISTINCT s.symbol, s.company_name, s.sector, f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity, h.revenue_growth"
    else:
        select_fragments = []
        for field in select_fields:
            table, column = TABLE_MAPPING[field]
            if table == "symbols": alias = "s"
            elif table == "historical_metrics": alias = "h"
            else: alias = "f"
            select_fragments.append(f"{alias}.{column}")
        prefix = "SELECT DISTINCT " if requires_historical else "SELECT "
        sql_select = prefix + ", ".join(select_fragments)
        
    # 2. FROM Construction 
    # Use LEFT JOIN for historical metrics to include companies with missing quarterly data gracefully
    if requires_historical:
        sql_from = "FROM symbols s JOIN fundamentals f ON s.id = f.company_id LEFT JOIN historical_metrics h ON s.id = h.company_id"
    else:
        sql_from = "FROM symbols s JOIN fundamentals f ON s.id = f.company_id"
    
    # 3. WHERE Construction (Recursive)
    sql_where = ""
    where_exprs = []
    
    # Process AST conditions
    if "where" in dsl_data:
        user_where_expr = _compile_condition_tree(dsl_data["where"], parameters)
        if user_where_expr.strip():
            where_exprs.append(f"({user_where_expr})")
            
    # Add time filter condition directly in WHERE clause
    if has_time_filter:
        tf_value = dsl_data["time_filter"]["value"]
        months_to_look_back = tf_value * 3
        
        # Use parameters for interval calculation safely
        time_sql = "(h.quarter >= current_date - (interval '1 month' * %s) OR h.quarter IS NULL)"
        where_exprs.append(time_sql)
        parameters.append(months_to_look_back)
        
    if where_exprs:
        sql_where = "WHERE " + " AND ".join(where_exprs)
            
    # 4. ORDER BY Construction
    sql_order = ""
    order_by_list = dsl_data.get("order_by", [])
    if order_by_list:
        order_frags = []
        for ob in order_by_list:
            if ob["field"] in TABLE_MAPPING:
                table, col = TABLE_MAPPING[ob["field"]]
                if table == "symbols": alias = "s"
                elif table == "historical_metrics": alias = "h"
                else: alias = "f"
                direction = "DESC" if str(ob.get("direction", "ASC")).upper() == "DESC" else "ASC"
                order_frags.append(f"{alias}.{col} {direction}")
        if order_frags:
            sql_order = "ORDER BY " + ", ".join(order_frags)
            
    # 5. Pagination
    limit = int(dsl_data.get("limit", default_limit))
    
    # Task 2: Make sure all queries never return more than 100 rows by default
    if limit > 100:
        limit = 100
        
    page = int(dsl_data.get("page", default_page))
    offset = (page - 1) * limit
    
    sql_limit = "LIMIT %s OFFSET %s"
    parameters.extend([limit, offset])
    
    # Task 1: SAFE: parameterized query - no injection risk (Stitched from validated fragments)
    final_sql = f"{sql_select} {sql_from} {sql_where} {sql_order} {sql_limit}".strip()
    
    # Fix extraneous spaces
    final_sql = " ".join(final_sql.split())
    
    result = (final_sql, parameters)
    SQL_CACHE[cache_key] = (time.time(), result)
    return result[0], list(result[1])

