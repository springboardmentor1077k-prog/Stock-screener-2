from fastapi import FastAPI

from backend.routes.companies import router as companies_router
from backend.routes.auth import router as auth_router
from backend.routes.portfolio import router as portfolio_router
from backend.routes.alerts import router as alerts_router
from backend.routes.query import router as query_router

app = FastAPI()


app.include_router(companies_router)
app.include_router(auth_router)
app.include_router(portfolio_router)
app.include_router(alerts_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {"message": "Stock Screener Backend Running"}