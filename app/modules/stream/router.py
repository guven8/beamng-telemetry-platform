"""
WebSocket router for real-time telemetry streaming.

Provides authenticated WebSocket endpoint for clients to receive
live telemetry data from BeamNG.drive.
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from jose import JWTError, jwt
from app.modules.auth.security import SECRET_KEY, ALGORITHM
from app.modules.auth.schemas import User
from app.modules.stream.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_user_from_token(token: str) -> User:
    """
    Validate JWT token and return User.
    
    Used for WebSocket authentication since WebSockets don't use
    HTTP Authorization headers in the same way.
    
    Args:
        token: JWT token string
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # For MVP, we use user_id=1 for the local user
        return User(id=1, username=username)
    except JWTError:
        raise credentials_exception


@router.websocket("/ws/telemetry")
async def websocket_telemetry(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time telemetry streaming.
    
    Requires valid JWT token as query parameter: ?token=<jwt_token>
    
    On connect:
    - Validates JWT token
    - Accepts WebSocket connection
    - Registers connection with manager
    
    On disconnect:
    - Unregisters connection
    
    Clients receive telemetry data as JSON messages in real-time.
    """
    try:
        # Validate JWT token
        user = await get_user_from_token(token)
        logger.info(f"WebSocket connection attempt from user: {user.username} (id={user.id})")
        
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user_id={user.id}")
        
        # Register connection
        await manager.connect(user.id, websocket)
        
        try:
            # Keep connection alive and handle incoming messages (if any)
            while True:
                # Wait for any message from client (ping/pong or close)
                data = await websocket.receive_text()
                # For now, we just echo back or ignore client messages
                # In the future, could handle subscription changes, etc.
                logger.debug(f"Received message from user_id={user.id}: {data}")
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected by client: user_id={user.id}")
        except Exception as e:
            logger.error(f"WebSocket error for user_id={user.id}: {e}", exc_info=True)
        finally:
            # Unregister connection on disconnect
            await manager.disconnect(user.id, websocket)
            
    except HTTPException as e:
        logger.warning(f"WebSocket authentication failed: {e.detail}")
        # Try to send error message before closing
        try:
            await websocket.close(code=1008)  # Policy violation
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)  # Internal error
        except:
            pass

