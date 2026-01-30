import pytest
from unittest.mock import MagicMock, patch
from app.agents.engineer import EngineerAgent

class TestEngineerAgent:
    
    @pytest.fixture
    def engineer_agent(self, mock_gemini_client):
        """Create an EngineerAgent instance with mocked Gemini client."""
        with patch("app.agents.engineer.get_gemini_client", return_value=mock_gemini_client):
            return EngineerAgent()

    @pytest.mark.asyncio
    async def test_generate_workflow_success(self, engineer_agent, mock_gemini_client):
        """Test successful workflow generation."""
        # Setup mock response
        mock_response = {
            "workflow_cwl": "cwlVersion: v1.3\nclass: Workflow",
            "tool_cwls": {},
            "dockerfiles": {},
            "adapters": [],
            "graph": {"nodes": [], "edges": []}
        }
        mock_gemini_client.generate_json.return_value = mock_response

        # Call the method
        result = await engineer_agent.generate_workflow(
            assay_id="assay_1",
            isa_json={},
            identified_tools=[],
            identified_models=[],
            identified_measurements=[]
        )
        
        # Verify result
        assert result["workflow_cwl"] == "cwlVersion: v1.3\nclass: Workflow"
        assert result["metadata"]["agent"] == "engineer"
        assert result["metadata"]["assay_id"] == "assay_1"

    @pytest.mark.asyncio
    async def test_generate_workflow_fallback(self, engineer_agent, mock_gemini_client):
        """Test fallback workflow generation on error."""
        # Setup mock to raise exception
        mock_gemini_client.generate_json.side_effect = Exception("Generation Failed")

        # Call the method
        result = await engineer_agent.generate_workflow(
            assay_id="assay_1",
            isa_json={},
            identified_tools=[],
            identified_models=[],
            identified_measurements=[]
        )
        
        # Verify fallback result
        assert "fallback" in result["metadata"]
        assert result["metadata"]["fallback"] is True
        assert "error" in result
        assert result["error"] == "Generation Failed"
        assert "workflow_cwl" in result  # Should have basic template

    def test_find_assay(self, engineer_agent):
        """Test logic for finding assay in ISA hierarchy."""
        isa_json = {
            "studies": [
                {
                    "assays": [
                        {"id": "a1", "name": "Assay 1"},
                        {"id": "a2", "name": "Assay 2"}
                    ]
                }
            ]
        }
        
        # Test finding existing assay
        assay = engineer_agent._find_assay(isa_json, "a2")
        assert assay["name"] == "Assay 2"
        
        # Test finding non-existent - defaults to first
        assay = engineer_agent._find_assay(isa_json, "non-existent")
        assert assay["name"] == "Assay 1"
        
        # Test empty isa
        assay = engineer_agent._find_assay({}, "any")
        assert assay["name"] == "Unknown Assay"
