from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from pydantic import BaseModel

from database import engine
from backend.auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------
# Request Schemas
# -----------------------------
class UserAuth(BaseModel):
    username: str
    password: str


# -----------------------------
# Register Endpoint
# -----------------------------
@router.post("/register")
def register_user(user: UserAuth):

    hashed_password = hash_password(user.password)

    with engine.begin() as conn:

        existing_user = conn.execute(
            text("""
                SELECT id FROM users
                WHERE username = :username
            """),
            {"username": user.username}
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        conn.execute(
            text("""
                INSERT INTO users (username, password)
                VALUES (:username, :password)
            """),
            {
                "username": user.username,
                "password": hashed_password
            }
        )

    return {"message": "User registered successfully"}


# -----------------------------
# Login Endpoint (FIXED)
# -----------------------------
@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):

    with engine.connect() as conn:

        db_user = conn.execute(
            text("""
                SELECT id, username, password
                FROM users
                WHERE username = :username
            """),
            {"username": form_data.username}
        ).fetchone()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token({"sub": db_user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }