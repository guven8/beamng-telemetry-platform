"""
Pytest configuration and shared fixtures for tests.
"""
import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Override DATABASE_URL for tests - will use temp file per test
# Must be set before importing app modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["SEEDED_USER_PASSWORD"] = "local"

from app.modules.analytics.database import Base, get_db
from app.modules.analytics.models import Session, TelemetryFrame  # noqa: F401 - needed for Base.metadata
from app.main import app


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    Uses a temporary SQLite file database for thread safety with TestClient.
    """
    # Create a temporary file for the database
    # Using a file instead of :memory: ensures thread safety with TestClient
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close file descriptor, we'll use the path
    
    try:
        # Create SQLite engine pointing to temp file
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
            engine.dispose()
    finally:
        # Clean up temp file
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture(scope="function")
def test_app(db_session):
    """
    Create a test FastAPI app with overridden database dependency.
    """
    # Tables are already created in db_session fixture
    # Override get_db dependency to use test database session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close session here, let fixture handle it
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app):
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(test_app)


@pytest.fixture
def auth_token(client):
    """
    Get an authentication token for testing.
    Returns the JWT token string.
    """
    response = client.post(
        "/api/auth/login",
        json={"username": "local", "password": "local"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]
