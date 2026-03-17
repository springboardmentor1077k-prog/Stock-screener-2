def compile_dsl_to_sql(dsl_dict: dict):
    time_filter = dsl_dict.get("time_filter")
    conditions_list = []
    params = []
    
    cte_query = """
    WITH GrowthData AS (
        SELECT 
            company_id,
            quarter,
            revenue,
            LAG(revenue) OVER (PARTITION BY company_id ORDER BY quarter) as prev_revenue
        FROM historical_metrics
    ),
    CalculatedMetrics AS (
        SELECT 
            company_id,
            quarter,
            CASE 
                WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN 0 
                ELSE ((revenue - prev_revenue) / prev_revenue) * 100 
            END as revenue_growth
        FROM GrowthData
    )
    """
    
    if time_filter:
        base_query = cte_query + "SELECT f.*, c.revenue_growth, c.quarter FROM fundamentals f JOIN CalculatedMetrics c ON f.symbol = c.company_id WHERE "
    else:
        base_query = "SELECT * FROM fundamentals WHERE "
        
    for cond in dsl_dict.get("conditions", []):
        field = cond['field']
        
        if time_filter and field == 'revenue_growth':
            conditions_list.append(f"c.{field} {cond['operator']} ?")
        elif time_filter:
            conditions_list.append(f"f.{field} {cond['operator']} ?")
        else:
            conditions_list.append(f"{field} {cond['operator']} ?")
            
        params.append(cond['value'])
    
    if time_filter == "last_4_quarters":
        conditions_list.append("c.quarter >= ?")
        params.append("2025-Q1")
        
    logic_operator = f" {dsl_dict.get('logic', 'AND')} "
    final_query = base_query + logic_operator.join(conditions_list)
    
    return final_query, params