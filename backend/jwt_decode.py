import jwt
import secrets

SECRET_KEY = "supersecretkey"
def decode_jwt(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])