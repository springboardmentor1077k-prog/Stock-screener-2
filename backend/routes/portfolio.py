from fastapi import APIRouter, Depends
from backend.auth_dependency import get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/")
def get_portfolio(user=Depends(get_current_user)):

    return {
        "message": "Portfolio fetched",
        "user": user
    }


@router.post("/")
def create_portfolio(user=Depends(get_current_user)):

    return {
        "message": "Portfolio created",
        "user": user
    }