from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from schemas import DSLQuery, PortfolioItem
import sqlite3
import os

from schemas import DSLQuery
from llm_parser import parse_natural_language_to_dsl
from compiler import compile_dsl_to_sql

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

# Global Error Handler for Pydantic Validation Errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    error_msg = exc.errors()[0].get("msg")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "code": "INVALID_FIELD",
            "message": error_msg
        }
    )

# Global Error Handler for General/LLM Errors to prevent server crash
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": str(exc)
        }
    )

@app.post("/query")
async def process_query(request: QueryRequest):
    # Step 1: Send raw natural language to LLM Parser
    raw_dsl_dict = parse_natural_language_to_dsl(request.query)
    
    # Step 2: Pass output through strict Pydantic Validator
    validated_dsl = DSLQuery(**raw_dsl_dict)
    
    # Step 3: Compile validated DSL into parameterized SQL
    sql_query, params = compile_dsl_to_sql(validated_dsl.model_dump())
    
    # Step 4: Execution Layer - Connect to DB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'stocks.db')
    
    conn = sqlite3.connect(db_path)
    # This row_factory automatically converts database rows into dictionary format
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Execute the query securely
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    print("🔥 SQL QUERY:", sql_query)
    print("🔥 PARAMS:", params)
    print("🔥 TOTAL ROWS FETCHED:", len(rows))

    # Convert row objects to standard Python dictionaries
    results = [dict(row) for row in rows]

    # Convert row objects to standard Python dictionaries
    results = [dict(row) for row in rows]
    conn.close()
    
    # Step 5: Return the final formatted API response
    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "debug_info": {
        "compiled_sql": sql_query
        }
    }
# ==========================================
# 📈 PORTFOLIO API ENDPOINTS
# ==========================================

@app.post("/portfolio/add")
async def add_to_portfolio(item: PortfolioItem):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    cursor = conn.cursor()
    
    # Check if stock already exists for this user
    cursor.execute("SELECT id, quantity, buy_price FROM portfolio WHERE user_id=? AND symbol=?", (item.user_id, item.symbol))
    existing = cursor.fetchone()
    
    if existing:
        old_qty, old_price = existing[1], existing[2]
        new_qty = old_qty + item.quantity
        new_avg_price = ((old_qty * old_price) + (item.quantity * item.buy_price)) / new_qty
        
        cursor.execute("UPDATE portfolio SET quantity=?, buy_price=? WHERE id=?", (new_qty, new_avg_price, existing[0]))
        msg = f"Updated {item.symbol} quantity. New Average Price: {round(new_avg_price, 2)}"
    else:
        # Insert fresh stock
        cursor.execute("INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (?, ?, ?, ?)", 
                       (item.user_id, item.symbol, item.quantity, item.buy_price))
        msg = f"Added {item.symbol} to portfolio"
        
    conn.commit()
    conn.close()
    return {"status": "success", "message": msg}

@app.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, quantity, buy_price FROM portfolio WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    
    portfolio_data = []
    for row in rows:
        item = dict(row)
        qty = item['quantity']
        buy_price = item['buy_price']
        
        # NOTE: For now, mocking current price (using snapshot idea). Real API can be added later.
        # Assuming current market price is slightly higher/lower than buy price for testing.
        current_price = buy_price * 1.08 # Dummy 8% growth snapshot
        
        #🔥Dynamic Derived Calculations 
        inv_value = qty * buy_price
        curr_value = qty * current_price
        profit_loss = curr_value - inv_value
        profit_pct = (profit_loss / inv_value) * 100 if inv_value > 0 else 0
        
        item['current_price'] = round(current_price, 2)
        item['investment_value'] = round(inv_value, 2)
        item['current_value'] = round(curr_value, 2)
        item['profit_loss'] = round(profit_loss, 2)
        item['profit_percentage'] = round(profit_pct, 2)
        
        portfolio_data.append(item)
        
    conn.close()
    return {"status": "success", "data": portfolio_data}

@app.delete("/portfolio/{item_id}")
async def delete_portfolio_item(item_id: int):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM portfolio WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Stock securely removed from portfolio"}