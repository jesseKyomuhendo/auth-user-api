from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    """
    Refresh token model.

    Represents a long-lived authentication session.
    Each refresh token is linked to a user and can be revoked
    independently to support logout, rotation, and security events.
    """

    __tablename__ = "refresh_tokens"

    refresh_token_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # User this refresh token belongs to
    user_id = Column(
        UUID(as_uuid=True),
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
        nullable=False,
        server_default=text("now()"),
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
