import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
import jwt
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

try:
    from backend.database import get_db, User
except ImportError:
    from database import get_db, User

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "querymind_super_secret_jwt_key_2026_change_in_prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

_pwd_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


try:
    from backend.schemas import (
        UserRegisterSchema,
        UserLoginSchema,
        UserResponseSchema,
        TokenResponseSchema,
    )
except ImportError:
    from schemas import (
        UserRegisterSchema,
        UserLoginSchema,
        UserResponseSchema,
        TokenResponseSchema,
    )


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _pwd_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2id hash."""
    return _pwd_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str, expires_days: int = JWT_EXPIRATION_DAYS) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a signed JWT token. Returns dict with user_id and email if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        if user_id and email:
            return {"user_id": user_id, "email": email}
        return None
    except (jwt.PyJWTError, ValueError):
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Enforces authentication and returns the current User."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account removed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Extracts User if valid Authorization Bearer token is provided, else returns None."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == payload["user_id"]).first()
