# app/services/user_service.py
"""
User service: higher-level operations around the User entity.

This module contains application/business logic and delegates database
operations to repositories (user_repo).

Why have a service layer?
- Keeps API routes thin
- Keeps DB logic in repos
- Makes testing easier
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repo


class UserNotFoundError(Exception):
    """Raised when a user does not exist."""


class UserInactiveError(Exception):
    """Raised when a user exists but is inactive."""


def get_user_or_404(db: Session, user_id: UUID) -> User:
    """
    Helper used by services and dependencies to fetch a user.
    """
    user = user_repo.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError("User not found")
    return user


def get_me(db: Session, current_user: User) -> User:
    """
    Return the current authenticated user.
    """
    if not current_user.is_active:
        raise UserInactiveError("User is inactive")
    return current_user


def update_me(db: Session, *, current_user: User, full_name: str | None = None) -> User:
    """
    Update the current user's profile fields.
    """
    if not current_user.is_active:
        raise UserInactiveError("User is inactive")

    return user_repo.update_user(db, user=current_user, full_name=full_name)


def admin_list_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Admin: list users (pagination ready).
    """
    return user_repo.list_users(db, skip=skip, limit=limit)


def admin_get_user(db: Session, user_id: UUID) -> User:
    """
    Admin: get any user by id.
    """
    return get_user_or_404(db, user_id)


def admin_set_active(db: Session, *, user_id: UUID, is_active: bool) -> User:
    """
    Admin: activate/deactivate a user.
    """
    user = get_user_or_404(db, user_id)
    return user_repo.set_user_active_status(db, user=user, is_active=is_active)
