from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import os

from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)

# -----------------------------
# DATABASE PATH
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")

router = APIRouter()


# -----------------------------
# REQUEST MODELS
# -----------------------------
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# -----------------------------
# SIGNUP API
# -----------------------------
@router.post("/signup")
def signup(data: SignupRequest):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (data.email,))
    existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    print("PASSWORD:", data.password)
    print("LENGTH:", len(data.password))

    # sanitize password
    password = data.password.strip()[:72]

    hashed_pw = hash_password(password)

    cursor.execute("""
        INSERT INTO users (username, email, hashed_password)
        VALUES (?, ?, ?)
    """, (data.username, data.email, hashed_pw))

    conn.commit()

    user_id = cursor.lastrowid
    conn.close()

    token = create_access_token(user_id)

    return {
        "message": "User created successfully",
        "access_token": token,
        "user_id": user_id
    }


# -----------------------------
# LOGIN API
# -----------------------------
@router.post("/login")
def login(data: LoginRequest):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, hashed_password FROM users WHERE email=?",
        (data.email,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, hashed_pw = user

    # sanitize password
    password = data.password.strip()[:72]

    if not verify_password(password, hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id
    }


# -----------------------------
# LIST USERS (for testing)
# -----------------------------
@router.get("/users")
def list_users():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, email FROM users")

    users = cursor.fetchall()

    conn.close()

    return [
        {
            "id": u[0],
            "username": u[1],
            "email": u[2]
        }
        for u in users
    ]