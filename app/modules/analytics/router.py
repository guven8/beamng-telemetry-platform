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
        
        # Get frame counts for each session
        session_ids = [s.id for s in sessions]
        frame_counts = {}
        if session_ids:
            counts = db.query(
                TelemetryFrame.session_id,
                func.count(TelemetryFrame.id).label('count')
            ).filter(
                TelemetryFrame.session_id.in_(session_ids)
            ).group_by(TelemetryFrame.session_id).all()
            
            frame_counts = {session_id: count for session_id, count in counts}
        
        # Build response with frame counts
        result = []
        for session in sessions:
            session_dict = {
                "id": session.id,
                "user_id": session.user_id,
                "car_name": session.car_name,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "frame_count": frame_counts.get(session.id, 0)
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
        
        # Build response
        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            car_name=session.car_name,
            start_time=session.start_time,
            end_time=session.end_time,
            frame_count=len(frames),
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

