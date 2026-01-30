import pytest
from unittest.mock import MagicMock, patch
from app.agents.reviewer import ReviewerAgent

class TestReviewerAgent:
    
    @pytest.fixture
    def reviewer_agent(self, mock_gemini_client):
        """Create a ReviewerAgent instance with mocked Gemini client."""
        with patch("app.agents.reviewer.get_gemini_client", return_value=mock_gemini_client):
            return ReviewerAgent()

    @pytest.mark.asyncio
    async def test_validate_workflow_success(self, reviewer_agent, mock_subprocess):
        """Test successful workflow validation."""
        # Mock subprocess for cwltool success
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = ""

        graph = {"nodes": [], "edges": []}
        
        result = await reviewer_agent.validate_workflow(
            workflow_cwl="cwl...",
            tool_cwls={},
            graph=graph
        )
        
        # Verify passed
        assert result["passed"] is True
        assert len(result["user_action_required"]) == 0

    @pytest.mark.asyncio
    async def test_validate_workflow_cwl_fail(self, reviewer_agent, mock_subprocess):
        """Test validation failure due to bad CWL."""
        # Mock subprocess for cwltool failure
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Syntax Error on line 5"

        result = await reviewer_agent.validate_workflow(
            workflow_cwl="bad cwl",
            tool_cwls={},
            graph={"nodes": [], "edges": []}
        )
        
        assert result["passed"] is False
        assert "Syntax Error on line 5" in result["checks"]["cwl_syntax"]["errors"]

    def test_check_type_compatibility(self, reviewer_agent):
        """Test type compatibility checking."""
        graph = {
            "nodes": [
                {
                    "id": "n1", 
                    "data": {"outputs": [{"id": "o1", "type": "application/dicom"}]}
                },
                {
                    "id": "n2", 
                    "data": {"inputs": [{"id": "i1", "type": "application/x-nifti"}]}
                }
            ],
            "edges": [
                {
                    "source": "n1", "target": "n2", 
                    "sourceHandle": "o1", "targetHandle": "i1"
                }
            ]
        }
        
        # Should detect mismatch (DICOM != NIfTI directly, though compatible via adapter)
        result = reviewer_agent._check_type_compatibility(graph)
        
        assert result["passed"] is False
        assert len(result["mismatches"]) == 1
        assert result["mismatches"][0]["suggested_adapter"] == "dcm2niix"

    @pytest.mark.asyncio
    async def test_translate_errors(self, reviewer_agent, mock_gemini_client):
        """Test error translation via Gemini."""
        mock_gemini_client.generate_json.return_value = [
            {"original": "err", "translated": "Friendly Error"}
        ]
        
        translated = await reviewer_agent._translate_errors(["err"])
        
        assert len(translated) == 1
        assert translated[0]["translated"] == "Friendly Error"
