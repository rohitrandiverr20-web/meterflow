from datetime import datetime, timedelta
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import User
import secrets
import hashlib

SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    # data will look like: {"sub": "user@email.com", "role": "developer"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decode JWT here and fetch user from DB
    # Return user object
    pass

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )
    return current_user

def generate_api_key():
    # Generate a secure 32-byte string
    raw_key = secrets.token_urlsafe(32)
    # Add a custom prefix for easy identification (optional but recommended)
    formatted_key = f"mf_live_{raw_key}"
    
    # Hash the key for storage using SHA-256
    key_hash = hashlib.sha256(formatted_key.encode()).hexdigest()
    
    return formatted_key, key_hash