from pydantic import BaseModel, EmailStr, Field


# =========================
# Authentication requests
# =========================
class LoginRequest(BaseModel):
    """
    Schema used for user login.

    The user provides credentials, which are verified against
    stored password hashes.
    """
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User plaintext password")


# =========================
# Token responses
# =========================
class TokenResponse(BaseModel):
    """
    Schema returned after successful authentication.

    Includes both access and refresh tokens.
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")


# =========================
# Token refresh request
# =========================
class RefreshTokenRequest(BaseModel):
    """
    Schema used to request a new access token using a refresh token.
    """
    refresh_token: str = Field(..., description="Valid refresh token")


# =========================
# Optional: logout request
# =========================
class LogoutRequest(BaseModel):
    """
    Schema used to revoke a refresh token (logout).
    """
    refresh_token: str = Field(..., description="Refresh token to revoke")
