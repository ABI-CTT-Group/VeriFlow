import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies that might not be installed in the test environment
# This allows tests to be collected even if requirements aren't fully installed
sys.modules['fitz'] = MagicMock()
sys.modules['minio'] = MagicMock()
sys.modules['minio'] = MagicMock()
sys.modules['minio.error'] = MagicMock()

# Set dummy API key to avoid initialization errors during collection
os.environ["GEMINI_API_KEY"] = "test-key"

@pytest.fixture
def mock_gemini_client():
    """Mock the GeminiClient to avoid actual API calls."""
    with patch("app.services.gemini_client.GeminiClient") as MockClient:
        client_instance = MockClient.return_value
        # Default mock behavior for common methods
        client_instance.generate_json.return_value = {}
        client_instance.generate_content.return_value = "Mock content"
        yield client_instance

@pytest.fixture
def mock_minio_service():
    """Mock the MinIO service."""
    with patch("app.services.minio_client.minio_service") as mock_service:
        yield mock_service

@pytest.fixture
def mock_pymupdf():
    """Mock fitz (PyMuPDF) for PDF processing."""
    with patch("fitz.open") as mock_open:
        # Create a mock document with pages
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Mock PDF Text Content"
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_open.return_value = mock_doc
        yield mock_open

@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for tool execution checks."""
    with patch("subprocess.run") as mock_run:
        yield mock_run
