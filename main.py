from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from schemas import DSLQuery, PortfolioItem, AlertItem
import sqlite3
import operator as op
import os
import time
from llm_parser import parse_natural_language_to_dsl
from compiler import compile_dsl_to_sql

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

# Global Error Handler for Pydantic Validation Errors 
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid input provided. Please check your query."}
    )

# Global Error Handler for all other System/Database Errors 
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"INTERNAL SYSTEM ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Something went wrong on our end. Please try again later."}
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
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()

    start_time = time.time()
    
    # Execute the query securely
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    
    end_time = time.time()
    execution_time_ms = round((end_time - start_time) * 1000, 2)
    
    print("🔥 SQL QUERY:", sql_query)
    print("🔥 PARAMS:", params)
    print(f"⏱️ EXECUTION TIME: {execution_time_ms} ms")

    # Convert row objects to standard Python dictionaries
    results = [dict(row) for row in rows]
    conn.close()
    
    # Step 5: Return the final formatted API response
    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "debug_info": {
            "compiled_sql": sql_query,
            "execution_time_ms": execution_time_ms
        }
    }
# ==========================================
# 📈 PORTFOLIO API ENDPOINTS
# ==========================================

@app.post("/portfolio/add")
async def add_to_portfolio(item: dict):
    try:
        conn = sqlite3.connect('stocks.db')
        cursor = conn.cursor()
        
        # Check if stock already exists in portfolio
        cursor.execute("SELECT id, quantity, buy_price FROM portfolio WHERE user_id=? AND symbol=?", (item['user_id'], item['symbol']))
        existing = cursor.fetchone()
        
        if existing:
            old_id, old_qty, old_price = existing
            new_qty = old_qty + item['quantity']
            # Calculate new average buy price
            new_avg_price = ((old_qty * old_price) + (item['quantity'] * item['buy_price'])) / new_qty
            
            cursor.execute("UPDATE portfolio SET quantity=?, buy_price=? WHERE id=?", (new_qty, round(new_avg_price, 2), old_id))
            message = f"Updated {item['symbol']}. New Avg Price: ₹{round(new_avg_price, 2)}"
        else:
            # Insert fresh stock
            cursor.execute("INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (?, ?, ?, ?)", 
                           (item['user_id'], item['symbol'], item['quantity'], item['buy_price']))
            message = f"Added {item['symbol']} to portfolio!"
            
        conn.commit()
        conn.close()
        return {"status": "success", "message": message}
    except Exception as e:
        print(f"INTERNAL ERROR: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to update portfolio."})

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
        current_price = buy_price * 1.08 
        
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
# Helper to map string operators to Python math operators
OPS_MAP = {
    '<': op.lt,
    '<=': op.le,
    '>': op.gt,
    '>=': op.ge,
    '=': op.eq
}

# ==========================================
# 🔔 ALERTS API ENDPOINTS & EVALUATION
# ==========================================

@app.post("/alert/add")
async def add_alert(item: AlertItem):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alerts (user_id, symbol, field, operator, value, alert_type) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (item.user_id, item.symbol, item.field, item.operator, item.value, item.alert_type))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Alert set: {item.symbol} {item.field} {item.operator} {item.value}"}

@app.get("/alerts/{user_id}")
async def get_alerts(user_id: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts WHERE user_id=? AND is_active=1", (user_id,))
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"status": "success", "data": alerts}

@app.delete("/alert/{alert_id}")
async def delete_alert(alert_id: int):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Alert removed"}

@app.get("/alerts/check/{user_id}")
async def check_alerts(user_id: str):
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(current_dir, 'stocks.db'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch active alerts 
    cursor.execute("SELECT * FROM alerts WHERE user_id=? AND is_active=1", (user_id,))
    active_alerts = cursor.fetchall()
    
    triggered_notifications = []
    
    # 2. Loop through alerts 
    for alert in active_alerts:
        symbol = alert['symbol']
        field = alert['field']
        target_value = alert['value']
        operator_str = alert['operator']
        alert_id = alert['id']
        
        
        # 3. Get current data from fundamentals (our recent data source)
        try:
            cursor.execute(f"SELECT {field} FROM fundamentals WHERE symbol=?", (symbol,))
            current_data = cursor.fetchone()
            
            if current_data and current_data[field] is not None:
                current_value = current_data[field]
                
                # 4. Evaluate condition dynamically 
                operation = OPS_MAP.get(operator_str)
                if operation and operation(current_value, target_value):
                    # CONDITION MET! Trigger alert! 
                    msg = f"🔔 ALERT TRIGGERED: {symbol} {field} is now {current_value} (Target was {operator_str} {target_value})"
                    triggered_notifications.append({"alert_id": alert_id, "message": msg})
 
                    cursor.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        except Exception as e:
            print(f"Error evaluating alert {alert_id}: {e}")
            
    conn.commit()
    conn.close()
    
    return {"status": "success", "triggered": triggered_notifications}