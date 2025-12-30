# app/api/v1/routes/auth.py
"""
Authentication routes.

Endpoints:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db


from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    """
    try:
        return auth_service.register_user(
            db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
        )
    except auth_service.EmailAlreadyRegistered as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Login and receive access + refresh tokens.
    """
    try:
        access, refresh = auth_service.login(
            db,
            email=data.email,
            password=data.password,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
        )
    except auth_service.InvalidCredentials as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except auth_service.InactiveUser as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Exchange a refresh token for a new access token.
    """
    try:
        access, new_refresh = auth_service.refresh_access_token(
            db,
            refresh_token=data.refresh_token,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh or data.refresh_token,
        )
    except auth_service.RefreshTokenInvalid as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except auth_service.InactiveUser as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
):
    """
    Logout by revoking the refresh token.
    """
    auth_service.logout(db, refresh_token=data.refresh_token)
