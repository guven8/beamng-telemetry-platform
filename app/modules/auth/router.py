"""
Authentication router for login endpoint.

This is a minimal local-only auth implementation.
In the future, login will query the PostgreSQL users table.
"""
import os
from functools import lru_cache
from fastapi import APIRouter, HTTPException, status
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])

# Minimal seeded user for demo purposes
# In the future, this will be stored in PostgreSQL
# Password can be set via environment variable or uses a simple default
SEEDED_USERNAME = "local"
SEEDED_PASSWORD = os.getenv("SEEDED_USER_PASSWORD", "local")


@lru_cache(maxsize=1)
def get_seeded_password_hash() -> str:
    """
    Get the hashed password for the seeded user.
    Uses LRU cache to compute hash only once on first call.
    This avoids bcrypt initialization issues at module import time.
    """
    return get_password_hash(SEEDED_PASSWORD)


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest) -> TokenResponse:
    """
    Login endpoint that accepts credentials and returns a JWT.
    
    Checks against a single hard-coded user (username: 'local').
    Password can be configured via SEEDED_USER_PASSWORD environment variable
    or defaults to 'local'.
    
    This is a minimal local-only auth implementation.
    In the future, this will query the PostgreSQL users table.
    
    Args:
        login_request: LoginRequest with username and password
        
    Returns:
        TokenResponse with JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Check against seeded user
    if login_request.username != SEEDED_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password (lazy hash computation on first login)
    if not verify_password(login_request.password, get_seeded_password_hash()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": login_request.username})
    return TokenResponse(access_token=access_token)

