from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

def error_response(code, message, status_code=400):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": code,
            "message": message,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
    )