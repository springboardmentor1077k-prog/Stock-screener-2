# app/services/screener_service.py
import time
import logging
from typing import Dict, Any, List, Optional
from app.services.compiler import compile_dsl_to_sql
from app.services.validator import validate_fields
from app.database.connection import execute_query
from app.schema.dsl_schema import DSL

# Setup logging
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Track query performance metrics"""
    def __init__(self):
        self.compilation_time = 0.0
        self.execution_time = 0.0
        self.total_time = 0.0
        self.rows_returned = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "compilation_ms": round(self.compilation_time, 2),
            "execution_ms": round(self.execution_time, 2),
            "total_ms": round(self.total_time, 2),
            "rows_returned": self.rows_returned
        }

def run_screener(dsl_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute stock screener query
    
    Args:
        dsl_raw: Dictionary containing DSL structure
    
    Returns:
        List of dictionaries containing query results
    
    Raises:
        ValueError: If validation fails
        Exception: For other errors
    """
    metrics = PerformanceMetrics()
    
    try:
        # Step 1: Convert to DSL model (Pydantic validation)
        start = time.time()
        dsl = DSL(**dsl_raw)
        metrics.compilation_time = (time.time() - start) * 1000
        logger.info(f"DSL parsed in {metrics.compilation_time:.2f}ms")
        
        # Step 2: Validate fields and conditions
        start = time.time()
        validate_fields(dsl)
        metrics.compilation_time += (time.time() - start) * 1000
        logger.info(f"Validation completed in {(time.time() - start) * 1000:.2f}ms")
        
        # Step 3: Compile DSL to SQL
        start = time.time()
        sql, params = compile_dsl_to_sql(dsl)
        compile_time = (time.time() - start) * 1000
        metrics.compilation_time += compile_time
        logger.info(f"SQL compiled in {compile_time:.2f}ms")
        logger.debug(f"Generated SQL: {sql}")
        logger.debug(f"Query params: {params}")
        
        # Step 4: Execute query
        start = time.time()
        results = execute_query(sql, params)
        metrics.execution_time = (time.time() - start) * 1000
        logger.info(f"Query executed in {metrics.execution_time:.2f}ms")
        
        # Calculate totals
        metrics.total_time = metrics.compilation_time + metrics.execution_time
        metrics.rows_returned = len(results)
        
        # Log performance summary
        logger.info(f"📊 Query Performance: {metrics.to_dict()}")
        
        return results
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Screener execution error: {e}")
        raise

def run_screener_with_metrics(dsl_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute screener and return results with performance metrics
    
    Args:
        dsl_raw: Dictionary containing DSL structure
    
    Returns:
        Dictionary with results and performance metrics
    """
    metrics = PerformanceMetrics()
    
    try:
        # Step 1: Convert to DSL model
        start = time.time()
        dsl = DSL(**dsl_raw)
        metrics.compilation_time = (time.time() - start) * 1000
        
        # Step 2: Validate
        start = time.time()
        validate_fields(dsl)
        metrics.compilation_time += (time.time() - start) * 1000
        
        # Step 3: Compile
        start = time.time()
        sql, params = compile_dsl_to_sql(dsl)
        metrics.compilation_time += (time.time() - start) * 1000
        
        # Step 4: Execute
        start = time.time()
        results = execute_query(sql, params)
        metrics.execution_time = (time.time() - start) * 1000
        
        # Calculate totals
        metrics.total_time = metrics.compilation_time + metrics.execution_time
        metrics.rows_returned = len(results)
        
        return {
            "data": results,
            "performance": metrics.to_dict(),
            "sql": sql,  # Optional: for debugging
            "params": params  # Optional: for debugging
        }
        
    except Exception as e:
        logger.error(f"Screener error: {e}")
        raise

# Optional: Portfolio command execution (if needed)
def execute_portfolio_command(command: dict, user_id: int = 1):
    """
    Execute portfolio commands from natural language
    This function is imported by query.py for portfolio commands
    """
    from app.services.portfolio_service import PortfolioService
    
    command_type = command.get("type")
    
    if command_type == "buy":
        return PortfolioService.add_stock(
            user_id=user_id,
            symbol=command["symbol"],
            quantity=command["quantity"],
            price=command.get("price", 100.00),
            notes=command.get("notes")
        )
    
    elif command_type == "sell":
        return PortfolioService.remove_stock(
            user_id=user_id,
            symbol=command["symbol"],
            quantity=command.get("quantity")
        )
    
    elif command_type == "view_portfolio":
        return PortfolioService.get_portfolio(user_id, include_transactions=False)
    
    elif command_type == "portfolio_summary":
        result = PortfolioService.get_portfolio_summary(user_id)
        return {
            "status": "success",
            "message": "Portfolio summary retrieved",
            "summary": result
        }
    
    elif command_type == "view_transactions":
        limit = command.get("limit", 20)
        transactions = PortfolioService.get_transaction_history(user_id, limit)
        return {
            "status": "success",
            "transactions": transactions,
            "count": len(transactions)
        }
    
    elif command_type == "watchlist_add":
        return PortfolioService.add_to_watchlist(
            user_id=user_id,
            symbol=command["symbol"],
            alert_price=command.get("alert_price"),
            notes=command.get("notes")
        )
    
    elif command_type == "watchlist_view":
        return PortfolioService.get_watchlist(user_id)
    
    else:
        raise ValueError(f"Unknown command type: {command_type}")
    
# app/services/screener_service.py (with debug)
import traceback

def run_screener(dsl_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute stock screener query"""
    
    try:
        print("=" * 60)
        print("DEBUG: Screener Service")
        print("=" * 60)
        print(f"DSL Raw: {dsl_raw}")
        
        # Step 1: Convert to DSL model
        dsl = DSL(**dsl_raw)
        print(f"DSL Parsed: {dsl}")
        
        # Step 2: Validate
        validate_fields(dsl)
        print("Validation passed")
        
        # Step 3: Compile to SQL
        sql, params = compile_dsl_to_sql(dsl)
        print(f"SQL: {sql}")
        print(f"Params: {params}")
        
        # Step 4: Execute query
        results = execute_query(sql, params)
        print(f"Results: {len(results)} rows")
        
        return results
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        raise