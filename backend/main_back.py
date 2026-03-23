from fastapi import FastAPI
from portfolio_back import router as portfolio_router
from sell_stock_back import router as sell_router
from buy_stock_back import router as buy_router
from company_back import router as company_details_back

app = FastAPI()

# include both routes
app.include_router(portfolio_router)
app.include_router(sell_router)
app.include_router(buy_router)
app.include_router(company_details_back)