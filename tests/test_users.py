# tests/test_users.py
"""
User management endpoint tests.

Tests for:
- Get current user profile
- Update current user profile
- Admin: List users
- Admin: Get user by ID
- Admin: Activate/deactivate users
- Authorization and permission checks
"""

import pytest
from uuid import UUID


# =========================
# Current User Profile Tests
# =========================

def test_get_me_success(client, auth_headers, registered_user):
    """
    Test getting current user's profile.

    Should return 200 with user data.
    """
    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify user data
    assert data["user_id"] == registered_user["user_id"]
    assert data["email"] == registered_user["email"]
    assert data["full_name"] == registered_user["full_name"]
    assert data["is_active"] is True

    # Verify password is NOT in response
    assert "password" not in data
    assert "hashed_password" not in data


def test_get_me_without_auth(client):
    """
    Test getting profile without authentication.

    Should return 401 Unauthorized.
    """
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_get_me_with_invalid_token(client):
    """
    Test getting profile with invalid token.

    Should return 401 Unauthorized.
    """
    invalid_headers = {
        "Authorization": "Bearer invalid.token.here"
    }

    response = client.get("/api/v1/users/me", headers=invalid_headers)

    assert response.status_code == 401


# =========================
# Update Profile Tests
# =========================

def test_update_me_success(client, auth_headers, registered_user):
    """
    Test updating current user's profile.

    Should return 200 with updated user data.
    """
    update_data = {
        "full_name": "Updated Name"
    }

    response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)

    assert response.status_code == 200
    data = response.json()

    # Verify update
    assert data["full_name"] == "Updated Name"
    assert data["user_id"] == registered_user["user_id"]
    assert data["email"] == registered_user["email"]  # Email unchanged


def test_update_me_clear_name(client, auth_headers):
    """
    Test clearing full_name (set to null).

    Should succeed - full_name is optional.
    """
    update_data = {
        "full_name": None
    }

    response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)

    assert response.status_code == 200
    assert response.json()["full_name"] is None


def test_update_me_without_auth(client):
    """
    Test updating profile without authentication.

    Should return 401 Unauthorized.
    """
    update_data = {
        "full_name": "Unauthorized Update"
    }

    response = client.put("/api/v1/users/me", json=update_data)

    assert response.status_code == 401


def test_update_me_empty_body(client, auth_headers):
    """
    Test updating profile with empty body.

    Should succeed (no changes made).
    """
    response = client.put("/api/v1/users/me", headers=auth_headers, json={})

    assert response.status_code == 200


# =========================
# Admin: List Users Tests
# =========================

def test_admin_list_users_success(client, admin_auth_headers, multiple_users):
    """
    Test admin listing all users.

    Should return 200 with list of users.
    """
    response = client.get("/api/v1/users", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify it's a list
    assert isinstance(data, list)

    # Should have at least the 5 test users + admin
    assert len(data) >= 6

    # Verify structure of first user
    if len(data) > 0:
        user = data[0]
        assert "user_id" in user
        assert "email" in user
        assert "is_active" in user


def test_admin_list_users_pagination(client, admin_auth_headers, multiple_users):
    """
    Test admin listing users with pagination.

    Should respect skip/limit parameters.
    """
    # Get first 2 users
    response1 = client.get("/api/v1/users?skip=0&limit=2", headers=admin_auth_headers)
    assert response1.status_code == 200
    users1 = response1.json()
    assert len(users1) == 2

    # Get next 2 users
    response2 = client.get("/api/v1/users?skip=2&limit=2", headers=admin_auth_headers)
    assert response2.status_code == 200
    users2 = response2.json()
    assert len(users2) == 2

    # Should be different users
    assert users1[0]["user_id"] != users2[0]["user_id"]


def test_admin_list_users_non_admin(client, auth_headers):
    """
    Test non-admin user trying to list users.

    Should return 403 Forbidden.
    """
    response = client.get("/api/v1/users", headers=auth_headers)

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_admin_list_users_without_auth(client):
    """
    Test listing users without authentication.

    Should return 401 Unauthorized.
    """
    response = client.get("/api/v1/users")

    assert response.status_code == 401


# =========================
# Admin: Get User by ID Tests
# =========================

def test_admin_get_user_success(client, admin_auth_headers, registered_user):
    """
    Test admin getting user by ID.

    Should return 200 with user data.
    """
    user_id = registered_user["user_id"]

    response = client.get(f"/api/v1/users/{user_id}", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["email"] == registered_user["email"]


def test_admin_get_user_not_found(client, admin_auth_headers):
    """
    Test admin getting non-existent user.

    Should return 404 Not Found.
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/users/{fake_uuid}", headers=admin_auth_headers)

    assert response.status_code == 404


def test_admin_get_user_invalid_uuid(client, admin_auth_headers):
    """
    Test admin getting user with invalid UUID.

    Should return 422 Validation Error.
    """
    response = client.get("/api/v1/users/not-a-uuid", headers=admin_auth_headers)

    assert response.status_code == 422


def test_admin_get_user_non_admin(client, auth_headers, registered_user):
    """
    Test non-admin trying to get user by ID.

    Should return 403 Forbidden.
    """
    user_id = registered_user["user_id"]

    response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)

    assert response.status_code == 403


# =========================
# Admin: Activate/Deactivate User Tests
# =========================

def test_admin_deactivate_user(client, admin_auth_headers, registered_user):
    """
    Test admin deactivating a user.

    Should return 200 with updated user (is_active=False).
    """
    user_id = registered_user["user_id"]

    response = client.patch(
        f"/api/v1/users/{user_id}/active?is_active=false",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["is_active"] is False


def test_admin_activate_user(client, admin_auth_headers, registered_user, db_session):
    """
    Test admin activating a previously deactivated user.

    Should return 200 with updated user (is_active=True).
    """
    user_id = registered_user["user_id"]

    # First deactivate
    from app.models.user import User
    user = db_session.query(User).filter(User.user_id == UUID(user_id)).first()
    user.is_active = False
    db_session.commit()

    # Then activate via API
    response = client.patch(
        f"/api/v1/users/{user_id}/active?is_active=true",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["is_active"] is True


def test_admin_activate_user_non_admin(client, auth_headers, registered_user):
    """
    Test non-admin trying to activate/deactivate user.

    Should return 403 Forbidden.
    """
    user_id = registered_user["user_id"]

    response = client.patch(
        f"/api/v1/users/{user_id}/active?is_active=false",
        headers=auth_headers
    )

    assert response.status_code == 403


def test_admin_activate_nonexistent_user(client, admin_auth_headers):
    """
    Test admin activating non-existent user.

    Should return 404 Not Found.
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.patch(
        f"/api/v1/users/{fake_uuid}/active?is_active=true",
        headers=admin_auth_headers
    )

    assert response.status_code == 404


# =========================
# Authorization Tests
# =========================

def test_regular_user_cannot_access_admin_endpoints(client, auth_headers, registered_user):
    """
    Test that regular users cannot access any admin endpoints.
    """
    user_id = registered_user["user_id"]

    # Try to list users
    response1 = client.get("/api/v1/users", headers=auth_headers)
    assert response1.status_code == 403

    # Try to get user by ID
    response2 = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert response2.status_code == 403

    # Try to deactivate user
    response3 = client.patch(
        f"/api/v1/users/{user_id}/active?is_active=false",
        headers=auth_headers
    )
    assert response3.status_code == 403


def test_admin_can_access_all_endpoints(client, admin_auth_headers, registered_user):
    """
    Test that admin can access all user endpoints.
    """
    user_id = registered_user["user_id"]

    # Can list users
    response1 = client.get("/api/v1/users", headers=admin_auth_headers)
    assert response1.status_code == 200

    # Can get user by ID
    response2 = client.get(f"/api/v1/users/{user_id}", headers=admin_auth_headers)
    assert response2.status_code == 200

    # Can deactivate user
    response3 = client.patch(
        f"/api/v1/users/{user_id}/active?is_active=false",
        headers=admin_auth_headers
    )
    assert response3.status_code == 200


# =========================
# Edge Cases
# =========================

def test_deactivated_user_cannot_login(client, sample_user_data, registered_user, db_session):
    """
    Test that deactivated user cannot login.
    """
    # Deactivate user
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


def test_deactivated_user_cannot_access_endpoints(client, auth_headers, registered_user, db_session):
    """
    Test that user with valid token but deactivated account cannot access endpoints.

    Note: This depends on whether your get_current_user dependency checks is_active.
    """
    # Get valid token first
    response1 = client.get("/api/v1/users/me", headers=auth_headers)
    assert response1.status_code == 200

    # Deactivate user
    from app.models.user import User
    user = db_session.query(User).filter(User.user_id == UUID(registered_user["user_id"])).first()
    user.is_active = False
    db_session.commit()

    # Try to access with same token (user now inactive)
    response2 = client.get("/api/v1/users/me", headers=auth_headers)

    # Should fail because user is inactive
    assert response2.status_code == 401


def test_user_can_update_own_profile_but_not_others(client, auth_headers, registered_user):
    """
    Test that users can update their own profile but not admin endpoints.
    """
    # Can update own profile
    response1 = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"full_name": "My New Name"}
    )
    assert response1.status_code == 200

    # Cannot list all users
    response2 = client.get("/api/v1/users", headers=auth_headers)
    assert response2.status_code == 403

    # Cannot deactivate themselves via admin endpoint
    response3 = client.patch(
        f"/api/v1/users/{registered_user['user_id']}/active?is_active=false",
        headers=auth_headers
    )
    assert response3.status_code == 403


# =========================
# Integration Tests
# =========================

def test_admin_user_lifecycle(client, admin_auth_headers):
    """
    Test complete user lifecycle from admin perspective:
    1. List users
    2. Create new user (via registration)
    3. Get user by ID
    4. Deactivate user
    5. Reactivate user
    """
    # 1. List users initially
    response1 = client.get("/api/v1/users", headers=admin_auth_headers)
    assert response1.status_code == 200
    initial_count = len(response1.json())

    # 2. Register new user (via public endpoint)
    register_data = {
        "email": "lifecycle@example.com",
        "password": "LifecyclePass123!",
        "full_name": "Lifecycle User"
    }
    response2 = client.post("/api/v1/auth/register", json=register_data)
    assert response2.status_code == 201
    new_user = response2.json()

    # 3. Admin can get this user
    response3 = client.get(f"/api/v1/users/{new_user['user_id']}", headers=admin_auth_headers)
    assert response3.status_code == 200

    # 4. Admin deactivates user
    response4 = client.patch(
        f"/api/v1/users/{new_user['user_id']}/active?is_active=false",
        headers=admin_auth_headers
    )
    assert response4.status_code == 200
    assert response4.json()["is_active"] is False

    # 5. Admin reactivates user
    response5 = client.patch(
        f"/api/v1/users/{new_user['user_id']}/active?is_active=true",
        headers=admin_auth_headers
    )
    assert response5.status_code == 200
    assert response5.json()["is_active"] is True

    # 6. User list now has one more user
    response6 = client.get("/api/v1/users", headers=admin_auth_headers)
    assert len(response6.json()) == initial_count + 1