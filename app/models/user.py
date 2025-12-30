from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    """
    User account model.

    Stores authentication and basic authorization data.
    Passwords are stored as secure hashes only.
    """

    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

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

    full_name = Column(
        String,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    is_admin = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
