from fastapi import HTTPException

def structured_error(code: int, error_code: str, message: str):
    raise HTTPException(
        status_code=code,
        detail={
            "status": "error",
            "code": error_code,
            "message": message
        }
    )