
#app/repositories/token_repo.py

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create_refresh_token(
    db: Session,
    *,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> RefreshToken:
    """
    Persist a new refresh token record.

    The token value itself must already be hashed before calling this function.
    
    Note: This function uses flush() instead of commit() to allow
    the session dependency to handle the final commit.
    """
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(refresh_token)
    db.flush()  # Flush to get generated ID
    db.refresh(refresh_token)  # Refresh to load generated fields
    return refresh_token


def get_refresh_token_by_id(
    db: Session,
    *,
    refresh_token_id: UUID,
) -> Optional[RefreshToken]:
    """
    Retrieve a refresh token by its unique identifier.
    """
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.refresh_token_id == refresh_token_id)
        .first()
    )


def get_refresh_token_by_hash(
    db: Session,
    *,
    token_hash: str,
) -> Optional[RefreshToken]:
    """
    Retrieve a refresh token by its hashed value.
    """
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )


def revoke_refresh_token(
    db: Session,
    *,
    refresh_token: RefreshToken,
) -> RefreshToken:
    """
    Revoke a refresh token by setting its revoked_at timestamp.
    
    Note: This function uses flush() instead of commit() to allow
    the session dependency to handle the final commit.
    """
    refresh_token.revoked_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(refresh_token)
    return refresh_token


def is_refresh_token_active(refresh_token: RefreshToken) -> bool:
    """
    Check whether a refresh token is still valid.

    A token is considered active if:
    - It is not revoked
    - It has not expired
    """
    now = datetime.now(timezone.utc)
    return (
        refresh_token.revoked_at is None
        and refresh_token.expires_at > now
    )
