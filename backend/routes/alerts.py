from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/")
def create_alert():
    return {"message": "Alert created"}


@router.get("/")
def get_alerts():
    return {"message": "User alerts returned"}