import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.execution_engine import ExecutionEngine
from app.models.execution import ExecutionStatus, LogLevel
from app.models.cwl import CWLParseResult, CWLValidationResult


class TestExecutionEngine:

    @pytest.fixture
    def mock_services(self):
        """Create mocked service dependencies for ExecutionEngine."""
        mock_parser = MagicMock()
        mock_dag_gen = MagicMock()
        mock_airflow = MagicMock()
        mock_docker = MagicMock()
        return mock_parser, mock_dag_gen, mock_airflow, mock_docker

    @pytest.fixture
    def engine(self, mock_services):
        """Create ExecutionEngine with mocked dependencies."""
        mock_parser, mock_dag_gen, mock_airflow, mock_docker = mock_services
        return ExecutionEngine(
            cwl_parser=mock_parser,
            dag_generator=mock_dag_gen,
            airflow_client=mock_airflow,
            docker_builder=mock_docker,
        )

    @pytest.mark.asyncio
    async def test_prepare_execution_success(self, engine, mock_services):
        """Test successful execution preparation."""
        mock_parser = mock_services[0]
        mock_dag_gen = mock_services[1]
        mock_docker = mock_services[3]

        # Mock successful parse
        mock_workflow = MagicMock()
        mock_workflow.step_order = ["step1"]
        mock_workflow.tools = {"step1": MagicMock()}
        mock_workflow.step_dependencies = {}

        mock_parse_result = MagicMock()
        mock_parse_result.success = True
        mock_parse_result.workflow = mock_workflow
        mock_parse_result.validation = MagicMock(valid=True)
        mock_parser.parse_workflow.return_value = mock_parse_result

        mock_dag_gen.generate_dag.return_value = "/path/to/dag.py"
        mock_dag_gen._generate_dag_id.return_value = "veriflow_test_exec"

        mock_docker.generate_dockerfile.return_value = "FROM python:3.11"
        mock_docker.get_image_name.return_value = "python:3.11-slim"

        result = await engine.prepare_execution("cwl content", "wf_123")

        assert result["success"] is True
        assert "execution_id" in result
        assert result["dag_id"] == "veriflow_test_exec"

    @pytest.mark.asyncio
    async def test_prepare_execution_parse_failure(self, engine, mock_services):
        """Test execution preparation fails on CWL parse error."""
        mock_parser = mock_services[0]

        mock_parse_result = MagicMock()
        mock_parse_result.success = False
        mock_parse_result.error = "Invalid CWL syntax"
        mock_parse_result.validation = None
        mock_parser.parse_workflow.return_value = mock_parse_result

        result = await engine.prepare_execution("bad cwl", "wf_123")

        assert result["success"] is False
        assert "CWL parsing failed" in result["error"]

    def test_get_execution_status_exists(self, engine):
        """Test getting status of an existing execution."""
        engine.active_executions["exec_123"] = {
            "status": ExecutionStatus.RUNNING,
            "overall_progress": 50,
        }

        result = engine.get_execution_status("exec_123")
        assert result is not None
        assert result["status"] == ExecutionStatus.RUNNING

    def test_get_execution_status_not_exists(self, engine):
        """Test getting status of non-existent execution returns None."""
        assert engine.get_execution_status("nonexistent") is None

    def test_get_execution_logs_exists(self, engine):
        """Test getting logs for an existing execution."""
        engine.active_executions["exec_123"] = {
            "logs": [
                {"level": "INFO", "message": "Started"},
                {"level": "INFO", "message": "Step 1 done"},
            ],
        }

        logs = engine.get_execution_logs("exec_123")
        assert len(logs) == 2
        assert logs[0]["message"] == "Started"

    def test_get_execution_logs_empty(self, engine):
        """Test getting logs for non-existent execution returns empty list."""
        assert engine.get_execution_logs("nonexistent") == []

    @pytest.mark.asyncio
    async def test_cancel_execution(self, engine):
        """Test cancelling a running execution."""
        engine.active_executions["exec_123"] = {
            "status": ExecutionStatus.RUNNING,
            "logs": [],
        }

        result = await engine.cancel_execution("exec_123")
        assert result is True
        assert engine.active_executions["exec_123"]["status"] == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_cancel_execution_not_exists(self, engine):
        """Test cancelling a non-existent execution returns False."""
        result = await engine.cancel_execution("nonexistent")
        assert result is False

    def test_generate_provenance(self, engine):
        """Test provenance generation for an execution."""
        engine.active_executions["exec_123"] = {
            "workflow_id": "wf_456",
            "step_order": ["step1", "step2"],
        }

        prov = engine._generate_provenance("exec_123")
        assert prov["execution_id"] == "exec_123"
        assert prov["workflow_id"] == "wf_456"
        assert len(prov["activities"]) == 2

    def test_add_log(self, engine):
        """Test adding a log entry to an execution."""
        engine.active_executions["exec_123"] = {"logs": []}

        engine._add_log("exec_123", LogLevel.INFO, "Test message", node_id="step1")

        logs = engine.active_executions["exec_123"]["logs"]
        assert len(logs) == 1
        assert logs[0]["message"] == "Test message"
        assert logs[0]["node_id"] == "step1"
