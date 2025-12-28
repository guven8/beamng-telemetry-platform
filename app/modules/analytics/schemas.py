"""
Pydantic schemas for analytics API responses.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TelemetryFrameResponse(BaseModel):
    """Telemetry frame response model."""
    id: int
    timestamp: datetime
    speed: Optional[float] = None
    rpm: Optional[int] = None
    gear: Optional[int] = None
    g_force_x: Optional[float] = None
    g_force_y: Optional[float] = None
    fuel: Optional[float] = None

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    """Session response model."""
    id: int
    user_id: int
    car_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    frame_count: Optional[int] = None  # Number of frames in session

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    """Session detail response with frames."""
    frames: List[TelemetryFrameResponse] = []

    model_config = {"from_attributes": True}

