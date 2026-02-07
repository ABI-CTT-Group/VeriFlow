import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


class TestPublicationsAPI:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Mock external services for publications API tests."""
        with patch("app.api.publications.minio_service") as mock_minio, \
             patch("app.api.publications.db_service") as mock_db:
            mock_minio.upload_file.return_value = "measurements/uploads/test/file.pdf"
            mock_minio.MEASUREMENTS_BUCKET = "measurements"

            mock_session = MagicMock()
            mock_session.session_id = "sess_test123"
            mock_db.create_session = AsyncMock(return_value=mock_session)
            mock_db.get_session_by_upload = AsyncMock(return_value=None)

            self.mock_minio = mock_minio
            self.mock_db = mock_db
            yield

    def test_upload_publication_success(self, app_client):
        """POST /api/v1/publications/upload returns upload_id."""
        with patch("app.api.publications.SCHOLAR_AVAILABLE", False):
            response = app_client.post(
                "/api/v1/publications/upload",
                files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert data["upload_id"].startswith("pub_")
        assert data["filename"] == "test.pdf"

    def test_get_study_design_processing(self, app_client):
        """GET /api/v1/study-design/{upload_id} returns processing status."""
        from app.api.publications import _upload_cache
        _upload_cache["pub_test123"] = {"status": "processing", "result": None}

        try:
            response = app_client.get("/api/v1/study-design/pub_test123")
            assert response.status_code == 200
            assert response.json()["status"] == "processing"
        finally:
            _upload_cache.pop("pub_test123", None)

    def test_get_study_design_completed(self, app_client):
        """GET /api/v1/study-design/{upload_id} returns completed result."""
        from app.api.publications import _upload_cache
        _upload_cache["pub_done"] = {
            "status": "completed",
            "result": {
                "isa_json": {"title": "Test Study"},
                "confidence_scores": {"title": 0.95},
            },
        }

        try:
            response = app_client.get("/api/v1/study-design/pub_done")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["hierarchy"]["investigation"]["title"] == "Test Study"
        finally:
            _upload_cache.pop("pub_done", None)

    def test_get_study_design_not_found(self, app_client):
        """GET /api/v1/study-design/{upload_id} returns 404 for unknown id."""
        response = app_client.get("/api/v1/study-design/pub_nonexistent")
        assert response.status_code == 404

    def test_load_example_success(self, app_client):
        """POST /api/v1/publications/load-example loads mama-mia example."""
        examples_dir = Path(__file__).parent.parent.parent / "examples" / "mama-mia"
        if not (examples_dir / "ground_truth_isa.json").exists():
            pytest.skip("mama-mia example not found")

        response = app_client.post(
            "/api/v1/publications/load-example",
            json={"example_name": "mama-mia"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "upload_id" in data

    def test_add_additional_info(self, app_client):
        """POST /api/v1/publications/{upload_id}/additional-info stores info."""
        from app.api.publications import _upload_cache
        _upload_cache["pub_info"] = {"status": "processing", "result": None}

        try:
            response = app_client.post(
                "/api/v1/publications/pub_info/additional-info",
                json={"info": "The study uses 3T MRI scanner."},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert _upload_cache["pub_info"]["additional_info"] == "The study uses 3T MRI scanner."
        finally:
            _upload_cache.pop("pub_info", None)
