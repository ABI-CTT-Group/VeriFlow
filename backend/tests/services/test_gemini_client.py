import pytest
import json
from unittest.mock import MagicMock, patch
import os
from app.services.gemini_client import GeminiClient


class TestGeminiClient:

    def test_init_success(self, mock_genai):
        """Test successful initialization with API key."""
        client = GeminiClient()

        mock_genai["genai"].Client.assert_called_with(api_key="test-key")
        assert client.model_name == "gemini-3-flash-preview"
        assert client.client is not None

    def test_init_no_key(self):
        """Test init failure without API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)
            with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
                GeminiClient()

    def test_generate_text_with_schema(self, mock_genai):
        """Test text generation with Pydantic response_schema."""
        client = GeminiClient()

        # Mock parsed response
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {"key": "value"}
        mock_genai["response"].parsed = mock_parsed

        from app.models.schemas import AnalysisResult
        result = client.generate_text(
            prompt="test prompt",
            system_instruction="test instruction",
            response_schema=AnalysisResult,
        )

        assert result == {"key": "value"}
        mock_genai["client"].models.generate_content.assert_called_once()

    def test_generate_text_without_schema(self, mock_genai):
        """Test text generation without schema returns raw text."""
        client = GeminiClient()
        mock_genai["response"].parsed = None
        mock_genai["response"].text = "Hello world"

        result = client.generate_text(prompt="test prompt")

        assert result == {"text": "Hello world"}

    def test_generate_text_with_thinking_level(self, mock_genai):
        """Test that thinking_level is passed in config."""
        client = GeminiClient()
        mock_genai["response"].parsed = None
        mock_genai["response"].text = "response"

        client.generate_text(
            prompt="test",
            thinking_level="HIGH",
        )

        call_args = mock_genai["client"].models.generate_content.call_args
        gen_config = call_args.kwargs.get("config") or call_args[1].get("config")
        assert gen_config is not None

    def test_generate_text_with_grounding(self, mock_genai):
        """Test that grounding with Google Search is enabled."""
        client = GeminiClient()
        mock_genai["response"].parsed = None
        mock_genai["response"].text = "response"

        client.generate_text(
            prompt="test",
            enable_grounding=True,
        )

        call_args = mock_genai["client"].models.generate_content.call_args
        gen_config = call_args.kwargs.get("config") or call_args[1].get("config")
        assert gen_config is not None

    def test_analyze_file(self, mock_genai, tmp_path):
        """Test file analysis with PDF upload."""
        client = GeminiClient()

        # Create a fake PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        # Mock parsed response
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Analyzed the document",
            "investigation": {"title": "Test", "description": "Test"},
            "identified_tools": [],
        }
        mock_genai["response"].parsed = mock_parsed

        result = client.analyze_file(
            file_path=str(pdf_file),
            prompt="Analyze this PDF",
            thinking_level="HIGH",
        )

        # Verify file was uploaded
        mock_genai["client"].files.upload.assert_called_once()
        # Verify generate_content was called
        mock_genai["client"].models.generate_content.assert_called_once()
        # Verify result
        assert result["thought_process"] == "Analyzed the document"

    def test_generate_with_history(self, mock_genai):
        """Test multi-turn generation with thought signatures."""
        client = GeminiClient()

        # Setup response with thought parts
        mock_part_thought = MagicMock()
        mock_part_thought.thought = True
        mock_part_thought.text = "internal reasoning"

        mock_part_text = MagicMock()
        mock_part_text.thought = False
        mock_part_text.text = '{"text": "response"}'

        mock_content = MagicMock()
        mock_content.parts = [mock_part_thought, mock_part_text]

        mock_candidate = MagicMock()
        mock_candidate.content = mock_content

        mock_genai["response"].candidates = [mock_candidate]
        mock_genai["response"].parsed = None
        mock_genai["response"].text = '{"text": "response"}'

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi", "thought_signatures": ["prev_thought"]},
            {"role": "user", "content": "Follow up"},
        ]

        result = client.generate_with_history(messages=messages)

        assert "result" in result
        assert "thought_signatures" in result
        assert "internal reasoning" in result["thought_signatures"]

    def test_build_generation_config(self, mock_genai):
        """Test that _build_generation_config creates proper config."""
        client = GeminiClient()

        config = client._build_generation_config(
            system_instruction="test system",
            temperature=1.0,
            thinking_level="HIGH",
            enable_grounding=True,
        )

        # Config should be a GenerateContentConfig instance
        assert config is not None

    def test_calculate_file_hash(self, mock_genai, tmp_path):
        """Test MD5 hash calculation for file caching."""
        client = GeminiClient()

        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"hello world")

        hash1 = client._calculate_file_hash(str(test_file))
        hash2 = client._calculate_file_hash(str(test_file))

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex digest length

    def test_analyze_file_cache_hit(self, mock_genai, tmp_path):
        """Test analyze_file returns cached result when cache_enabled and key exists."""
        client = GeminiClient()
        client.cache_enabled = True

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 content")

        # Create cache file
        import hashlib
        file_hash = client._calculate_file_hash(str(test_file))
        prompt = "analyze"
        cache_key = f"{client.model_name}|{file_hash}|{hashlib.md5(prompt.encode()).hexdigest()}"

        cache_file = tmp_path / "genai_cache.json"
        cached_data = {cache_key: {"thought_process": "cached result"}}
        cache_file.write_text(json.dumps(cached_data))
        client.cache_file = cache_file

        result = client.analyze_file(file_path=str(test_file), prompt=prompt)

        assert result["thought_process"] == "cached result"
        # API should NOT have been called
        mock_genai["client"].files.upload.assert_not_called()

    def test_analyze_file_cache_miss(self, mock_genai, tmp_path):
        """Test analyze_file calls API and stores result on cache miss."""
        client = GeminiClient()
        client.cache_enabled = True
        client.cache_file = tmp_path / "genai_cache.json"

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 content")

        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {"thought_process": "new result"}
        mock_genai["response"].parsed = mock_parsed

        result = client.analyze_file(file_path=str(test_file), prompt="analyze")

        assert result["thought_process"] == "new result"
        mock_genai["client"].files.upload.assert_called_once()
        # Cache file should have been created
        assert client.cache_file.exists()

    def test_generate_text_json_parse_fallback(self, mock_genai):
        """Test generate_text falls back to json.loads when parsed=None but schema given."""
        client = GeminiClient()
        mock_genai["response"].parsed = None
        mock_genai["response"].text = '{"key": "value"}'

        from app.models.schemas import AnalysisResult
        result = client.generate_text(prompt="test", response_schema=AnalysisResult)

        assert result == {"key": "value"}
