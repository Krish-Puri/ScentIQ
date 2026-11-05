"""SCENTIQ Security, Cryptography and Role-Based Access Control.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import AuthRequiredError, ForbiddenError


class UserTokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    role: str = "guest"
    exp: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> UserTokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return UserTokenPayload(**payload)
    except JWTError:
        raise AuthRequiredError("Invalid or expired authentication token")


def get_current_user(authorization: Optional[str] = Header(None)) -> UserTokenPayload:
    """Dependency for strictly authenticated routes. Requires a valid Bearer token."""
    if not authorization:
        raise AuthRequiredError("Authentication required: missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthRequiredError("Authorization header must be Bearer token")

    return decode_token(token)


def get_optional_user(authorization: Optional[str] = Header(None)) -> UserTokenPayload:
    """Dependency for endpoints that can optionally personalize if a token is present, else default to guest."""
    if not authorization:
        return UserTokenPayload(sub="guest-anonymous", role="guest")

    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return decode_token(token)
    except Exception:
        pass
    return UserTokenPayload(sub="guest-anonymous", role="guest")


def require_role(allowed_roles: List[str]):
    """Enforces specific user roles (e.g. curator, reviewer, admin)."""
    def role_checker(current_user: UserTokenPayload = Depends(get_current_user)):
        if current_user.role not in allowed_roles and current_user.role != "admin":
            raise ForbiddenError(f"Role '{current_user.role}' lacks permission for this action")
        return current_user

    return role_checker

