import re
from typing import Tuple, List, Any, Union

# ==========================================
# 1. FIELD & OPERATOR MAPPERS
# ==========================================

# Maps human-readable DSL names to SQL column names
FIELD_MAP = {
    "pe ratio": "f.pe_ratio",
    "revenue": "f.revenue",
    "sector": "s.sector",
    "market cap": "f.market_cap",
    "price": "s.price",
    "company": "s.company_name",
    "revenue growth": "h.revenue_growth",
    "eps growth": "h.eps_growth"
}

# Maps DSL operators to strict SQL operators
OPERATOR_MAP = {
    "==": "=",
    "!=": "!=",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">="
}

# ==========================================
# 2. PARSER CORE
# ==========================================

def _parse_condition(condition_str: str) -> Tuple[str, str, Any]:
    """
    Parses a single condition string like 'pe ratio < 15' into its components.
    
    Args:
        condition_str (str): The raw string condition.
        
    Returns:
        Tuple[str, str, Any]: A tuple of (mapped_field, sql_operator, parsed_value).
        
    Raises:
        ValueError: If the condition is malformed or uses an invalid operator.
    """
    # Regex to capture: (field) (operator) (value)
    # The (==|!=|<=|>=|<|>) strictly limits us to supported operators
    match = re.search(r'^(.*?)\s*(==|!=|<=|>=|<|>)\s*(.*)$', condition_str.strip())
    
    if not match:
        raise ValueError(f"Invalid condition format: '{condition_str}'")
    
    raw_field = match.group(1).strip().lower()
    raw_op = match.group(2).strip()
    raw_val = match.group(3).strip()
    
    # 1. Map the field securely
    # Fallback auto-replaces spaces with underscores if not in MAP
    # Default to fundamentals table 'f.' if not specified in MAP for fallback
    sql_field = FIELD_MAP.get(raw_field, f"f.{raw_field.replace(' ', '_')}")
    
    # 2. Map the operator
    sql_op = OPERATOR_MAP[raw_op]
    
    # 3. Parse the value dynamically (int, float, or string)
    if raw_val.startswith(('"', "'")) and raw_val.endswith(('"', "'")):
        # It's a quoted string, strip the quotes
        parsed_val = raw_val[1:-1]
    else:
        # Attempt to parse as a number
        try:
            if '.' in raw_val:
                parsed_val = float(raw_val)
            else:
                parsed_val = int(raw_val)
        except ValueError:
            # Fallback to string if casting fails
            parsed_val = raw_val
            
    return sql_field, sql_op, parsed_val


def generate_sql(dsl_input: str, time_filter: dict = None, placeholder: str = "%s") -> Tuple[str, List[Any]]:
    """
    Parses a human-readable DSL string and converts it deterministically 
    into a parameterized SQL string and a companion list of parameters.
    
    Args:
        dsl_input (str): The human-readable string (e.g. "PE ratio < 15 AND sector == 'Tech'")
        time_filter (dict): Example: {"type": "last_m_quarters", "value": 4}
        placeholder (str): The parameter placeholder ('%s' for PostgreSQL, '?' for SQLite3)
        
    Returns:
        Tuple[str, List[Any]]: A tuple containing the parameterized SQL string and the list of parameter values.
    """
    sql_from = "FROM symbols s JOIN fundamentals f ON s.id = f.company_id"
    requires_historical = False
    
    # Check if a time filter is explicitly passed or if we parse historical metrics
    if time_filter is not None or "revenue growth" in dsl_input.lower() or "eps growth" in dsl_input.lower():
        requires_historical = True
        sql_from += " LEFT JOIN historical_metrics h ON s.id = h.company_id"
        
    if not dsl_input or not dsl_input.strip():
        return f"SELECT s.symbol, s.company_name, f.pe_ratio, f.revenue {sql_from}", []
        
    # Split the string by logical operators (AND / OR) while keeping the delimiters
    # Example: ['PE ratio < 15', 'AND', 'revenue > 100000']
    tokens = re.split(r'(?i)\s+(AND|OR)\s+', dsl_input.strip())
    
    sql_clauses = [f"SELECT s.symbol, s.company_name {sql_from} WHERE"]
    params = []
    
    where_exprs = []
    
    for token in tokens:
        upper_token = token.upper()
        
        # If the token is a logical connector, append it to the SQL directly
        if upper_token in ["AND", "OR"]:
            where_exprs.append(upper_token)
            
        # Otherwise, the token is a condition that must be parsed
        else:
            field, sql_op, parsed_val = _parse_condition(token.strip())
            
            # Secure Parameterization implementation: NEVER concatenate `parsed_val`
            where_exprs.append(f"{field} {sql_op} {placeholder}")
            params.append(parsed_val)
            
    if time_filter and time_filter.get("type") == "last_m_quarters":
        m = time_filter.get("value", 4)
        time_sql_condition = f"(h.quarter >= current_date - interval '{m * 3} months' OR h.quarter IS NULL)"
        if where_exprs:
            where_exprs.insert(0, "(")
            where_exprs.append(")")
            where_exprs.append("AND")
        where_exprs.append(time_sql_condition)
        
    sql_clauses.append(" ".join(where_exprs))
    sql_string = " ".join(sql_clauses)
    return sql_string, params

# ==========================================
# 3. EXAMPLE RUNS (Executed when script runs)
# ==========================================
if __name__ == "__main__":
    print("--- DSL TO SECURE SQL COMPILER ---")
    
    example_inputs = [
        "PE ratio < 15",
        "revenue > 1000000",
        'sector == "Tech"',
        "PE ratio < 15 AND revenue > 1000000",
        "sector == 'Healthcare' OR price <= 50.5"
    ]
    
    print("\n[PostgreSQL Format Default (%s)]")
    for dsl in example_inputs:
        sql, p = generate_sql(dsl)
        print(f"Input:  {dsl}")
        print(f"SQL:    {sql}")
        print(f"Params: {p}\n")
        
    print("[SQLite3 Format (?)]")
    sql_lite, p_lite = generate_sql("PE ratio < 15 AND revenue > 1000000", placeholder="?")
    print(f"SQL:    {sql_lite}")
    print(f"Params: {p_lite}")
