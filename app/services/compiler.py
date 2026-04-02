# app/services/compiler.py
from typing import Dict, Tuple, Any, List
import logging

logger = logging.getLogger(__name__)

FIELD_TABLE_MAP = {
    "sector": ("s", "sector", "symbols", False),
    "pe_ratio": ("f", "pe_ratio", "fundamentals", True),
    "peg_ratio": ("f", "peg_ratio", "fundamentals", True),
    "debt_fcf": ("f", "debt_fcf", "fundamentals", True),
    "promoter_holding": ("f", "promoter_holding", "fundamentals", True),
    "revenue": ("f", "revenue", "fundamentals", True),  # Revenue is in fundamentals
    "ebitda": ("f", "ebitda", "fundamentals", True)     # EBITDA is in fundamentals
}

def compile_dsl_to_sql(dsl) -> Tuple[str, Dict[str, Any]]:
    """
    Compile DSL to SQL query
    
    Args:
        dsl: DSL object with conditions, logic, and limit
        
    Returns:
        Tuple of (sql_query, parameters)
    """
    
    # Determine which tables are needed
    needs_fundamentals = False
    needs_historic = False
    
    for cond in dsl.conditions:
        if cond.field in FIELD_TABLE_MAP:
            _, _, _, requires_join = FIELD_TABLE_MAP[cond.field]
            if requires_join:
                if cond.field in ["revenue", "ebitda"]:
                    needs_historic = True
                else:
                    needs_fundamentals = True
    
    # Build SELECT clause - only needed columns
    select_columns = ["s.symbol", "s.company_name"]
    
    # Check if we need sector in SELECT
    if any(cond.field == "sector" for cond in dsl.conditions):
        select_columns.append("s.sector")
    
    # Check if we need PE ratio in SELECT
    if any(cond.field == "pe_ratio" for cond in dsl.conditions):
        select_columns.append("f.pe_ratio")
    
    # Check if we need revenue in SELECT
    if any(cond.field == "revenue" for cond in dsl.conditions):
        select_columns.append("f.revenue")
    
    select_clause = "SELECT " + ", ".join(select_columns)
    
    # Build FROM clause
    from_clause = "FROM symbols s"
    
    # Add JOINs only if needed
    if needs_fundamentals:
        from_clause += "\nINNER JOIN fundamentals f ON s.id = f.company_id"
    
    # Build WHERE clause
    where_clauses = []
    params = {}
    
    for i, cond in enumerate(dsl.conditions):
        if cond.field not in FIELD_TABLE_MAP:
            raise ValueError(f"Unknown field: {cond.field}")
        
        table_alias, column, _, _ = FIELD_TABLE_MAP[cond.field]
        param_key = f"param_{i}"
        
        where_clauses.append(f"{table_alias}.{column} {cond.operator} :{param_key}")
        params[param_key] = cond.value
    
    # Build the final query
    query = f"{select_clause}\n{from_clause}"
    
    if where_clauses:
        where_str = f" {dsl.logic} ".join(where_clauses)
        query += f"\nWHERE {where_str}"
    
    # Add LIMIT
    query += f"\nLIMIT :limit"
    params["limit"] = dsl.limit
    
    # Log the query for debugging
    logger.info(f"Generated SQL: {query}")
    logger.info(f"Parameters: {params}")
    
    return query, params