from fastapi import APIRouter
from alert_schema import AlertCreate
from alert_service import add_alert, get_alerts, delete_alert, check_alerts

router = APIRouter()


@router.post("/alerts/add")
def create_alert(alert: AlertCreate):
    alert_id = add_alert(alert)
    return {"message": "Alert created", "alert_id": alert_id}


@router.get("/alerts/{user_id}")
def fetch_alerts(user_id: int):
    return {"alerts": get_alerts(user_id)}


@router.delete("/alerts/{alert_id}")
def remove_alert(alert_id: int):
    delete_alert(alert_id)
    return {"message": "Deleted"}


@router.get("/test")
def test():
    return {"message": "Alert route working"}
