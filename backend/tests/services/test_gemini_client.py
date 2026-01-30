import pytest
from unittest.mock import MagicMock, patch
import os
from app.services.gemini_client import GeminiClient

class TestGeminiClient:
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the google.generativeai module."""
        with patch("app.services.gemini_client.genai") as mock:
            # Setup list_models return
            mock_model_1 = MagicMock()
            mock_model_1.name = "models/gemini-2.0-flash"
            mock.list_models.return_value = [mock_model_1]
            yield mock

    def test_init_success(self, mock_genai):
        """Test successful initialization with API key."""
        client = GeminiClient(api_key="test-key")
        
        mock_genai.configure.assert_called_with(api_key="test-key")
        assert client.model_name == "gemini-2.0-flash"

    def test_init_no_key(self):
        """Test init failure without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                GeminiClient()

    def test_generate_json_parsing(self, mock_genai):
        """Test JSON parsing from model response."""
        client = GeminiClient(api_key="k")
        
        # Mock response with markdown fence
        mock_response = MagicMock()
        mock_response.text = "```json\n{\"key\": \"value\"}\n```"
        client.model.generate_content.return_value = mock_response
        
        result = client.generate_json("prompt")
        
        assert result["key"] == "value"

    def test_generate_json_retry(self, mock_genai):
        """Test JSON parsing error raises ValueError."""
        client = GeminiClient(api_key="k")
        
        # Mock invalid json
        mock_response = MagicMock()
        mock_response.text = "Not JSON"
        client.model.generate_content.return_value = mock_response
        
        with pytest.raises(ValueError):
            client.generate_json("prompt")
