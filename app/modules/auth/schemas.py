"""
Authentication schemas for request/response models.

This is a minimal local-only auth implementation.
In the future, this will be backed by a real PostgreSQL users table.
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request payload."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """User model for authenticated requests."""
    id: int
    username: str

