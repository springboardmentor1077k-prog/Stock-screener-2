# app/services/compiler.py
import re
from typing import Dict, List, Tuple, Any

FIELD_TABLE_MAP = {
    "sector": ("s", "sector", "symbols", False),
    "pe_ratio": ("f", "pe_ratio", "fundamentals", True),
    "peg_ratio": ("f", "peg_ratio", "fundamentals", True),
    "debt_fcf": ("f", "debt_fcf", "fundamentals", True),
    "promoter_holding": ("f", "promoter_holding", "fundamentals", True),
    "revenue": ("h", "revenue", "historic_metrics", True),
    "ebitda": ("h", "ebitda", "historic_metrics", True)
}

# Time range to quarter count mapping
TIME_RANGE_QUARTERS = {
    "last_quarter": 1,
    "last_4_quarters": 4,
    "last_8_quarters": 8,
    "last_12_quarters": 12
}

def get_quarter_date_filter(quarters: int) -> str:
    """Generate SQL filter for last N quarters"""
    return f"""
        h.quarter >= date(
            'now', 
            '-' || (CAST(strftime('%m', 'now') AS INTEGER) % 3 + 3 * ({quarters} - 1)) || ' months'
        )
    """

def compile_dsl_to_sql(dsl) -> Tuple[str, Dict[str, Any]]:
    """
    Compile DSL to SQL with support for:
    - Regular conditions
    - Time filters
    - Growth calculations using window functions
    - Trend analysis
    """
    
    # Track which tables need to be joined
    joins_needed = {
        "fundamentals": False,
        "historic_metrics": False
    }
    
    # Check if we need growth calculations
    needs_growth = len(dsl.get_growth_conditions()) > 0 or len(dsl.get_trend_conditions()) > 0
    
    # Determine time range for growth analysis
    time_range = dsl.time_filter.range if dsl.time_filter else "last_4_quarters"
    num_quarters = TIME_RANGE_QUARTERS.get(time_range, 4)
    
    # Base query with Common Table Expression (CTE) for quarterly data with window functions
    if needs_growth:
        query = f"""
        WITH quarterly_data AS (
            SELECT 
                s.id,
                s.symbol,
                s.company_name,
                s.sector,
                h.quarter,
                h.revenue,
                h.ebitda,
                h.net_profit,
                -- Window functions for growth calculation
                LAG(h.revenue, 1) OVER (PARTITION BY s.id ORDER BY h.quarter) as prev_revenue,
                LAG(h.revenue, 4) OVER (PARTITION BY s.id ORDER BY h.quarter) as prev_year_revenue,
                LAG(h.ebitda, 1) OVER (PARTITION BY s.id ORDER BY h.quarter) as prev_ebitda,
                LAG(h.net_profit, 1) OVER (PARTITION BY s.id ORDER BY h.quarter) as prev_profit,
                -- Quarter-over-Quarter growth
                CASE 
                    WHEN LAG(h.revenue, 1) OVER (PARTITION BY s.id ORDER BY h.quarter) > 0 
                    THEN (h.revenue - LAG(h.revenue, 1) OVER (PARTITION BY s.id ORDER BY h.quarter)) / 
                         LAG(h.revenue, 1) OVER (PARTITION BY s.id ORDER BY h.quarter) * 100
                    ELSE NULL
                END as qoq_revenue_growth,
                -- Year-over-Year growth
                CASE 
                    WHEN LAG(h.revenue, 4) OVER (PARTITION BY s.id ORDER BY h.quarter) > 0 
                    THEN (h.revenue - LAG(h.revenue, 4) OVER (PARTITION BY s.id ORDER BY h.quarter)) / 
                         LAG(h.revenue, 4) OVER (PARTITION BY s.id ORDER BY h.quarter) * 100
                    ELSE NULL
                END as yoy_revenue_growth,
                -- Running averages
                AVG(h.revenue) OVER (
                    PARTITION BY s.id 
                    ORDER BY h.quarter 
                    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
                ) as avg_revenue_4q,
                -- Trend detection (linear regression simplified)
                ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY h.quarter) as rn,
                COUNT(*) OVER (PARTITION BY s.id) as total_quarters
            FROM symbols s
            JOIN historic_metrics h ON s.id = h.company_id
            WHERE {get_quarter_date_filter(num_quarters)}
        ),
        """
    else:
        query = """
        SELECT DISTINCT s.symbol, s.company_name
        FROM symbols s
        """
    
    # Add JOINs for fundamentals if needed
    for cond in dsl.get_regular_conditions():
        if cond.field in FIELD_TABLE_MAP:
            _, _, table_name, requires_join = FIELD_TABLE_MAP[cond.field]
            if requires_join and table_name in joins_needed:
                joins_needed[table_name] = True
    
    if needs_growth:
        # We already have historic_metrics in CTE
        joins_needed["historic_metrics"] = False
    
    # Build JOIN clauses for regular conditions
    joins = []
    if joins_needed["fundamentals"]:
        joins.append("JOIN fundamentals f ON s.id = f.company_id")
    
    # Build WHERE clauses for regular conditions
    where_clauses = []
    params = {}
    param_counter = 0
    
    # Process regular conditions
    for idx, cond in enumerate(dsl.get_regular_conditions()):
        if cond.field in FIELD_TABLE_MAP:
            table_alias, column, _, _ = FIELD_TABLE_MAP[cond.field]
            param_key = f"value_{param_counter}"
            where_clauses.append(f"{table_alias}.{column} {cond.operator} :{param_key}")
            params[param_key] = cond.value
            param_counter += 1
    
    # Process growth conditions
    growth_having_clauses = []
    for cond in dsl.get_growth_conditions():
        condition_sql, param_key = _build_growth_condition(cond, param_counter)
        if condition_sql:
            growth_having_clauses.append(condition_sql)
            params.update(param_key)
            param_counter += len(param_key)
    
    # Process trend conditions
    trend_having_clauses = []
    for cond in dsl.get_trend_conditions():
        condition_sql, param_key = _build_trend_condition(cond, param_counter)
        if condition_sql:
            trend_having_clauses.append(condition_sql)
            params.update(param_key)
            param_counter += len(param_key)
    
    # Build final query
    if needs_growth:
        # Add company summary CTE
        query += f"""
        company_summary AS (
            SELECT 
                id,
                symbol,
                company_name,
                sector,
                AVG(qoq_revenue_growth) as avg_qoq_growth,
                AVG(yoy_revenue_growth) as avg_yoy_growth,
                -- Count of quarters with positive growth
                SUM(CASE WHEN qoq_revenue_growth > 0 THEN 1 ELSE 0 END) as positive_growth_quarters,
                COUNT(*) as total_analyzed_quarters,
                -- Trend score (higher means more increasing)
                CORR(rn, revenue) as revenue_trend_score
            FROM quarterly_data
            WHERE revenue IS NOT NULL
            GROUP BY id, symbol, company_name, sector
        )
        SELECT cs.symbol, cs.company_name, cs.sector,
               cs.avg_qoq_growth, cs.avg_yoy_growth, cs.positive_growth_quarters
        FROM company_summary cs
        """
        
        # Add JOIN for fundamentals if needed
        if joins_needed["fundamentals"]:
            query = query.replace(
                "FROM company_summary cs",
                "FROM company_summary cs JOIN fundamentals f ON cs.id = f.company_id"
            )
        
        # Add WHERE clauses for regular conditions
        if where_clauses:
            query += " WHERE " + f" {dsl.logic} ".join(where_clauses)
        
        # Add HAVING clauses for growth and trend conditions
        having_clauses = growth_having_clauses + trend_having_clauses
        if having_clauses:
            query += " HAVING " + f" {dsl.logic} ".join(having_clauses)
        
    else:
        # Simple query without growth analysis
        query = "SELECT DISTINCT s.symbol, s.company_name FROM symbols s"
        
        if joins_needed["fundamentals"]:
            query += " JOIN fundamentals f ON s.id = f.company_id"
        
        if where_clauses:
            query += " WHERE " + f" {dsl.logic} ".join(where_clauses)
    
    # Add limit
    query += " LIMIT :limit"
    params["limit"] = dsl.limit
    
    print("Generated SQL:", query)
    print("SQL Params:", params)
    
    return query, params

def _build_growth_condition(cond, start_param: int) -> Tuple[str, Dict]:
    """Build SQL condition for growth metrics"""
    params = {}
    
    metric_map = {
        "revenue_growth": "qoq_revenue_growth",
        "profit_growth": "qoq_profit_growth", 
        "avg_revenue_growth": "avg_qoq_growth",
        "avg_profit_growth": "avg_profit_growth"
    }
    
    if cond.metric not in metric_map:
        return "", {}
    
    column = metric_map[cond.metric]
    param_key = f"growth_val_{start_param}"
    
    # Add time range filter if specified
    time_filter = ""
    if hasattr(cond, 'time_range') and cond.time_range != "last_4_quarters":
        quarters = TIME_RANGE_QUARTERS.get(cond.time_range, 4)
        time_filter = f" AND total_analyzed_quarters >= {quarters}"
    
    condition = f"{column} {cond.operator} :{param_key}{time_filter}"
    params[param_key] = cond.value
    
    return condition, params

def _build_trend_condition(cond, start_param: int) -> Tuple[str, Dict]:
    """Build SQL condition for trend analysis"""
    params = {}
    
    trend_map = {
        "increasing": "revenue_trend_score > :trend_threshold",
        "decreasing": "revenue_trend_score < -:trend_threshold",
        "volatile": "ABS(revenue_trend_score) < :trend_threshold"
    }
    
    if cond.direction not in trend_map:
        return "", {}
    
    condition = trend_map[cond.direction]
    param_key = f"trend_thresh_{start_param}"
    params[param_key] = cond.confidence
    
    # Add time range filter
    quarters = TIME_RANGE_QUARTERS.get(cond.time_range, 4)
    condition += f" AND total_analyzed_quarters >= {quarters}"
    
    return condition, params