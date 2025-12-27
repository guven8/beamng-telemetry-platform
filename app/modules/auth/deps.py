"""
FastAPI dependencies for authentication.

This is a minimal local-only auth implementation.
In the future, get_current_user will query the PostgreSQL users table.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.modules.auth.schemas import User
from app.modules.auth.security import SECRET_KEY, ALGORITHM

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    FastAPI dependency that validates JWT and returns current user.
    
    Reads the JWT from the Authorization header (Bearer <token>),
    validates it, and returns a User object.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User object with id and username
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Minimal implementation: return user based on username
    # In the future, this will query the database for the user
    # For now, we assume the username from the token is valid
    return User(id=1, username=username)

