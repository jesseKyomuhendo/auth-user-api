# app/core/security.py
"""
Security utilities:
- Password hashing/verification (bcrypt)
- JWT access + refresh token creation
- JWT decoding + basic validation

This file is intentionally "pure" (no FastAPI imports) so it can be reused in services,
tests, and background jobs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context.
# bcrypt is the common default for web apps.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a JWT is invalid, expired, or otherwise not acceptable."""


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password before storing it.

    Never store plaintext passwords in the database.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plaintext password against a stored bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _build_claims(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Standard JWT claims:
    - sub: subject (we use user_id)
    - typ: token type ("access" or "refresh")
    - iat: issued-at (unix time)
    - exp: expiry (unix time)

    You can add more claims via extra_claims, but avoid sensitive data.
    """
    issued_at = _now_utc()
    expires_at = issued_at + expires_delta

    claims: Dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if extra_claims:
        claims.update(extra_claims)
    return claims


def create_access_token(*, user_id: UUID) -> str:
    """
    Create a short-lived access token.

    Used by clients to call protected endpoints (Authorization: Bearer <token>).
    """
    claims = _build_claims(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(*, user_id: UUID, token_id: UUID) -> str:
    """
    Create a long-lived refresh token.

    Pattern used in "Option B":
    - Refresh tokens are stored in DB (so you can revoke/rotate them).
    - The JWT includes a token id (jti) that matches the DB row.
    """
    claims = _build_claims(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims={
            "jti": str(token_id),  # unique identifier for this refresh token
        },
    )
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT signature + exp.

    Raises TokenError if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        # JWTError covers invalid signature, expired, malformed, etc.
        raise TokenError("Invalid or expired token") from e


def extract_subject_user_id(payload: Dict[str, Any]) -> UUID:
    """
    Extract and validate the user_id stored in the 'sub' claim.
    """
    sub = payload.get("sub")
    if not sub:
        raise TokenError("Token missing 'sub' claim")
    try:
        return UUID(sub)
    except ValueError as e:
        raise TokenError("Token 'sub' is not a valid UUID") from e


def require_token_type(payload: Dict[str, Any], expected: TokenType) -> None:
    """
    Ensure a token is the expected type (access vs refresh).
    """
    typ = payload.get("typ")
    if typ != expected:
        raise TokenError(f"Wrong token type (expected '{expected}', got '{typ}')")


def extract_refresh_jti(payload: Dict[str, Any]) -> UUID:
    """
    Extract the refresh token id (jti) from a refresh token.
    Used to look up the token in DB for rotation/revocation checks.
    """
    jti = payload.get("jti")
    if not jti:
        raise TokenError("Refresh token missing 'jti' claim")
    try:
        return UUID(jti)
    except ValueError as e:
        raise TokenError("Token 'jti' is not a valid UUID") from e
