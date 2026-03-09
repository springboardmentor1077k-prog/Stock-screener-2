from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.llm_service import generate_dsl
from app.services.screener_service import run_screener
from app.utils.error_handler import error_response

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)

@router.post("/query")
def query_endpoint(req: QueryRequest):
    try:
        dsl_raw = generate_dsl(req.query)
    except Exception as e:
        print("REAL LLM ERROR:", e)
        return error_response("LLM_ERROR", str(e))

    try:
        dsl_raw["limit"] = req.limit
        results = run_screener(dsl_raw)
    except ValueError as e:
        return error_response("INVALID_FIELD", str(e))
    except Exception:
        return error_response("QUERY_FAILED", "Unable to process query")

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }