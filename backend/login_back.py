from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import psycopg2
import bcrypt
import jwt
# import os


SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 3000

router = APIRouter()

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )


class RegisterUser(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str


# PASSWORD HASHING


def hash_password(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# JWT TOKEN GENERATION


def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = data.copy()
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# REGISTER ENDPOINT


@router.post("/register")
def register(user: RegisterUser):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)

    cursor.execute("""
        INSERT INTO users (email, name, hashed_password)
        VALUES (%s, %s, %s)
    """, (user.email, user.name, hashed_pw))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User registered successfully"}


# LOGIN ENDPOINT


@router.post("/login")
def login(user: LoginUser):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, email, hashed_password FROM users WHERE email = %s",
        (user.email,)
    )
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, email, hashed_password = result

    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user_id, "email": email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": "1 minute"
    }


# JWT VERIFICATION DEPENDENCY


def verify_token(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# PROTECTED ROUTE EXAMPLE


@router.get("/protected")
def protected_route(user_data: dict = Depends(verify_token)):
    return {
        "message": "You can now use the routerlication",
        "user": user_data
    }