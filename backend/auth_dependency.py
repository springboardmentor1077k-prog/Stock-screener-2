from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import text

from database import engine

SECRET_KEY = "change_this_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Fetch user from DB
    with engine.connect() as conn:

        user = conn.execute(
            text("""
                SELECT id, username
                FROM users
                WHERE username = :username
            """),
            {"username": username}
        ).fetchone()

    if user is None:
        raise credentials_exception

    return {
        "id": user.id,
        "username": user.username
    }