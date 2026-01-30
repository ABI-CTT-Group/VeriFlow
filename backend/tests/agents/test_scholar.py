import pytest
from unittest.mock import MagicMock, patch
from app.agents.scholar import ScholarAgent

class TestScholarAgent:
    
    @pytest.fixture
    def scholar_agent(self, mock_gemini_client):
        """Create a ScholarAgent instance with mocked Gemini client."""
        with patch("app.agents.scholar.get_gemini_client", return_value=mock_gemini_client):
            return ScholarAgent()

    def test_extract_text_from_pdf(self, scholar_agent, mock_pymupdf):
        """Test PDF text extraction."""
        pdf_bytes = b"fake pdf content"
        text = scholar_agent.extract_text_from_pdf(pdf_bytes)
        
        # Verify PyMuPDF was called
        mock_pymupdf.assert_called_once()
        # Verify text was extracted (logic from conftest mock)
        assert "[Page 1]" in text
        assert "Mock PDF Text Content" in text

    @pytest.mark.asyncio
    async def test_analyze_publication_success(self, scholar_agent, mock_gemini_client):
        """Test successful publication analysis."""
        # Setup mock response
        mock_response = {
            "investigation": {
                "id": "inv_1",
                "title": "Test Investigation",
                "studies": []
            },
            "confidence_scores": {},
            "identified_tools": [],
            "identified_models": [],
            "identified_measurements": []
        }
        mock_gemini_client.generate_json.return_value = mock_response

        # Call the method
        result = await scholar_agent.analyze_publication("Sample Text", upload_id="test-123")
        
        # Verify Gemini was called correctly
        mock_gemini_client.generate_json.assert_called_once()
        
        # Verify result structure
        assert result["isa_json"]["title"] == "Test Investigation"
        assert result["metadata"]["upload_id"] == "test-123"
        assert result["metadata"]["agent"] == "scholar"

    @pytest.mark.asyncio
    async def test_analyze_publication_error(self, scholar_agent, mock_gemini_client):
        """Test error handling during analysis."""
        # Setup mock to raise exception
        mock_gemini_client.generate_json.side_effect = Exception("Gemini Error")

        # Call the method
        result = await scholar_agent.analyze_publication("Sample Text")
        
        # Verify error handling
        assert "error" in result
        assert result["error"] == "Gemini Error"
        assert result["isa_json"] is None

    def test_build_hierarchy_response(self, scholar_agent):
        """Test building the frontend-compatible hierarchy response."""
        scholar_output = {
            "isa_json": {
                "id": "inv_1",
                "title": "Test Inv",
                "studies": []
            },
            "confidence_scores": {"prop_1": 90},
            "identified_tools": [{"name": "Tool A"}],
            "identified_models": [],
            "identified_measurements": []
        }
        
        response = scholar_agent.build_hierarchy_response(scholar_output, "upload-xyz")
        
        # Verify structure
        assert "hierarchy" in response
        assert response["hierarchy"]["investigation"]["title"] == "Test Inv"
        assert response["confidence_scores"]["upload_id"] == "upload-xyz"
        assert len(response["identified_tools"]) == 1
        assert response["identified_tools"][0]["name"] == "Tool A"
