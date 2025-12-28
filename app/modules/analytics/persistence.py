"""
Persistence service for saving telemetry frames to database.

Consumes telemetry samples from queue and persists them at controlled intervals.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.analytics.database import SessionLocal
from app.modules.analytics.models import TelemetryFrame
from app.modules.analytics.session_manager import SessionManager
from app.modules.telemetry.schemas import TelemetrySample

logger = logging.getLogger(__name__)


async def persistence_worker(queue: asyncio.Queue) -> None:
    """
    Background worker that persists telemetry frames to database.
    
    Consumes TelemetrySample objects from queue, manages sessions,
    and saves frames at controlled intervals.
    
    This worker runs for the entire app lifetime and handles multiple sessions.
    When a session ends, it continues running and will create a new session
    when movement resumes.
    
    Args:
        queue: asyncio.Queue containing TelemetrySample objects
    """
    logger.info("Starting persistence worker...")
    
    # For MVP, use user_id=1 (local user)
    # In the future, this would map to actual users based on IP or other criteria
    USER_ID = 1
    
    db: Session = SessionLocal()
    try:
        session_manager = SessionManager(db, user_id=USER_ID)
    except Exception as e:
        logger.error(f"Failed to initialize session manager: {e}", exc_info=True)
        db.close()
        return
    
    try:
        # Main loop - runs until app shutdown
        while True:
            try:
                # Get telemetry sample from queue (with timeout to allow cancellation)
                sample: TelemetrySample = await asyncio.wait_for(
                    queue.get(),
                    timeout=1.0
                )
                
                # Process sample and get current active session
                # This handles session start/end logic
                current_session = session_manager.process_sample(sample)
                
                # Save frame if we have an active session and save interval has passed
                if current_session is not None:
                    now = datetime.utcnow()
                    if session_manager.should_save_frame(now):
                        _save_frame(db, current_session.id, sample)
                        session_manager.update_save_time(now)
                
            except asyncio.TimeoutError:
                # Timeout is expected - allows us to check for cancellation
                # Check if we need to end an inactive session
                # This ensures sessions end even if no new samples arrive
                now = datetime.utcnow()
                session_manager.check_inactivity(now)
                continue
            except Exception as e:
                logger.error(f"Error in persistence worker: {e}", exc_info=True)
                # Continue processing even if one sample fails
                await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        logger.info("Persistence worker cancelled, shutting down...")
        # End current session if active before shutdown
        if session_manager.current_session is not None:
            session_manager._end_session(datetime.utcnow())
        raise
    except Exception as e:
        logger.error(f"Fatal error in persistence worker: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.info("Persistence worker stopped")


def _save_frame(db: Session, session_id: int, sample: TelemetrySample) -> None:
    """
    Save a telemetry frame to the database.
    
    Args:
        db: Database session
        session_id: Session ID to associate frame with
        sample: TelemetrySample to save
    """
    try:
        frame = TelemetryFrame(
            session_id=session_id,
            timestamp=sample.timestamp,
            speed=sample.speed,
            rpm=sample.rpm,
            gear=sample.gear,
            g_force_x=sample.g_force_x,
            g_force_y=sample.g_force_y,
            fuel=None  # Not available in OutGauge
        )
        db.add(frame)
        db.commit()
    except Exception as e:
        logger.error(f"Error saving frame: {e}", exc_info=True)
        db.rollback()

