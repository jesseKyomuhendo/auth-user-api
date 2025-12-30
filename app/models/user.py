# app/models/user.py
"""
User model with database compatibility for both PostgreSQL and SQLite.

This version removes PostgreSQL-specific features:
- Changed from server_default=text("gen_random_uuid()") to default=uuid4
- Changed from server_default=text("true"/"false") to default=True/False
- Changed from server_default=text("now()") to default=func.now()
- Uses custom GUID type instead of PostgreSQL UUID
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, CHAR
from uuid import uuid4
import uuid

from app.db.base import Base


# =========================
# Custom UUID Type for SQLite
# =========================

class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    Stores UUIDs as strings in SQLite.

    This allows the same model to work with:
    - PostgreSQL: Native UUID type (binary, efficient)
    - SQLite: CHAR(36) string representation
    - Python: Always returns uuid.UUID objects
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Choose the right database type based on dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Convert Python UUID to database format."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        """Convert database format to Python UUID."""
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


# =========================
# User Model
# =========================

class User(Base):
    """
    User account model.

    Stores authentication and basic authorization data.
    Passwords are stored as secure hashes only.

    Compatible with both PostgreSQL (production) and SQLite (testing).

    Changes from original:
    - user_id: Uses GUID() with default=uuid4 instead of server_default
    - is_active: Uses default=True instead of server_default=text("true")
    - is_admin: Uses default=False instead of server_default=text("false")
    - created_at: Uses default=func.now() instead of server_default=text("now()")
    - updated_at: Uses default=func.now() and onupdate=func.now()
    """

    __tablename__ = "users"

    # Primary key - works with both PostgreSQL and SQLite
    user_id = Column(
        GUID(),
        primary_key=True,
        default=uuid4,  # Python-level default (works everywhere)
        nullable=False
    )

    # User credentials
    email = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    hashed_password = Column(
        String,
        nullable=False,
    )

    # Profile information
    full_name = Column(
        String,
        nullable=True,
    )

    # Status flags - Python-level defaults work everywhere
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,  # Python-level default instead of server_default
    )

    is_admin = Column(
        Boolean,
        nullable=False,
        default=False,  # Python-level default instead of server_default
    )

    # Timestamps - use func.now() for database-level defaults
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),  # Database-level default (both databases support)
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),  # Database-level default
        onupdate=func.now(),  # Auto-update on modification
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"