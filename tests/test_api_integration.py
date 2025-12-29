"""
API integration tests using FastAPI TestClient.

Tests the API endpoints to ensure they behave correctly.
Uses in-memory SQLite database for testing.
"""
import pytest
from fastapi import status


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data


def test_auth_login_success(client):
    """Test successful login with correct credentials."""
    response = client.post(
        "/api/auth/login",
        json={"username": "local", "password": "local"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_auth_login_failure_wrong_password(client):
    """Test login failure with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={"username": "local", "password": "wrongpassword"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    assert "incorrect" in data["detail"].lower() or "invalid" in data["detail"].lower()


def test_auth_login_failure_wrong_username(client):
    """Test login failure with wrong username."""
    response = client.post(
        "/api/auth/login",
        json={"username": "wronguser", "password": "local"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data


def test_sessions_requires_auth(client):
    """Test that sessions endpoint requires authentication."""
    response = client.get("/api/sessions")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN or response.status_code == status.HTTP_401_UNAUTHORIZED


def test_sessions_empty_initially(client, auth_token):
    """Test that sessions endpoint returns empty list for new user."""
    response = client.get(
        "/api/sessions",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # Should be empty initially


def test_sessions_with_token(client, auth_token):
    """Test sessions endpoint with valid token."""
    response = client.get(
        "/api/sessions",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_sessions_invalid_token(client):
    """Test sessions endpoint with invalid token."""
    response = client.get(
        "/api/sessions",
        headers={"Authorization": "Bearer invalid-token-here"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED or response.status_code == status.HTTP_403_FORBIDDEN


def test_telemetry_debug_endpoint(client):
    """Test the telemetry debug endpoint."""
    response = client.get("/api/telemetry/debug")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "queue_size" in data
    assert "udp_port" in data
    assert isinstance(data["queue_size"], int)
    assert isinstance(data["udp_port"], int)
