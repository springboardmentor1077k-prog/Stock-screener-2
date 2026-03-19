from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def get_user_id(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


@router.post("/post")
def create_post(content: str, authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posts (user_id, content)
        VALUES (?, ?)
    """, (user_id, content))

    conn.commit()
    conn.close()

    return {"message": "Post created"}


@router.get("/")
def get_posts():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, created_at
        FROM posts
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"content": r[0], "time": r[1]} for r in rows]