import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.execution import ExecutionStatus


class TestExecutionsAPI:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Mock external services for executions API tests."""
        with patch("app.api.publications.minio_service") as mock_minio, \
             patch("app.api.publications.db_service") as mock_db, \
             patch("app.api.executions.minio_service") as mock_minio_exec, \
             patch("app.api.executions.db_service") as mock_db_exec, \
             patch("app.api.executions._run_mock_execution", new_callable=AsyncMock):
            mock_minio.upload_file.return_value = "path"
            mock_minio.MEASUREMENTS_BUCKET = "measurements"
            mock_session = MagicMock()
            mock_session.session_id = "sess_test"
            mock_db.create_session = AsyncMock(return_value=mock_session)
            mock_db.get_session_by_upload = AsyncMock(return_value=None)

            mock_minio_exec.PROCESS_BUCKET = "process"
            mock_minio_exec.get_presigned_download_url.return_value = "https://download-url"
            mock_minio_exec.download_file.side_effect = Exception("Not found")
            yield

    def test_create_execution(self, app_client):
        """POST /api/v1/executions returns 202 with execution_id."""
        with patch("app.api.executions.EXECUTION_ENGINE_AVAILABLE", False):
            response = app_client.post(
                "/api/v1/executions",
                json={"workflow_id": "wf_test"},
            )

        assert response.status_code == 202
        data = response.json()
        assert "execution_id" in data
        assert data["status"] == "queued"

    def test_get_execution_status(self, app_client):
        """GET /api/v1/executions/{execution_id} returns status."""
        from app.api.executions import _executions
        _executions["exec_status"] = {
            "execution_id": "exec_status",
            "workflow_id": "wf_test",
            "status": ExecutionStatus.RUNNING,
            "overall_progress": 50,
            "node_statuses": {
                "step1": {"status": "completed", "progress": 100},
            },
            "logs": [],
        }

        try:
            with patch("app.api.executions.EXECUTION_ENGINE_AVAILABLE", False):
                response = app_client.get("/api/v1/executions/exec_status")

            assert response.status_code == 200
            data = response.json()
            assert data["execution_id"] == "exec_status"
            assert data["status"] == "running"
            assert data["overall_progress"] == 50
        finally:
            _executions.pop("exec_status", None)

    def test_get_execution_status_not_found(self, app_client):
        """GET /api/v1/executions/{execution_id} returns 404 for unknown id."""
        with patch("app.api.executions.EXECUTION_ENGINE_AVAILABLE", False):
            response = app_client.get("/api/v1/executions/exec_nonexistent")

        assert response.status_code == 404

    def test_get_execution_results_empty(self, app_client):
        """GET /api/v1/executions/{execution_id}/results returns empty when no results."""
        from app.api.executions import _executions
        _executions["exec_noresult"] = {
            "execution_id": "exec_noresult",
            "workflow_id": "wf_test",
            "status": ExecutionStatus.SUCCESS,
        }

        try:
            with patch("app.api.executions.EXECUTION_ENGINE_AVAILABLE", False):
                response = app_client.get("/api/v1/executions/exec_noresult/results")

            assert response.status_code == 200
            data = response.json()
            assert data["files"] == []
        finally:
            _executions.pop("exec_noresult", None)

    def test_get_execution_provenance(self, app_client):
        """GET /api/v1/executions/{execution_id}/provenance returns provenance data."""
        from app.api.executions import _executions
        _executions["exec_prov"] = {
            "execution_id": "exec_prov",
            "workflow_id": "wf_test",
            "status": ExecutionStatus.SUCCESS,
            "provenance": {
                "execution_id": "exec_prov",
                "workflow_id": "wf_test",
                "entities": {"input": {}, "output": {}},
            },
        }

        try:
            with patch("app.api.executions.EXECUTION_ENGINE_AVAILABLE", False):
                response = app_client.get("/api/v1/executions/exec_prov/provenance")

            assert response.status_code == 200
            data = response.json()
            assert data["execution_id"] == "exec_prov"
            assert "entities" in data
        finally:
            _executions.pop("exec_prov", None)
