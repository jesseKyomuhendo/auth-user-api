from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Central application configuration.

    All configuration values are loaded from environment variables.
    This allows the same codebase to run in different environments
    (local, Docker, future cloud) without code changes.
    """

    # =========================
    # Application
    # =========================
    APP_NAME: str = "auth-user-api"
    DEBUG: bool = False

    # =========================
    # Database
    # =========================
    # Full database connection string.
    # Example (Docker):
    # postgresql://auth_user:password@db:5432/auth_db
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection URL"
    )

    # =========================
    # Security / Authentication
    # =========================
    # Secret key used to sign JWT tokens.
    # MUST be kept secret and never committed to the repo.
    JWT_SECRET_KEY: str = Field(
        ...,
        description="Secret key for signing JWT tokens"
    )

    # JWT signing algorithm
    JWT_ALGORITHM: str = "HS256"

    # Access token lifetime (minutes)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Refresh token lifetime (days)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =========================
    # Password hashing
    # =========================
    # bcrypt is slow by design → protects against brute-force attacks
    PASSWORD_HASH_SCHEME: str = "bcrypt"

    class Config:
        """
        Pydantic settings configuration.

        env_file:
            Allows loading variables from a .env file during local development.
            In Docker or CI, environment variables are injected directly.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        # IMPORTANT: Allow extra environment variables (like POSTGRES_USER, etc.)
        # These are used by Docker but not by the Python application
        extra = "ignore"  # This allows POSTGRES_* variables without errors


# Singleton settings instance
# This is imported wherever configuration is needed.
settings = Settings()