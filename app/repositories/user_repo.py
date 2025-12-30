
#app/repositories/user_repo.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """
    Retrieve a user by their unique identifier.
    """
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email address.

    Used during login and registration checks.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    *,
    email: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    is_admin: bool = False,
) -> User:
    """
    Create and persist a new user.

    The password must already be hashed before calling this function.
    
    Note: This function uses flush() instead of commit() to allow
    the session dependency to handle the final commit.
    """
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_admin=is_admin,
    )
    db.add(user)
    db.flush()  # Flush to get generated ID
    db.refresh(user)  # Refresh to load generated fields
    return user


def update_user(
    db: Session,
    *,
    user: User,
    full_name: Optional[str] = None,
) -> User:
    """
    Update mutable user fields.

    Supports partial updates.
    
    Note: This function uses flush() instead of commit() to allow
    the session dependency to handle the final commit.
    """
    if full_name is not None:
        user.full_name = full_name

    db.flush()
    db.refresh(user)
    return user


def list_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieve a paginated list of users.

    Intended for admin use.
    """
    return (
        db.query(User)
        .offset(skip)
        .limit(limit)
        .all()
    )


def set_user_active_status(
    db: Session,
    *,
    user: User,
    is_active: bool,
) -> User:
    """
    Activate or deactivate a user account.
    
    Note: This function uses flush() instead of commit() to allow
    the session dependency to handle the final commit.
    """
    user.is_active = is_active
    db.flush()
    db.refresh(user)
    return user
