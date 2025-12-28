"""
Session management logic.

Handles starting and stopping sessions based on movement and inactivity.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.modules.analytics.models import Session as SessionModel
from app.modules.telemetry.schemas import TelemetrySample

logger = logging.getLogger(__name__)

# Configuration
MOVEMENT_THRESHOLD = 0.5  # m/s - speed threshold to consider "moving"
INACTIVITY_TIMEOUT = timedelta(seconds=30)  # End session after 30s of no movement
FRAME_SAVE_INTERVAL = timedelta(seconds=1)  # Save frame every 1 second


class SessionManager:
    """
    Manages telemetry sessions: starting, stopping, and tracking state.
    """
    
    def __init__(self, db: Session, user_id: int = 1):
        """
        Initialize session manager.
        
        Args:
            db: Database session
            user_id: User ID for the session (defaults to 1 for MVP)
        """
        self.db = db
        self.user_id = user_id
        self.current_session: Optional[SessionModel] = None
        self.last_activity_time: Optional[datetime] = None
        self.last_save_time: Optional[datetime] = None
        self.is_moving = False
    
    def process_sample(self, sample: TelemetrySample) -> Optional[SessionModel]:
        """
        Process a telemetry sample and manage session state.
        
        Starts session when movement begins, ends after inactivity timeout.
        
        Args:
            sample: TelemetrySample to process
            
        Returns:
            Current session if active, None otherwise
        """
        now = datetime.utcnow()
        
        # Check if we're moving (speed above threshold)
        moving = sample.speed is not None and sample.speed > MOVEMENT_THRESHOLD
        
        # Start session if we start moving and no session exists
        if moving and not self.is_moving and self.current_session is None:
            self._start_session(now)
        
        # Update activity time if moving
        if moving:
            self.last_activity_time = now
            self.is_moving = True
        else:
            self.is_moving = False
        
        # End session if inactive for too long
        if (self.current_session is not None and 
            self.last_activity_time is not None and
            now - self.last_activity_time > INACTIVITY_TIMEOUT):
            self._end_session(now)
            return None
        
        return self.current_session
    
    def _start_session(self, start_time: datetime) -> None:
        """Start a new session."""
        try:
            session = SessionModel(
                user_id=self.user_id,
                start_time=start_time
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            self.current_session = session
            self.last_activity_time = start_time
            self.last_save_time = start_time
            
            logger.info(f"Started session {session.id} for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            self.db.rollback()
    
    def _end_session(self, end_time: datetime) -> None:
        """End the current session."""
        if self.current_session is None:
            return
        
        try:
            self.current_session.end_time = end_time
            self.db.commit()
            
            duration = end_time - self.current_session.start_time
            logger.info(f"Ended session {self.current_session.id} (duration: {duration})")
            
            self.current_session = None
            self.last_activity_time = None
            self.last_save_time = None
        except Exception as e:
            logger.error(f"Error ending session: {e}", exc_info=True)
            self.db.rollback()
    
    def check_inactivity(self, now: datetime) -> None:
        """
        Check for inactivity and end session if timeout exceeded.
        
        Args:
            now: Current timestamp
        """
        if (self.current_session is not None and 
            self.last_activity_time is not None and
            now - self.last_activity_time > INACTIVITY_TIMEOUT):
            self._end_session(now)
    
    def should_save_frame(self, now: datetime) -> bool:
        """
        Check if we should save a frame based on save interval.
        
        Args:
            now: Current timestamp
            
        Returns:
            True if frame should be saved
        """
        if self.last_save_time is None:
            return True
        
        return now - self.last_save_time >= FRAME_SAVE_INTERVAL
    
    def update_save_time(self, now: datetime) -> None:
        """Update the last save time."""
        self.last_save_time = now

