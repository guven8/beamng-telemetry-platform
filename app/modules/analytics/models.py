"""
Database models for sessions and telemetry frames.

Defines SQLAlchemy models for persistence of telemetry data.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.modules.analytics.database import Base


class Session(Base):
    """
    Telemetry session model.
    
    Represents a driving session that starts when movement begins
    and ends after inactivity timeout.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    car_name = Column(String, nullable=True)  # Optional for MVP
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Relationship to telemetry frames
    frames = relationship("TelemetryFrame", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, start={self.start_time})>"


class TelemetryFrame(Base):
    """
    Individual telemetry frame model.
    
    Stores a single telemetry sample from a session.
    """
    __tablename__ = "telemetry_frames"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    speed = Column(Float, nullable=True)  # m/s
    rpm = Column(Integer, nullable=True)
    gear = Column(Integer, nullable=True)  # -1=reverse, 0=neutral, 1-9=gears
    g_force_x = Column(Float, nullable=True)
    g_force_y = Column(Float, nullable=True)
    fuel = Column(Float, nullable=True)  # Optional
    
    # Relationship to session
    session = relationship("Session", back_populates="frames")

    def __repr__(self):
        return f"<TelemetryFrame(id={self.id}, session_id={self.session_id}, speed={self.speed})>"



