"""
Session management logic.

Handles starting and stopping sessions based on movement and inactivity.

Session Lifecycle:
- A session represents a contiguous period of driving
- Sessions are separated by at least INACTIVITY_TIMEOUT seconds of no movement
- Start: When speed > MOVEMENT_THRESHOLD and there is no active session
- End: When inactive (no movement) for longer than INACTIVITY_TIMEOUT
- After a session ends, current_session is reset to None, allowing a new session to start
  when movement resumes
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
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
    
    Maintains a single "active session" (current_session) which is None when no session
    is active. After a session ends, current_session is reset to None, allowing a new
    session to be created when movement resumes.
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
        self.current_session: Optional[SessionModel] = None  # Active session ID, None if no active session
        self.last_activity_time: Optional[datetime] = None
        self.last_save_time: Optional[datetime] = None
    
    def process_sample(self, sample: TelemetrySample) -> Optional[SessionModel]:
        """
        Process a telemetry sample and manage session state.
        
        Session lifecycle:
        1. If no active session and speed > threshold: start new session
        2. If moving: update last_activity_time
        3. If inactive for > timeout: end current session (resets current_session to None)
        
        Args:
            sample: TelemetrySample to process
            
        Returns:
            Current active session if one exists, None otherwise
        """
        now = datetime.now(timezone.utc)
        
        # Check if we're moving (speed above threshold)
        moving = sample.speed is not None and sample.speed > MOVEMENT_THRESHOLD
        
        # Start new session if we're moving and there's no active session
        # This handles both initial movement and movement after a session has ended
        if moving and self.current_session is None:
            self._start_session(now)
        
        # Update activity time if moving
        if moving:
            self.last_activity_time = now
        
        # End session if inactive for too long (only if we have an active session)
        if (self.current_session is not None and 
            self.last_activity_time is not None and
            now - self.last_activity_time > INACTIVITY_TIMEOUT):
            self._end_session(now)
            # After ending, current_session is None, allowing a new session to start
            # when movement resumes
        
        return self.current_session
    
    def _start_session(self, start_time: datetime) -> None:
        """
        Start a new session.
        
        Creates a new Session record and sets it as the active session.
        """
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
            
            logger.info(f"Started session {session.id} for user {self.user_id} at {start_time}")
        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            self.db.rollback()
    
    def _end_session(self, end_time: datetime) -> None:
        """
        End the current active session.
        
        Marks the session as ended in the database and resets current_session to None.
        This allows a new session to be created when movement resumes.
        """
        if self.current_session is None:
            return
        
        session_id = self.current_session.id
        
        try:
            # Get frame count before ending
            from app.modules.analytics.models import TelemetryFrame
            frame_count = self.db.query(TelemetryFrame).filter(
                TelemetryFrame.session_id == session_id
            ).count()
            
            self.current_session.end_time = end_time
            self.db.commit()
            
            duration = end_time - self.current_session.start_time
            logger.info(
                f"Ended session {session_id} at {end_time} "
                f"(duration: {duration}, frame_count: {frame_count})"
            )
            
            # Reset to None - this allows a new session to start when movement resumes
            self.current_session = None
            self.last_activity_time = None
            self.last_save_time = None
        except Exception as e:
            logger.error(f"Error ending session: {e}", exc_info=True)
            self.db.rollback()
            # Still reset current_session to allow recovery
            self.current_session = None
            self.last_activity_time = None
            self.last_save_time = None
    
    def check_inactivity(self, now: datetime) -> None:
        """
        Check for inactivity and end session if timeout exceeded.
        
        Called periodically (e.g., during queue timeout) to check if an active
        session should be ended due to inactivity.
        
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

