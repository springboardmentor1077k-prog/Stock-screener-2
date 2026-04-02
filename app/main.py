# app/main.py (add portfolio router)
from fastapi import FastAPI
from app.routes.query import router as query_router
from app.routes.portfolio import router as portfolio_router  # NEW
from app.routes.alerts import router as alerts_router


app = FastAPI(title="AI Stock Screener")

# Include routers
app.include_router(query_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")  # NEW
app.include_router(alerts_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "AI Stock Screener API",
        "endpoints": {
            "screener": "/api/v1/query",
            "portfolio": "/api/v1/portfolio"
        }
    }