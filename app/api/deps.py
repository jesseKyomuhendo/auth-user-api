# app/api/deps.py
"""
FastAPI dependencies:
- get_current_user (via Bearer access token)
- require_admin

These are used inside your routes to protect endpoints.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import (
    TokenError,
    decode_token,
    extract_subject_user_id,
    require_token_type,
)
from app.db.session import get_db
from app.models.user import User
from app.repositories import user_repo


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Extract user_id from JWT access token, fetch user from DB, and return it.

    Raises 401 if token invalid or user doesn't exist.
    """
    try:
        payload = decode_token(token)
        require_token_type(payload, "access")
        user_id: UUID = extract_subject_user_id(payload)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user = user_repo.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Ensure the current user is an admin (RBAC).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
