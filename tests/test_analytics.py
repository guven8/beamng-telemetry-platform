"""
Unit tests for analytics calculations.

Tests the calculate_session_analytics function with various scenarios.
These are pure unit tests - no database, no FastAPI, just Python objects.
"""
from datetime import datetime, timedelta, timezone
from app.modules.analytics.analytics import calculate_session_analytics


class MockSession:
    """Mock session object for testing."""
    def __init__(self, start_time, end_time=None):
        self.start_time = start_time
        self.end_time = end_time


class MockTelemetryFrame:
    """Mock telemetry frame object for testing."""
    def __init__(self, timestamp, speed=None, rpm=None):
        self.timestamp = timestamp
        self.speed = speed
        self.rpm = rpm


def test_calculate_session_analytics_with_frames():
    """Test analytics calculation with multiple frames."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(seconds=60)
    session = MockSession(start_time, end_time)
    
    frames = [
        MockTelemetryFrame(start_time + timedelta(seconds=10), speed=10.0, rpm=2000),
        MockTelemetryFrame(start_time + timedelta(seconds=20), speed=20.0, rpm=3000),
        MockTelemetryFrame(start_time + timedelta(seconds=30), speed=30.0, rpm=4000),
        MockTelemetryFrame(start_time + timedelta(seconds=40), speed=25.0, rpm=3500),
        MockTelemetryFrame(start_time + timedelta(seconds=50), speed=15.0, rpm=2500),
    ]
    
    analytics = calculate_session_analytics(session, frames)
    
    assert analytics["duration_seconds"] == 60.0, "Duration should be 60 seconds"
    assert analytics["top_speed"] == 30.0, "Top speed should be 30.0 m/s"
    assert analytics["avg_speed"] == 20.0, "Average speed should be 20.0 m/s (100/5)"
    assert analytics["max_rpm"] == 4000, "Max RPM should be 4000"


def test_calculate_session_analytics_no_frames():
    """Test analytics calculation with no frames (edge case)."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(seconds=30)
    session = MockSession(start_time, end_time)
    
    frames = []
    
    analytics = calculate_session_analytics(session, frames)
    
    assert analytics["duration_seconds"] == 30.0, "Duration should still be calculated"
    assert analytics["top_speed"] is None, "Top speed should be None with no frames"
    assert analytics["avg_speed"] is None, "Average speed should be None with no frames"
    assert analytics["max_rpm"] is None, "Max RPM should be None with no frames"


def test_calculate_session_analytics_single_frame():
    """Test analytics calculation with single frame."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(seconds=5)
    session = MockSession(start_time, end_time)
    
    frames = [
        MockTelemetryFrame(start_time + timedelta(seconds=2), speed=15.5, rpm=2500),
    ]
    
    analytics = calculate_session_analytics(session, frames)
    
    assert analytics["duration_seconds"] == 5.0, "Duration should be 5 seconds"
    assert analytics["top_speed"] == 15.5, "Top speed should be 15.5 m/s"
    assert analytics["avg_speed"] == 15.5, "Average speed should be 15.5 m/s (single value)"
    assert analytics["max_rpm"] == 2500, "Max RPM should be 2500"


def test_calculate_session_analytics_active_session():
    """Test analytics calculation for active session (no end_time, uses last frame)."""
    start_time = datetime.now(timezone.utc)
    session = MockSession(start_time, end_time=None)  # Active session
    
    last_frame_time = start_time + timedelta(seconds=45)
    frames = [
        MockTelemetryFrame(start_time + timedelta(seconds=10), speed=10.0, rpm=2000),
        MockTelemetryFrame(start_time + timedelta(seconds=20), speed=20.0, rpm=3000),
        MockTelemetryFrame(last_frame_time, speed=25.0, rpm=3500),
    ]
    
    analytics = calculate_session_analytics(session, frames)
    
    # Duration should be calculated from start_time to last frame timestamp
    expected_duration = (last_frame_time - start_time).total_seconds()
    assert analytics["duration_seconds"] == expected_duration, \
        f"Duration should be {expected_duration} seconds (from start to last frame)"
    assert analytics["top_speed"] == 25.0, "Top speed should be 25.0 m/s"
    assert analytics["avg_speed"] == (10.0 + 20.0 + 25.0) / 3, "Average speed should be mean of all speeds"


def test_calculate_session_analytics_with_none_values():
    """Test analytics calculation with frames containing None values."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(seconds=30)
    session = MockSession(start_time, end_time)
    
    frames = [
        MockTelemetryFrame(start_time + timedelta(seconds=5), speed=10.0, rpm=None),
        MockTelemetryFrame(start_time + timedelta(seconds=10), speed=None, rpm=3000),
        MockTelemetryFrame(start_time + timedelta(seconds=15), speed=20.0, rpm=4000),
        MockTelemetryFrame(start_time + timedelta(seconds=20), speed=None, rpm=None),
    ]
    
    analytics = calculate_session_analytics(session, frames)
    
    # Only frames with non-None speed should be counted
    assert analytics["top_speed"] == 20.0, "Top speed should be 20.0 m/s (ignoring None)"
    assert analytics["avg_speed"] == 15.0, "Average speed should be 15.0 m/s ((10+20)/2)"
    # Only frames with non-None rpm should be counted
    assert analytics["max_rpm"] == 4000, "Max RPM should be 4000 (ignoring None)"


def test_calculate_session_analytics_zero_speeds():
    """Test analytics calculation with zero speeds."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(seconds=20)
    session = MockSession(start_time, end_time)
    
    frames = [
        MockTelemetryFrame(start_time + timedelta(seconds=5), speed=0.0, rpm=800),
        MockTelemetryFrame(start_time + timedelta(seconds=10), speed=0.0, rpm=800),
        MockTelemetryFrame(start_time + timedelta(seconds=15), speed=5.0, rpm=1500),
    ]
    
    analytics = calculate_session_analytics(session, frames)
    
    assert analytics["top_speed"] == 5.0, "Top speed should be 5.0 m/s"
    assert analytics["avg_speed"] == (0.0 + 0.0 + 5.0) / 3, "Average speed should include zeros"
    assert analytics["max_rpm"] == 1500, "Max RPM should be 1500"
