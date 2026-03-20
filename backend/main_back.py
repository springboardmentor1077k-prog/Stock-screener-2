from fastapi import FastAPI
from portfolio_back import router as portfolio_router
from sell_stock_back import router as sell_router

app = FastAPI()

# include both routes
app.include_router(portfolio_router)
app.include_router(sell_router)