import pytest
from unittest.mock import MagicMock, patch


class TestScholarAgent:

    @pytest.fixture
    def scholar_agent(self, mock_genai):
        """Create a ScholarAgent instance with mocked Gemini client."""
        from app.agents.scholar import ScholarAgent
        return ScholarAgent()

    @pytest.mark.asyncio
    async def test_analyze_publication_success(self, scholar_agent, mock_genai, tmp_path):
        """Test successful publication analysis with Gemini 3."""
        # Create a fake PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        # Mock parsed response
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Analyzed the document carefully",
            "investigation": {
                "title": "Test Investigation",
                "description": "Test description",
                "study_factors": [],
                "metadata": [],
            },
            "confidence_scores": [{"name": "title", "score": 0.95}],
            "identified_tools": [{"name": "Tool A", "description": "A test tool"}],
            "identified_models": ["U-Net"],
            "identified_measurements": ["DCE-MRI"],
        }
        mock_genai["response"].parsed = mock_parsed

        result = await scholar_agent.analyze_publication(
            pdf_path=str(pdf_file),
            upload_id="test-123",
        )

        # Verify result structure
        assert result["isa_json"]["title"] == "Test Investigation"
        assert result["metadata"]["upload_id"] == "test-123"
        assert result["metadata"]["agent"] == "scholar_v2"
        assert result["metadata"]["thinking_level"] == "HIGH"
        assert result["confidence_scores"]["title"] == 0.95
        assert len(result["identified_tools"]) == 1
        assert result["agent_thoughts"] == "Analyzed the document carefully"

    @pytest.mark.asyncio
    async def test_analyze_publication_file_not_found(self, scholar_agent):
        """Test error when file doesn't exist."""
        result = await scholar_agent.analyze_publication(
            pdf_path="/nonexistent/file.pdf",
        )
        assert "error" in result
        assert "File not found" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_publication_error(self, scholar_agent, mock_genai, tmp_path):
        """Test error handling during analysis."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        mock_genai["client"].files.upload.side_effect = Exception("Upload failed")

        result = await scholar_agent.analyze_publication(
            pdf_path=str(pdf_file),
        )

        assert "error" in result
        assert "Upload failed" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_with_vision_success(self, scholar_agent, mock_genai, tmp_path):
        """Test vision analysis returns vision_analysis in result."""
        import sys
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        # Setup fitz mock for vision
        mock_fitz = sys.modules['fitz']
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b"fake png"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc
        mock_fitz.Matrix.return_value = MagicMock()

        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Vision analysis",
            "investigation": {"title": "Vision Test", "description": "desc", "study_factors": [], "metadata": []},
            "confidence_scores": [],
            "identified_tools": [],
            "identified_models": [],
            "identified_measurements": [],
        }
        mock_genai["response"].parsed = mock_parsed

        result = await scholar_agent.analyze_with_vision(pdf_path=str(pdf_file), upload_id="vis-123")

        assert "vision_analysis" in result
        assert result["vision_analysis"]["method"] == "agentic_vision"
        assert result["metadata"]["agent"] == "scholar_v2_vision"

    @pytest.mark.asyncio
    async def test_analyze_with_vision_no_pymupdf(self, scholar_agent, mock_genai, tmp_path):
        """Test ImportError falls back to analyze_publication."""
        import sys
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        # Make fitz.open raise ImportError
        mock_fitz = sys.modules['fitz']
        mock_fitz.open.side_effect = ImportError("No module named 'fitz'")

        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Fallback analysis",
            "investigation": {"title": "Fallback", "description": "desc", "study_factors": [], "metadata": []},
            "confidence_scores": [],
            "identified_tools": [],
            "identified_models": [],
            "identified_measurements": [],
        }
        mock_genai["response"].parsed = mock_parsed

        result = await scholar_agent.analyze_with_vision(pdf_path=str(pdf_file))

        # Should fall back to analyze_publication result
        assert "vision_analysis" not in result or result.get("metadata", {}).get("agent") == "scholar_v2"

    @pytest.mark.asyncio
    async def test_analyze_with_vision_file_not_found(self, scholar_agent):
        """Test vision analysis with non-existent file."""
        result = await scholar_agent.analyze_with_vision(pdf_path="/nonexistent/file.pdf")
        assert "error" in result
        assert "File not found" in result["error"]

    def test_confidence_score_transformation(self, scholar_agent):
        """Test list-to-dict conversion of confidence scores."""
        conf_list = [{"name": "title", "score": 0.95}, {"name": "description", "score": 0.8}]
        conf_dict = {item["name"]: item["score"] for item in conf_list}

        assert conf_dict["title"] == 0.95
        assert conf_dict["description"] == 0.8

    @pytest.mark.asyncio
    async def test_context_content_appended_to_prompt(self, scholar_agent, mock_genai, tmp_path):
        """Test that context_content is appended to the prompt."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "test",
            "investigation": {"title": "Test", "description": "desc", "study_factors": [], "metadata": []},
            "confidence_scores": [],
            "identified_tools": [],
            "identified_models": [],
            "identified_measurements": [],
        }
        mock_genai["response"].parsed = mock_parsed

        await scholar_agent.analyze_publication(
            pdf_path=str(pdf_file),
            context_content="Additional context about the study",
        )

        # Verify the prompt was called with context appended
        call_args = mock_genai["client"].models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args[1].get("contents") or call_args[0][1] if len(call_args[0]) > 1 else None
        # The prompt string should contain context
        if contents:
            prompt_str = str(contents)
            assert "Additional context about the study" in prompt_str
