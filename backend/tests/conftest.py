import pytest
from unittest.mock import MagicMock, patch, PropertyMock, AsyncMock
import os
import sys

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies that might not be installed in the test environment
sys.modules['fitz'] = MagicMock()
sys.modules['minio'] = MagicMock()
sys.modules['minio.error'] = MagicMock()
sys.modules['asyncpg'] = MagicMock()

# Mock google-genai SDK (may not be installed in Docker/CI)
try:
    from google import genai as _test_genai  # noqa: F401
except (ImportError, AttributeError):
    _mock_genai_mod = MagicMock()
    _mock_types_mod = MagicMock()
    _mock_genai_mod.types = _mock_types_mod
    # Ensure the google namespace exists
    if 'google' not in sys.modules:
        sys.modules['google'] = MagicMock()
    sys.modules['google'].genai = _mock_genai_mod
    sys.modules['google.genai'] = _mock_genai_mod
    sys.modules['google.genai.types'] = _mock_types_mod

# Set dummy API key to avoid initialization errors during collection
os.environ["GEMINI_API_KEY"] = "test-key"


@pytest.fixture
def mock_genai():
    """Mock the google.genai module for GeminiClient."""
    with patch("app.services.gemini_client.genai") as mock:
        # Mock the Client
        mock_client = MagicMock()
        mock.Client.return_value = mock_client

        # Mock files.upload
        mock_file_ref = MagicMock()
        mock_client.files.upload.return_value = mock_file_ref

        # Mock models.generate_content response
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = '{"thought_process": "test", "investigation": {"title": "Test", "description": "Test desc", "study_factors": [], "metadata": []}, "confidence_scores": [], "identified_tools": [], "identified_models": [], "identified_measurements": []}'
        mock_response.candidates = []
        mock_client.models.generate_content.return_value = mock_response

        yield {
            "genai": mock,
            "client": mock_client,
            "file_ref": mock_file_ref,
            "response": mock_response,
        }


@pytest.fixture
def mock_gemini_client(mock_genai):
    """Create a mocked GeminiClient instance."""
    from app.services.gemini_client import GeminiClient
    client = GeminiClient()
    return client


@pytest.fixture
def mock_minio_service():
    """Mock the MinIO service."""
    with patch("app.services.minio_client.minio_service") as mock_service:
        yield mock_service


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for tool execution checks."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def sample_cwl_workflow():
    """A valid CWL v1.3 Workflow YAML string."""
    return """
cwlVersion: v1.3
class: Workflow
id: test-workflow
label: Test Workflow
doc: A test workflow for unit testing

inputs:
  input_data:
    type: File
    doc: Input data file

outputs:
  output_data:
    type: File
    outputSource: step2/output_file

steps:
  step1:
    run: tools/step1.cwl
    in:
      input_file: input_data
    out: [output_file]

  step2:
    run: tools/step2.cwl
    in:
      input_file: step1/output_file
    out: [output_file]
"""


@pytest.fixture
def sample_cwl_tool():
    """A valid CWL v1.3 CommandLineTool YAML string."""
    return """
cwlVersion: v1.3
class: CommandLineTool
id: test-tool
label: Test Tool
baseCommand: ["python", "-c"]
inputs:
  input_file:
    type: File
outputs:
  output_file:
    type: File
    outputBinding:
      glob: "*.out"
requirements:
  - class: DockerRequirement
    dockerPull: python:3.11-slim
"""


@pytest.fixture
def mock_minio_client():
    """Patches the Minio constructor in minio_client module."""
    with patch("app.services.minio_client.Minio") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_httpx_client():
    """Patches httpx.AsyncClient for AirflowClient tests."""
    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        # Make it usable as async context manager
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        yield mock_instance


@pytest.fixture
def reset_config_singleton():
    """Reset AppConfig singleton between tests."""
    from app.config import AppConfig
    original = AppConfig._instance
    AppConfig._instance = None
    yield
    AppConfig._instance = original


@pytest.fixture
def reset_prompt_manager_singleton():
    """Reset PromptManager singleton between tests."""
    from app.services.prompt_manager import PromptManager
    original = PromptManager._instance
    PromptManager._instance = None
    yield
    PromptManager._instance = original


@pytest.fixture
def app_client():
    """FastAPI TestClient from app.main with mocked startup deps."""
    with patch("app.main.db_service") as mock_db, \
         patch("app.main.minio_service") as mock_minio:
        mock_db.connect = AsyncMock()
        mock_db.disconnect = AsyncMock()
        mock_minio.ensure_buckets_exist = MagicMock()

        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            yield client
