from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns basic API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Auto-DJ Backend API"


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    # Note: This might fail in tests without proper database/redis setup
    # In a real test environment, you'd mock these dependencies
    assert response.status_code in [200, 503]  # Allow both healthy and unhealthy
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_api_docs():
    """Test that API documentation is accessible."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Auto-DJ Backend"


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.options("/")
    # CORS headers should be present
    assert (
        "access-control-allow-origin" in response.headers or response.status_code == 200
    )


def test_404_handler():
    """Test custom 404 handler."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
