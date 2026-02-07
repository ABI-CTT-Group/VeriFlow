import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services.airflow_client import AirflowClient, TaskInstanceState


class TestAirflowClient:

    @pytest.fixture
    def client(self):
        return AirflowClient(base_url="http://test:8080", username="test", password="test")

    # --- health_check ---

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test health check returns True on 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.get = AsyncMock(return_value=mock_response)

            result = await client.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check returns False on connection error."""
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            result = await client.health_check()
            assert result is False

    # --- trigger_dag ---

    @pytest.mark.asyncio
    async def test_trigger_dag_success(self, client):
        """Test successful DAG trigger returns dag_run_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"dag_run_id": "run_123"}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http
        client._token = "fake-token"

        result = await client.trigger_dag("test_dag")
        assert result == "run_123"

    @pytest.mark.asyncio
    async def test_trigger_dag_not_found(self, client):
        """Test trigger_dag returns None when DAG not found (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http
        client._token = "fake-token"

        result = await client.trigger_dag("nonexistent_dag")
        assert result is None

    # --- get_dag_run ---

    @pytest.mark.asyncio
    async def test_get_dag_run_success(self, client):
        """Test get_dag_run returns run data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"dag_run_id": "run_123", "state": "running"}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http
        client._token = "fake-token"

        result = await client.get_dag_run("test_dag", "run_123")
        assert result["state"] == "running"

    @pytest.mark.asyncio
    async def test_get_dag_run_not_found(self, client):
        """Test get_dag_run returns None for 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http
        client._token = "fake-token"

        result = await client.get_dag_run("test_dag", "nonexistent")
        assert result is None

    # --- calculate_progress ---

    def test_calculate_progress_all_complete(self, client):
        """Test 100% progress when all tasks complete."""
        tasks = [
            {"state": "success"},
            {"state": "success"},
            {"state": "skipped"},
        ]
        assert client.calculate_progress(tasks) == 100

    def test_calculate_progress_half(self, client):
        """Test 50% progress when half of tasks complete."""
        tasks = [
            {"state": "success"},
            {"state": "running"},
        ]
        assert client.calculate_progress(tasks) == 50

    def test_calculate_progress_empty(self, client):
        """Test 0% progress with no tasks."""
        assert client.calculate_progress([]) == 0

    # --- map_task_state ---

    def test_map_task_state_running(self, client):
        """Test mapping running state."""
        assert client.map_task_state("running") == "running"

    def test_map_task_state_success(self, client):
        """Test mapping success state."""
        assert client.map_task_state("success") == "completed"

    def test_map_task_state_failed(self, client):
        """Test mapping failed state."""
        assert client.map_task_state("failed") == "error"
