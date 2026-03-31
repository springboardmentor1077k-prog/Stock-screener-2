from fastapi import FastAPI

from portfolio_back import router as portfolio_router
from sell_stock_back import router as sell_router
from buy_stock_back import router as buy_router
from company_back import router as company_details_back
from alert_back import router as alert_router
from login_back import router as login_router
from query_back import router as query_router

app = FastAPI(title="Stock Screener API")

app.include_router(login_router, prefix="/auth", tags=["Auth"])


app.include_router(query_router, prefix="/query", tags=["Querys"])

app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])


app.include_router(buy_router, prefix="/trade", tags=["Buy"])
app.include_router(sell_router, prefix="/trade", tags=["Sell"])


app.include_router(company_details_back, prefix="/company", tags=["Company"])


app.include_router(alert_router, prefix="/alerts", tags=["Alerts"])