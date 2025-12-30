from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =========================
# Base schema
# =========================
class UserBase(BaseModel):
    """
    Shared fields across multiple user-related schemas.

    This base schema is never used directly in responses.
    """
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(
        None,
        description="Optional display name for the user",
        max_length=255,
    )


# =========================
# Schemas for requests
# =========================
class UserCreate(UserBase):
    """
    Schema used when a user registers.

    Includes password because this is user input.
    """
    password: str = Field(
        ...,
        min_length=8,
        description="Plaintext password (will be hashed before storage)",
    )


class UserUpdate(BaseModel):
    """
    Schema used when a user updates their own profile.

    All fields are optional to support partial updates.
    """
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated display name",
    )


# =========================
# Schemas for responses
# =========================
class UserRead(BaseModel):
    """
    Schema returned in API responses.

    Sensitive fields such as passwords are intentionally excluded.
    """
    user_id: UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True
