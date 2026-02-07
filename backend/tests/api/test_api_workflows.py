import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestWorkflowsAPI:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Mock external services for workflows API tests."""
        with patch("app.api.publications.minio_service") as mock_minio, \
             patch("app.api.publications.db_service") as mock_db:
            mock_minio.upload_file.return_value = "measurements/uploads/test/file.pdf"
            mock_minio.MEASUREMENTS_BUCKET = "measurements"
            mock_session = MagicMock()
            mock_session.session_id = "sess_test"
            mock_db.create_session = AsyncMock(return_value=mock_session)
            mock_db.get_session_by_upload = AsyncMock(return_value=None)
            yield

    def test_assemble_workflow_fallback(self, app_client):
        """POST /api/v1/workflows/assemble returns mock graph when no agents."""
        with patch("app.api.workflows.AGENTS_AVAILABLE", False):
            response = app_client.post(
                "/api/v1/workflows/assemble",
                json={"assay_id": "assay_1", "upload_id": "pub_test"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["workflow_id"].startswith("wf_")
        assert "graph" in data
        assert len(data["graph"]["nodes"]) > 0
        assert len(data["graph"]["edges"]) > 0

    def test_get_workflow_success(self, app_client):
        """GET /api/v1/workflows/{workflow_id} returns workflow data."""
        from app.api.workflows import _workflows
        _workflows["wf_test"] = {
            "workflow_id": "wf_test",
            "graph": {"nodes": [], "edges": []},
            "status": "draft",
        }

        try:
            response = app_client.get("/api/v1/workflows/wf_test")
            assert response.status_code == 200
            assert response.json()["workflow_id"] == "wf_test"
        finally:
            _workflows.pop("wf_test", None)

    def test_get_workflow_not_found(self, app_client):
        """GET /api/v1/workflows/{workflow_id} returns 404 for unknown id."""
        response = app_client.get("/api/v1/workflows/wf_nonexistent")
        assert response.status_code == 404

    def test_save_workflow_update(self, app_client):
        """PUT /api/v1/workflows/{workflow_id} saves workflow graph."""
        from app.api.workflows import _workflows
        _workflows["wf_save"] = {
            "workflow_id": "wf_save",
            "graph": {"nodes": [], "edges": []},
            "status": "draft",
        }

        try:
            response = app_client.put(
                "/api/v1/workflows/wf_save",
                json={"graph": {"nodes": [], "edges": []}},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["workflow_id"] == "wf_save"
            assert "updated_at" in data
        finally:
            _workflows.pop("wf_save", None)

    def test_assemble_response_structure(self, app_client):
        """Validate that assemble response has correct schema."""
        with patch("app.api.workflows.AGENTS_AVAILABLE", False):
            response = app_client.post(
                "/api/v1/workflows/assemble",
                json={"assay_id": "assay_1"},
            )

        data = response.json()
        # Verify schema
        assert "workflow_id" in data
        assert "graph" in data
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph

        # Verify node structure
        for node in graph["nodes"]:
            assert "id" in node
            assert "type" in node
            assert "position" in node
            assert "data" in node
            assert "x" in node["position"]
            assert "y" in node["position"]

        # Verify edge structure
        for edge in graph["edges"]:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
