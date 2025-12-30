# app/models/refresh_token.py
"""
RefreshToken model with database compatibility for both PostgreSQL and SQLite.

This version removes PostgreSQL-specific features:
- Changed from server_default=text("gen_random_uuid()") to default=uuid4
- Changed from server_default=text("now()") to default=func.now()
- Uses custom GUID type instead of PostgreSQL UUID
"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base import Base
from app.models.user import GUID  # Import the custom GUID type


class RefreshToken(Base):
    """
    Refresh token model.

    Represents a long-lived authentication session.
    Each refresh token is linked to a user and can be revoked
    independently to support logout, rotation, and security events.

    Compatible with both PostgreSQL (production) and SQLite (testing).

    Changes from original:
    - refresh_token_id: Uses GUID() with default=uuid4 instead of server_default
    - user_id: Uses GUID() instead of PostgreSQL UUID
    - issued_at: Uses default=func.now() instead of server_default=text("now()")
    """

    __tablename__ = "refresh_tokens"

    refresh_token_id = Column(
        GUID(),
        primary_key=True,
        default=uuid4,  # Python-level default (works everywhere)
        nullable=False
    )

    # User this refresh token belongs to
    user_id = Column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hashed value of the refresh token (never store plaintext tokens)
    token_hash = Column(
        String,
        nullable=False,
        unique=True,
    )

    # Timestamp when the token was issued
    issued_at = Column(
        DateTime(timezone=True),
        default=func.now(),  # Database-level default (works with both databases)
        nullable=False,
    )

    # Absolute expiration timestamp
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # If set, the token is considered revoked and unusable
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Optional metadata for auditing / security analysis
    user_agent = Column(
        String,
        nullable=True,
    )

    ip_address = Column(
        String,
        nullable=True,
    )

    # =========================
    # Relationships
    # =========================
    user = relationship(
        "User",
        backref="refresh_tokens",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<RefreshToken(refresh_token_id={self.refresh_token_id}, user_id={self.user_id})>"