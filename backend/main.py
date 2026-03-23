from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import logging

from backend.db import get_connection
from backend.auth import create_access_token, verify_token, get_password_hash, verify_password

app = FastAPI(title="AI Stock Screener API")
logging.basicConfig(level=logging.INFO)

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class QueryRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 10
    sort_by: str = "pe_ratio"
    sort_order: str = "asc"

@app.get("/")
def read_root():
    return {"status": "Advanced Screener API is running!"}

@app.post("/register")
def register(user: RegisterRequest):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE username=%s OR email=%s", (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or Email already exists")
        
        # Insert new user with the email column active
        hashed_pw = get_password_hash(user.password)
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (user.username, user.email, hashed_pw))
        conn.commit()
        return {"message": "User registered successfully"}
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username=%s", (user.username,))
        db_user = cursor.fetchone()
        
        if not db_user or not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        token = create_access_token({"sub": db_user['username']})
        return {"access_token": token, "token_type": "bearer"}
    finally:
        cursor.close()
        conn.close()

import json
import redis
import os
from backend.llm import parse_nl_to_dsl
from backend.compiler import validate_dsl, compile_sql_from_dsl

# Set up Redis safely (Fail gracefully if they don't have a Redis Server installed locally)
try:
    redis_client = redis.StrictRedis(host=os.getenv("REDIS_HOST", "127.0.0.1"), port=6379, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

@app.post("/ask_ai")
def ask_ai(request: QueryRequest, username: str = Depends(verify_token)):
    # 1. OPTIONAL: Check Redis Cache First
    cache_key = f"query_cache:{request.query}"
    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return {"source": "Redis Cache", "data": json.loads(cached_result)}
    
    # 2. Parsing: Natural Language -> JSON DSL via ChatGPT
    dsl_data = parse_nl_to_dsl(request.query)
    if "error" in dsl_data:
        raise HTTPException(status_code=400, detail=dsl_data["error"])
        
    # 3. Validation: Validate DSL rigidly
    is_valid, err_msg = validate_dsl(dsl_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation Failed: {err_msg}")
        
    # 4. Compiler: DSL -> Safe Parameterized SQL
    sql_query, parameters = compile_sql_from_dsl(
        dsl_data, 
        sort_by=request.sort_by, 
        sort_order=request.sort_order, 
        limit=request.limit, 
        page=request.page
    )
    
    # 5. Database Execution
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Connection Failed.")
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_query, parameters)
        results = cursor.fetchall()
        
        # 6. Store in Cache (if Redis is running)
        response_data = {"dsl": dsl_data, "sql": sql_query, "params": parameters, "data": results}
        if redis_client:
            redis_client.setex(cache_key, 300, json.dumps(results)) # Cache for 5 minutes
            
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
