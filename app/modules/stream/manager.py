"""
WebSocket connection manager for real-time telemetry broadcasting.

Manages WebSocket connections per user and broadcasts telemetry data
to authenticated clients.
"""
import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time telemetry streaming.
    
    Stores connections per user ID and provides methods to connect,
    disconnect, and broadcast messages to specific users.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        # Map user_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Register a WebSocket connection for a user.
        
        Args:
            user_id: User ID from authentication
            websocket: WebSocket connection to register
        """
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(f"WebSocket connected: user_id={user_id}, total connections for user: {len(self.active_connections[user_id])}")
    
    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection for a user.
        
        Args:
            user_id: User ID from authentication
            websocket: WebSocket connection to unregister
        """
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    # Remove user entry if no connections remain
                    del self.active_connections[user_id]
                logger.info(f"WebSocket disconnected: user_id={user_id}, remaining connections for user: {len(self.active_connections.get(user_id, set()))}")
    
    async def broadcast_to_user(self, user_id: int, message: dict) -> None:
        """
        Broadcast a message to all WebSocket connections for a specific user.
        
        Args:
            user_id: User ID to broadcast to
            message: Dictionary to send (will be JSON-encoded)
        """
        # Get connections for this user (create a copy to avoid lock contention)
        async with self._lock:
            connections = list(self.active_connections.get(user_id, set()))
        
        if not connections:
            return
        
        # Send to all connections for this user
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket (user_id={user_id}): {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                if user_id in self.active_connections:
                    for ws in disconnected:
                        self.active_connections[user_id].discard(ws)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
    
    def get_connection_count(self, user_id: int | None = None) -> int:
        """
        Get the number of active connections.
        
        Args:
            user_id: If provided, count connections for this user only.
                     If None, count all connections.
        
        Returns:
            Number of active connections
        """
        if user_id is not None:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global manager instance
manager = WebSocketConnectionManager()

