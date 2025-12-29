"""
Analytics calculation functions.

Simple, maintainable analytics calculations over telemetry frames.
KISS principle - straightforward Python calculations.
"""
from typing import List, Optional
from app.modules.analytics.models import TelemetryFrame, Session as SessionModel
from datetime import datetime, timezone


def _ensure_timezone_aware(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware (UTC).
    
    If the datetime is naive, assume it's UTC and add timezone info.
    This is a defensive measure to handle edge cases where naive datetimes
    might exist (e.g., from old database records).
    
    Args:
        dt: Datetime that may be naive or aware
        
    Returns:
        Timezone-aware datetime (UTC)
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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
        # Ensure both datetimes are timezone-aware for comparison
        end_time_aware = _ensure_timezone_aware(session.end_time)
        start_time_aware = _ensure_timezone_aware(session.start_time)
        duration = end_time_aware - start_time_aware
        analytics["duration_seconds"] = duration.total_seconds()
    elif frames:
        # If session is still active, use last frame timestamp
        last_frame_time = max(f.timestamp for f in frames)
        # Ensure both datetimes are timezone-aware for comparison
        last_frame_aware = _ensure_timezone_aware(last_frame_time)
        start_time_aware = _ensure_timezone_aware(session.start_time)
        duration = last_frame_aware - start_time_aware
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

