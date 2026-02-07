import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import os
import sys

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies that might not be installed in the test environment
sys.modules['fitz'] = MagicMock()
sys.modules['minio'] = MagicMock()
sys.modules['minio.error'] = MagicMock()

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
