import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import os
from app.services.gemini_client import GeminiClient

class TestGeminiClient:

    @pytest.fixture
    def mock_genai(self):
        """Mock the google.genai module."""
        with patch("app.services.gemini_client.genai") as mock:
            # Setup client mock with models.list() return
            mock_client = MagicMock()
            mock_model_1 = MagicMock()
            mock_model_1.name = "models/gemini-3-flash-preview"
            mock_client.models.list.return_value = [mock_model_1]
            mock.Client.return_value = mock_client
            yield mock

    def test_init_success(self, mock_genai):
        """Test successful initialization with API key."""
        client = GeminiClient(api_key="test-key")

        mock_genai.Client.assert_called_with(api_key="test-key")
        assert client.model_name == "gemini-3-flash-preview"

    def test_init_no_key(self):
        """Test init failure without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                GeminiClient()

    def test_generate_json_parsing(self, mock_genai):
        """Test JSON parsing from model response."""
        client = GeminiClient(api_key="k")

        # Mock response
        mock_response = MagicMock()
        mock_response.text = '{"key": "value"}'
        client.client.models.generate_content.return_value = mock_response

        result = client.generate_json("prompt")

        assert result["key"] == "value"

    def test_generate_json_with_markdown_fence(self, mock_genai):
        """Test JSON parsing strips markdown fences (defensive)."""
        client = GeminiClient(api_key="k")

        mock_response = MagicMock()
        mock_response.text = "```json\n{\"key\": \"value\"}\n```"
        client.client.models.generate_content.return_value = mock_response

        result = client.generate_json("prompt")

        assert result["key"] == "value"

    def test_generate_json_invalid(self, mock_genai):
        """Test JSON parsing error raises ValueError."""
        client = GeminiClient(api_key="k")

        # Mock invalid json
        mock_response = MagicMock()
        mock_response.text = "Not JSON"
        client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError):
            client.generate_json("prompt")

    def test_generate_content(self, mock_genai):
        """Test single-turn content generation."""
        client = GeminiClient(api_key="k")

        mock_response = MagicMock()
        mock_response.text = "Generated text"
        client.client.models.generate_content.return_value = mock_response

        result = client.generate_content("prompt", system_instruction="Be helpful")

        assert result == "Generated text"
        client.client.models.generate_content.assert_called_once()

    def test_generate_content_with_history(self, mock_genai):
        """Test multi-turn content generation via chats API."""
        client = GeminiClient(api_key="k")

        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Chat response"
        mock_chat.send_message.return_value = mock_response
        client.client.chats.create.return_value = mock_chat

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = client.generate_content_with_history(
            prompt="Follow up",
            history=history,
            system_instruction="Be concise",
        )

        assert result == "Chat response"
        client.client.chats.create.assert_called_once()
        mock_chat.send_message.assert_called_once_with(message="Follow up")
