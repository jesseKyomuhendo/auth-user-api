# tests/conftest.py
"""
Pytest configuration and fixtures for testing.

Provides:
- Test database setup/teardown
- Test client
- Sample user fixtures
- Authentication helpers
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# IMPORTANT: Set TESTING environment variable BEFORE importing app
# This prevents app/main.py from trying to connect to Docker PostgreSQL
os.environ["TESTING"] = "true"

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# =========================
# Test Database Setup
# =========================

# Use in-memory SQLite for tests (fast and isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with simple settings for SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Keep same connection across threads
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# =========================
# Database Fixtures
# =========================

@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database for each test.

    Scope: function (new DB per test for isolation)
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI test client with test database.

    Overrides the get_db dependency to use test database.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


# =========================
# User Fixtures
# =========================

@pytest.fixture
def sample_user_data():
    """
    Sample user registration data.
    """
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_admin_data():
    """
    Sample admin user registration data.
    """
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User"
    }


@pytest.fixture
def registered_user(client, sample_user_data):
    """
    Register a user and return the response.

    Returns: User registration response (dict with user_id, email, etc.)
    """
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def registered_admin(client, sample_admin_data, db_session):
    """
    Register an admin user and return the response.

    Note: Sets is_admin=True directly in database since
    normal registration creates non-admin users.
    """
    # Register as normal user first
    response = client.post("/api/v1/auth/register", json=sample_admin_data)
    assert response.status_code == 201
    user_data = response.json()

    # Manually set is_admin=True in database
    from app.models.user import User
    from uuid import UUID

    user = db_session.query(User).filter(
        User.user_id == UUID(user_data["user_id"])
    ).first()
    user.is_admin = True
    db_session.commit()

    return user_data


# =========================
# Authentication Fixtures
# =========================

@pytest.fixture
def user_tokens(client, sample_user_data, registered_user):
    """
    Login and return access + refresh tokens for a regular user.

    Returns: dict with 'access_token' and 'refresh_token'
    """
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def admin_tokens(client, sample_admin_data, registered_admin):
    """
    Login and return access + refresh tokens for an admin user.

    Returns: dict with 'access_token' and 'refresh_token'
    """
    login_data = {
        "email": sample_admin_data["email"],
        "password": sample_admin_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(user_tokens):
    """
    Authorization headers for authenticated requests (regular user).

    Returns: dict with Authorization header
    """
    return {
        "Authorization": f"Bearer {user_tokens['access_token']}"
    }


@pytest.fixture
def admin_auth_headers(admin_tokens):
    """
    Authorization headers for authenticated requests (admin user).

    Returns: dict with Authorization header
    """
    return {
        "Authorization": f"Bearer {admin_tokens['access_token']}"
    }


# =========================
# Helper Fixtures
# =========================

@pytest.fixture
def multiple_users(client):
    """
    Create multiple test users for pagination/listing tests.

    Returns: list of user data dicts
    """
    users = []
    for i in range(5):
        user_data = {
            "email": f"user{i}@example.com",
            "password": f"Password{i}123!",
            "full_name": f"User {i}"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        users.append(response.json())

    return users


# =========================
# Configuration
# =========================

@pytest.fixture(autouse=True)
def reset_settings():
    """
    Reset any settings modifications after each test.

    autouse=True means this runs automatically for every test.
    """
    # Store original values
    original_debug = settings.DEBUG

    yield

    # Restore original values
    settings.DEBUG = original_debug