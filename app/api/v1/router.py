# app/api/v1/router.py
"""
V1 API Router

Collects routers for API version v1.
Routes are grouped by domain:
- /auth
- /users
(optional later)
- /admin
"""

from fastapi import APIRouter

from app.api.v1.routes import auth, users  # add admin later when you create it

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Later (optional):
# from app.api.v1.routes import admin
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
