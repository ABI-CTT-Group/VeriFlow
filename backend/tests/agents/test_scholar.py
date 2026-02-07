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
