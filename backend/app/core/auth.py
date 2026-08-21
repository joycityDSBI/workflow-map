"""JWT authentication core — password hashing, token creation, and FastAPI dependencies."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.users import User
from app.schemas.auth import CurrentUser

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_DEFAULT_EXPIRE_HOURS = 8


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Encode a JWT access token.

    Args:
        data: Payload to encode (must include a ``sub`` key).
        expires_delta: Token lifetime; defaults to ACCESS_TOKEN_EXPIRE_HOURS.

    Returns:
        Signed JWT string.
    """
    to_encode = data.copy()
    expire_hours = getattr(settings, "ACCESS_TOKEN_EXPIRE_HOURS", _DEFAULT_EXPIRE_HOURS)
    delta = expires_delta or timedelta(hours=expire_hours)
    expire = datetime.now(timezone.utc) + delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token and return the payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Decode the JWT bearer token and return the authenticated user.

    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return CurrentUser(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,  # type: ignore[arg-type]
    )


async def require_domain_expert(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Allow domain_expert and admin roles; raise 403 otherwise."""
    if current_user.role not in ("domain_expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Domain expert or admin role required",
        )
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Allow admin role only; raise 403 otherwise."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
