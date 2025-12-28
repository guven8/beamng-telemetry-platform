"""
Telemetry queue consumer for broadcasting to WebSocket clients.

Consumes TelemetrySample objects from the queue and broadcasts them
to all active WebSocket connections for the authenticated user.
"""
import asyncio
import logging
from datetime import datetime
from app.modules.telemetry.schemas import TelemetrySample
from app.modules.stream.manager import manager

logger = logging.getLogger(__name__)


def telemetry_sample_to_dict(sample: TelemetrySample) -> dict:
    """
    Convert TelemetrySample to JSON-safe dictionary.
    
    Args:
        sample: TelemetrySample object
        
    Returns:
        Dictionary ready for JSON serialization
    """
    return {
        "speed": sample.speed,
        "rpm": sample.rpm,
        "gear": sample.gear,
        "g_force_x": sample.g_force_x,
        "g_force_y": sample.g_force_y,
        "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
    }


async def telemetry_consumer(queue: asyncio.Queue) -> None:
    """
    Background task that consumes telemetry from queue and broadcasts to WebSocket clients.
    
    Pulls TelemetrySample objects from the queue, converts them to JSON-safe format,
    and broadcasts to all active WebSocket connections for the local user (user_id=1).
    
    This runs continuously until cancelled.
    
    Args:
        queue: asyncio.Queue containing TelemetrySample objects
    """
    logger.info("Starting telemetry consumer...")
    
    # For MVP, we broadcast to user_id=1 (the local user)
    # In the future, this would map telemetry to users based on IP or other criteria
    TARGET_USER_ID = 1
    
    broadcast_count = 0
    
    try:
        while True:
            try:
                # Get telemetry sample from queue (with timeout to allow cancellation)
                sample: TelemetrySample = await asyncio.wait_for(
                    queue.get(), 
                    timeout=1.0
                )
                
                # Convert to JSON-safe dict
                message = telemetry_sample_to_dict(sample)
                
                # Broadcast to all connections for the target user
                await manager.broadcast_to_user(TARGET_USER_ID, message)
                
                broadcast_count += 1
                
                # Log periodically to avoid spam
                if broadcast_count % 100 == 0:
                    connection_count = manager.get_connection_count(TARGET_USER_ID)
                    logger.info(
                        f"Broadcasted {broadcast_count} telemetry samples "
                        f"(active connections: {connection_count})"
                    )
                
            except asyncio.TimeoutError:
                # Timeout is expected - allows us to check for cancellation
                continue
            except Exception as e:
                logger.error(f"Error in telemetry consumer: {e}", exc_info=True)
                # Continue processing even if one sample fails
                await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        logger.info("Telemetry consumer cancelled, shutting down...")
        raise
    except Exception as e:
        logger.error(f"Fatal error in telemetry consumer: {e}", exc_info=True)
        raise


