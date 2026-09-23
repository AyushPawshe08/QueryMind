import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
import jwt
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

load_dotenv()

# Secret key for JWT signing & verification
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "querymind_super_secret_jwt_key_2026_change_in_prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

# Password hashing instance with Argon2id
_pwd_hash = PasswordHash.recommended()


# ── Pydantic Schemas ───────────────────────────────────────────────────────────
class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    full_name: Optional[str] = Field(default=None, max_length=100)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


# ── Password Utilities ─────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _pwd_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2id hash."""
    return _pwd_hash.verify(plain_password, hashed_password)


# ── JWT Token Utilities ────────────────────────────────────────────────────────
def create_access_token(user_id: int, email: str, expires_days: int = JWT_EXPIRATION_DAYS) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


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
