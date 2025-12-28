"""
Analytics calculation functions.

Simple, maintainable analytics calculations over telemetry frames.
KISS principle - straightforward Python calculations.
"""
from typing import List, Optional
from app.modules.analytics.models import TelemetryFrame, Session as SessionModel
from datetime import datetime


def calculate_session_analytics(
    session: SessionModel,
    frames: List[TelemetryFrame]
) -> dict:
    """
    Calculate analytics for a session from its frames.
    
    Args:
        session: Session model
        frames: List of TelemetryFrame objects for this session
        
    Returns:
        Dictionary with analytics: duration_seconds, top_speed, avg_speed, max_rpm
    """
    analytics = {
        "duration_seconds": None,
        "top_speed": None,
        "avg_speed": None,
        "max_rpm": None,
    }
    
    # Calculate duration
    if session.end_time:
        duration = session.end_time - session.start_time
        analytics["duration_seconds"] = duration.total_seconds()
    elif frames:
        # If session is still active, use last frame timestamp
        last_frame_time = max(f.timestamp for f in frames)
        duration = last_frame_time - session.start_time
        analytics["duration_seconds"] = duration.total_seconds()
    
    if not frames:
        return analytics
    
    # Calculate speed analytics (in m/s)
    speeds = [f.speed for f in frames if f.speed is not None]
    if speeds:
        analytics["top_speed"] = max(speeds)
        analytics["avg_speed"] = sum(speeds) / len(speeds)
    
    # Calculate max RPM
    rpms = [f.rpm for f in frames if f.rpm is not None]
    if rpms:
        analytics["max_rpm"] = max(rpms)
    
    return analytics

