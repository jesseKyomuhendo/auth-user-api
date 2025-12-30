# tests/test_auth.py
"""
Authentication endpoint tests.

Tests for:
- User registration
- User login
- Token refresh
- Logout
- Error cases
"""

import pytest
from uuid import UUID


# =========================
# Registration Tests
# =========================

def test_register_user_success(client, sample_user_data):
    """
    Test successful user registration.

    Should return 201 and user data with user_id.
    """
    response = client.post("/api/v1/auth/register", json=sample_user_data)

    assert response.status_code == 201
    data = response.json()

    # Verify response contains expected fields
    assert "user_id" in data
    assert data["email"] == sample_user_data["email"]
    assert data["full_name"] == sample_user_data["full_name"]
    assert data["is_active"] is True
    assert data["is_admin"] is False

    # Verify password is NOT in response
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify user_id is valid UUID
    UUID(data["user_id"])  # Should not raise


def test_register_duplicate_email(client, sample_user_data):
    """
    Test registration with duplicate email.

    Should return 409 Conflict.
    """
    # Register first user
    response1 = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response1.status_code == 201

    # Try to register again with same email
    response2 = client.post("/api/v1/auth/register", json=sample_user_data)

    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"].lower()


def test_register_invalid_email(client):
    """
    Test registration with invalid email format.

    Should return 422 Validation Error.
    """
    invalid_data = {
        "email": "not-an-email",  # Invalid format
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }

    response = client.post("/api/v1/auth/register", json=invalid_data)

    assert response.status_code == 422


def test_register_short_password(client):
    """
    Test registration with password shorter than 8 characters.

    Should return 422 Validation Error.
    """
    invalid_data = {
        "email": "test@example.com",
        "password": "Short1!",  # Only 7 characters
        "full_name": "Test User"
    }

    response = client.post("/api/v1/auth/register", json=invalid_data)

    assert response.status_code == 422


def test_register_without_full_name(client):
    """
    Test registration without full_name (optional field).

    Should succeed - full_name is optional.
    """
    data = {
        "email": "test@example.com",
        "password": "SecurePassword123!"
        # No full_name
    }

    response = client.post("/api/v1/auth/register", json=data)

    assert response.status_code == 201
    assert response.json()["full_name"] is None


# =========================
# Login Tests
# =========================

def test_login_success(client, sample_user_data, registered_user):
    """
    Test successful login with correct credentials.

    Should return 200 with access and refresh tokens.
    """
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()

    # Verify tokens are present
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify tokens are non-empty strings
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert isinstance(data["refresh_token"], str)
    assert len(data["refresh_token"]) > 0


def test_login_wrong_password(client, sample_user_data, registered_user):
    """
    Test login with incorrect password.

    Should return 401 Unauthorized.
    """
    login_data = {
        "email": sample_user_data["email"],
        "password": "WrongPassword123!"
    }

    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """
    Test login with non-existent email.

    Should return 401 Unauthorized.
    """
    login_data = {
        "email": "nonexistent@example.com",
        "password": "SomePassword123!"
    }

    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401


def test_login_inactive_user(client, sample_user_data, registered_user, db_session):
    """
    Test login with inactive user account.

    Should return 403 Forbidden.
    """
    # Deactivate the user
    from app.models.user import User
    user = db_session.query(User).filter(User.email == sample_user_data["email"]).first()
    user.is_active = False
    db_session.commit()

    # Try to login
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


# =========================
# Token Refresh Tests
# =========================

def test_refresh_token_success(client, user_tokens):
    """
    Test successful token refresh.

    Should return new access token and optionally new refresh token.
    """
    refresh_data = {
        "refresh_token": user_tokens["refresh_token"]
    }

    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 200
    data = response.json()

    # Verify new tokens are present
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify new access token is different from old one
    assert data["access_token"] != user_tokens["access_token"]


def test_refresh_with_invalid_token(client):
    """
    Test refresh with invalid/malformed token.

    Should return 401 Unauthorized.
    """
    refresh_data = {
        "refresh_token": "invalid.token.here"
    }

    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401


def test_refresh_with_access_token(client, user_tokens):
    """
    Test refresh using access token instead of refresh token.

    Should return 401 (wrong token type).
    """
    refresh_data = {
        "refresh_token": user_tokens["access_token"]  # Wrong type!
    }

    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401


def test_refresh_after_logout(client, user_tokens):
    """
    Test refresh after token has been revoked via logout.

    Should return 401 (token revoked).
    """
    # Logout (revokes refresh token)
    logout_data = {
        "refresh_token": user_tokens["refresh_token"]
    }
    client.post("/api/v1/auth/logout", json=logout_data)

    # Try to refresh with revoked token
    refresh_data = {
        "refresh_token": user_tokens["refresh_token"]
    }
    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401


# =========================
# Logout Tests
# =========================

def test_logout_success(client, user_tokens):
    """
    Test successful logout.

    Should return 204 No Content.
    """
    logout_data = {
        "refresh_token": user_tokens["refresh_token"]
    }

    response = client.post("/api/v1/auth/logout", json=logout_data)

    assert response.status_code == 204


def test_logout_with_invalid_token(client):
    """
    Test logout with invalid token.

    Should still return 204 (idempotent - client is "logged out" either way).
    """
    logout_data = {
        "refresh_token": "invalid.token.here"
    }

    response = client.post("/api/v1/auth/logout", json=logout_data)

    # Even with invalid token, logout succeeds
    # (from client perspective, they're logged out)
    assert response.status_code == 204


def test_logout_twice(client, user_tokens):
    """
    Test logging out twice with same token.

    Should succeed both times (idempotent).
    """
    logout_data = {
        "refresh_token": user_tokens["refresh_token"]
    }

    # First logout
    response1 = client.post("/api/v1/auth/logout", json=logout_data)
    assert response1.status_code == 204

    # Second logout (same token)
    response2 = client.post("/api/v1/auth/logout", json=logout_data)
    assert response2.status_code == 204


# =========================
# Integration Tests
# =========================

def test_full_auth_flow(client):
    """
    Test complete authentication flow:
    1. Register
    2. Login
    3. Refresh token
    4. Logout
    """
    # 1. Register
    register_data = {
        "email": "fullflow@example.com",
        "password": "FlowPassword123!",
        "full_name": "Full Flow User"
    }
    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    # 2. Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()

    # 3. Refresh token
    refresh_data = {
        "refresh_token": tokens["refresh_token"]
    }
    refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()

    # 4. Logout
    logout_data = {
        "refresh_token": new_tokens["refresh_token"]
    }
    logout_response = client.post("/api/v1/auth/logout", json=logout_data)
    assert logout_response.status_code == 204


def test_multiple_users_isolated(client):
    """
    Test that multiple users can register and login independently.
    """
    # Register user 1
    user1_data = {
        "email": "user1@example.com",
        "password": "User1Password123!",
        "full_name": "User One"
    }
    response1 = client.post("/api/v1/auth/register", json=user1_data)
    assert response1.status_code == 201

    # Register user 2
    user2_data = {
        "email": "user2@example.com",
        "password": "User2Password123!",
        "full_name": "User Two"
    }
    response2 = client.post("/api/v1/auth/register", json=user2_data)
    assert response2.status_code == 201

    # Both users should have different IDs
    assert response1.json()["user_id"] != response2.json()["user_id"]

    # Both users can login
    login1 = client.post("/api/v1/auth/login", json={
        "email": user1_data["email"],
        "password": user1_data["password"]
    })
    assert login1.status_code == 200

    login2 = client.post("/api/v1/auth/login", json={
        "email": user2_data["email"],
        "password": user2_data["password"]
    })
    assert login2.status_code == 200

    # Tokens should be different
    assert login1.json()["access_token"] != login2.json()["access_token"]