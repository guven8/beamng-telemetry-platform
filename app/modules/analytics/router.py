"""
Analytics router for sessions API.

Provides endpoints to list and retrieve telemetry sessions.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.analytics.database import get_db
from app.modules.analytics.models import Session as SessionModel, TelemetryFrame
from app.modules.analytics.schemas import SessionResponse, SessionDetailResponse, TelemetryFrameResponse
from app.modules.analytics.analytics import calculate_session_analytics
from app.modules.auth.deps import get_current_user
from app.modules.auth.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all sessions for the authenticated user.
    
    Returns sessions ordered by start_time descending (most recent first).
    """
    try:
        # Get sessions for the current user
        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id
        ).order_by(
            SessionModel.start_time.desc()
        ).offset(skip).limit(limit).all()
        
        # Get all frames for all sessions (for analytics calculation)
        session_ids = [s.id for s in sessions]
        all_frames = {}
        if session_ids:
            frames = db.query(TelemetryFrame).filter(
                TelemetryFrame.session_id.in_(session_ids)
            ).all()
            
            # Group frames by session_id
            for frame in frames:
                if frame.session_id not in all_frames:
                    all_frames[frame.session_id] = []
                all_frames[frame.session_id].append(frame)
        
        # Build response with analytics
        result = []
        for session in sessions:
            frames_for_session = all_frames.get(session.id, [])
            analytics = calculate_session_analytics(session, frames_for_session)
            
            session_dict = {
                "id": session.id,
                "user_id": session.user_id,
                "car_name": session.car_name,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "frame_count": len(frames_for_session),
                "duration_seconds": analytics["duration_seconds"],
                "top_speed": analytics["top_speed"],
                "avg_speed": analytics["avg_speed"],
                "max_rpm": analytics["max_rpm"],
            }
            result.append(SessionResponse(**session_dict))
        
        return result
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get session detail with all telemetry frames.
    
    Returns session information and all associated telemetry frames.
    """
    try:
        # Get session and verify ownership
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get all frames for this session
        frames = db.query(TelemetryFrame).filter(
            TelemetryFrame.session_id == session_id
        ).order_by(TelemetryFrame.timestamp.asc()).all()
        
        # Calculate analytics
        analytics = calculate_session_analytics(session, frames)
        
        # Build response
        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            car_name=session.car_name,
            start_time=session.start_time,
            end_time=session.end_time,
            frame_count=len(frames),
            duration_seconds=analytics["duration_seconds"],
            top_speed=analytics["top_speed"],
            avg_speed=analytics["avg_speed"],
            max_rpm=analytics["max_rpm"],
            frames=[TelemetryFrameResponse.model_validate(frame) for frame in frames]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )

