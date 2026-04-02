# app/routes/query.py (updated)

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.llm_service import generate_dsl, generate_portfolio_command, detect_query_type
from app.services.screener_service import run_screener, execute_portfolio_command
from app.utils.error_handler import error_response

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    user_id: int = Field(default=1, ge=1)  # For portfolio commands

@router.post("/query")
def query_endpoint(req: QueryRequest):
    """
    Unified endpoint that handles both stock screening and portfolio commands
    """
    
    # Step 1: Detect query type
    query_type = detect_query_type(req.query)
    
    if query_type == "portfolio":
        # Handle portfolio commands
        try:
            command = generate_portfolio_command(req.query)
            result = execute_portfolio_command(command, req.user_id)
            return result
        except Exception as e:
            print("Portfolio command error:", e)
            return error_response("PORTFOLIO_ERROR", str(e))
    
    else:
        # Handle stock screener queries
        try:
            dsl_raw = generate_dsl(req.query)
        except Exception as e:
            print("LLM Error:", e)
            return error_response("LLM_ERROR", str(e))
        
        try:
            dsl_raw["limit"] = req.limit
            results = run_screener(dsl_raw)
        except ValueError as e:
            return error_response("INVALID_FIELD", str(e))
        except Exception as e:
            print("Query execution error:", e)
            return error_response("QUERY_FAILED", "Unable to process query")
        
        return {
            "status": "success",
            "type": "screener",
            "count": len(results),
            "data": results
        }