"""
Telemetry data schemas for parsed UDP packets.

Represents a single telemetry sample from BeamNG.drive via OutGauge protocol.
"""
from datetime import datetime
from pydantic import BaseModel


class TelemetrySample(BaseModel):
    """
    A single telemetry sample parsed from OutGauge UDP packet.
    
    All fields are optional to handle incomplete or malformed packets gracefully.
    """
    speed: float | None = None  # Speed in m/s (OutGauge provides this)
    rpm: int | None = None  # Engine RPM
    gear: int | None = None  # Current gear (0 = neutral, -1 = reverse)
    g_force_x: float | None = None  # Lateral G-force (left/right)
    g_force_y: float | None = None  # Longitudinal G-force (forward/backward)
    timestamp: datetime  # When this sample was received/parsed
    raw_bytes: bytes | None = None  # Optional: original packet bytes for debugging

