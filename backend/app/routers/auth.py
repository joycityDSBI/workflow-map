"""Authentication router — login, register, and current-user endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    require_admin,
    verify_password,
)
from app.database import get_db
from app.models.users import User
from app.schemas.auth import CurrentUser, RegisterRequest, TokenResponse

# auto_error=False → 토큰 없어도 401 안 냄 (register 부트스트랩용)
_optional_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Obtain a JWT access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with username + password (OAuth2 form) and return a bearer token."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=CurrentUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (open when no users exist; admin token required otherwise)",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(_optional_bearer),
) -> CurrentUser:
    """Create a new user.
    - 사용자 0명: 인증 없이 첫 admin 계정 생성 (부트스트랩)
    - 사용자 존재: Bearer admin 토큰 필요
    """
    count_result = await db.execute(select(func.count()).select_from(User))
    user_count = count_result.scalar_one()

    if user_count > 0:
        # 기존 사용자 있음 → admin 토큰 검증
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="admin 토큰이 필요합니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        from app.core.auth import decode_token
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰")
        # DB에서 admin 확인
        caller = await db.execute(select(User).where(User.username == payload.get("sub")))
        caller_user = caller.scalar_one_or_none()
        if caller_user is None or caller_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin 권한이 필요합니다")
    else:
        # 부트스트랩: 첫 번째 사용자는 무조건 admin
        body.role = "admin"

    # Check for duplicate username
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken",
        )

    # Check for duplicate email
    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' is already registered",
        )

    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=body.role,
    )
    db.add(new_user)
    await db.flush()  # populate id before returning

    return CurrentUser(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,  # type: ignore[arg-type]
    )


@router.get("/me", response_model=CurrentUser, summary="Return the authenticated user's profile")
async def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Return identity information decoded from the bearer token."""
    return current_user
