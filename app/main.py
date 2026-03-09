from fastapi import FastAPI
from app.routes.query import router as query_router

app = FastAPI(title="AI Stock Screener")

app.include_router(query_router, prefix="/api/v1")