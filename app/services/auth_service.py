# app/services/auth_service.py
"""
Auth service (Option B):
- Access tokens: short-lived JWT (not stored in DB)
- Refresh tokens: long-lived, stored in DB (revocable/rotatable)

Flow:
- Register: create user
- Login: verify password, create access token + refresh token (DB-backed)
- Refresh: validate refresh JWT + compare to DB record + issue new access token
- Logout: revoke refresh token record
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_refresh_jti,
    extract_subject_user_id,
    get_password_hash,
    require_token_type,
    verify_password,
)
from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories import user_repo, token_repo


# =========================
# Exceptions (service-level)
# =========================
class AuthError(Exception):
    """Base auth error."""


class EmailAlreadyRegistered(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class InactiveUser(AuthError):
    pass


class RefreshTokenInvalid(AuthError):
    pass


# =========================
# Helpers
# =========================
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    """
    Hash token value before storing in DB.

    We never store refresh tokens in plaintext. If DB leaks, attacker
    should not be able to use tokens directly.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _refresh_expires_at() -> datetime:
    return _now_utc() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)


# =========================
# Core operations
# =========================
def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    """
    Register a new user.
    """
    existing = user_repo.get_user_by_email(db, email)
    if existing:
        raise EmailAlreadyRegistered("Email already registered")

    hashed_pw = get_password_hash(password)
    user = user_repo.create_user(
        db,
        email=email,
        hashed_password=hashed_pw,
        full_name=full_name,
        is_admin=False,
    )
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """
    Verify email/password and return user if valid.
    """
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise InvalidCredentials("Invalid email or password")

    if not user.is_active:
        raise InactiveUser("User is inactive")

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Invalid email or password")

    return user


def issue_tokens_for_user(
    db: Session,
    *,
    user: User,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, str]:
    """
    Create and return (access_token, refresh_token).

    Refresh token is DB-backed and hashed in the database.
    """
    access = create_access_token(user_id=user.user_id)

    # Create a DB row FIRST to get refresh_token_id (jti).
    # We'll store a temporary unique hash, then replace with real token hash after signing.
    temp_hash = _hash_token(uuid4().hex)
    rt_row = token_repo.create_refresh_token(
        db,
        user_id=user.user_id,
        token_hash=temp_hash,
        expires_at=_refresh_expires_at(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    refresh = create_refresh_token(user_id=user.user_id, token_id=rt_row.refresh_token_id)

    # Replace temp hash with actual refresh token hash
    # CHANGED: Use flush() instead of commit()
    rt_row.token_hash = _hash_token(refresh)
    db.flush()
    db.refresh(rt_row)

    return access, refresh


def login(
    db: Session,
    *,
    email: str,
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, str]:
    """
    Authenticate user and issue tokens.
    
    This is the main login flow that combines authentication
    and token issuance.
    
    Args:
        db: Database session
        email: User email address
        password: Plaintext password
        user_agent: Optional user agent string for audit
        ip_address: Optional IP address for audit
    
    Returns:
        tuple[str, str]: (access_token, refresh_token)
        
    Raises:
        InvalidCredentials: If email/password is wrong
        InactiveUser: If user account is deactivated
    """
    user = authenticate_user(db, email=email, password=password)
    return issue_tokens_for_user(
        db,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address,
    )


def refresh_access_token(
    db: Session,
    *,
    refresh_token: str,
    rotate_refresh_token: bool = True,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, str | None]:
    """
    Validate refresh token (JWT + DB record) and issue a new access token.

    If rotate_refresh_token=True:
    - revoke old refresh token
    - issue new refresh token
    """
    try:
        payload = decode_token(refresh_token)
        require_token_type(payload, "refresh")
        user_id = extract_subject_user_id(payload)
        jti = extract_refresh_jti(payload)
    except TokenError as e:
        raise RefreshTokenInvalid(str(e)) from e

    rt_row = token_repo.get_refresh_token_by_id(db, refresh_token_id=jti)
    if not rt_row or not token_repo.is_refresh_token_active(rt_row):
        raise RefreshTokenInvalid("Refresh token revoked or expired")

    # Compare hashed token value to prevent replay if DB token_id is known
    if rt_row.token_hash != _hash_token(refresh_token):
        raise RefreshTokenInvalid("Refresh token does not match active session")

    user = user_repo.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise InactiveUser("User is inactive")

    new_access = create_access_token(user_id=user.user_id)

    if not rotate_refresh_token:
        return new_access, None

    # Rotate: revoke old, mint new
    token_repo.revoke_refresh_token(db, refresh_token=rt_row)
    new_access, new_refresh = issue_tokens_for_user(
        db,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return new_access, new_refresh


def logout(db: Session, *, refresh_token: str) -> None:
    """
    Logout by revoking the refresh token (DB-backed).
    """
    try:
        payload = decode_token(refresh_token)
        require_token_type(payload, "refresh")
        jti = extract_refresh_jti(payload)
    except TokenError as e:
        # Even if token is invalid, treat as "logged out" from client perspective.
        return

    rt_row = token_repo.get_refresh_token_by_id(db, refresh_token_id=jti)
    if rt_row and token_repo.is_refresh_token_active(rt_row):
        token_repo.revoke_refresh_token(db, refresh_token=rt_row)
