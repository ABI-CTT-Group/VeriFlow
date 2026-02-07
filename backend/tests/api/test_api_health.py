import pytest


class TestHealthAPI:

    def test_health_endpoint(self, app_client):
        """GET /health returns healthy status."""
        response = app_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, app_client):
        """GET / returns API info."""
        response = app_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "VeriFlow API"
        assert "endpoints" in data
        assert "publications" in data["endpoints"]

    def test_docs_available(self, app_client):
        """GET /docs returns 200."""
        response = app_client.get("/docs")

        assert response.status_code == 200
