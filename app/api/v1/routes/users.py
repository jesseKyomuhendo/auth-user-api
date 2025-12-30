# app/api/v1/routes/users.py
"""
User routes.

Endpoints:
- GET    /users/me
- PUT    /users/me
- GET    /users          (admin)
- GET    /users/{id}     (admin)
- PATCH  /users/{id}/active (admin)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
)
def read_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile.
    """
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's profile.
    """
    try:
        return user_service.update_me(
            db,
            current_user=current_user,
            full_name=data.full_name,
        )
    except user_service.UserInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# =========================
# Admin endpoints
# =========================
@router.get(
    "",
    response_model=list[UserRead],
)
def admin_list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
):
    """
    Admin: list all users.
    """
    return user_service.admin_list_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
def admin_get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: get user by ID.
    """
    try:
        return user_service.admin_get_user(db, user_id)
    except user_service.UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/{user_id}/active",
    response_model=UserRead,
)
def admin_set_active(
    user_id: UUID,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: activate or deactivate a user.
    """
    try:
        return user_service.admin_set_active(db, user_id=user_id, is_active=is_active)
    except user_service.UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
