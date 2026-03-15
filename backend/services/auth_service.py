from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# -----------------------------
# SECURITY SETTINGS
# -----------------------------
SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

# password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
# PASSWORD FUNCTIONS
# -----------------------------
def hash_password(password: str):
    """
    Hash a password safely.
    bcrypt only supports 72 bytes, so truncate if longer.
    """
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    """
    Verify password against stored hash.
    """
    try:
        plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# -----------------------------
# CREATE ACCESS TOKEN
# -----------------------------
def create_access_token(user_id: int):
    """
    Generate JWT token for authenticated user.
    """

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


# -----------------------------
# VERIFY TOKEN
# -----------------------------
def verify_token(token: str):
    """
    Decode JWT token and return user_id.
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")

    except Exception:
        return None