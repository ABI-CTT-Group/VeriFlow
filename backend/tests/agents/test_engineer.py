import pytest
from unittest.mock import MagicMock, patch


class TestEngineerAgent:

    @pytest.fixture
    def engineer_agent(self, mock_genai):
        """Create an EngineerAgent instance with mocked Gemini client."""
        from app.agents.engineer import EngineerAgent
        return EngineerAgent()

    @pytest.mark.asyncio
    async def test_generate_workflow_success(self, engineer_agent, mock_genai):
        """Test successful workflow generation with Gemini 3 structured output."""
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Generated CWL workflow",
            "workflow_cwl": "cwlVersion: v1.3\nclass: Workflow",
            "tool_cwls": {"tool_1": "cwlVersion: v1.3\nclass: CommandLineTool"},
            "dockerfiles": {"tool_1": "FROM python:3.10-slim"},
            "adapters": [],
            "nodes": [
                {
                    "id": "input-1",
                    "type": "measurement",
                    "position_x": 50,
                    "position_y": 100,
                    "label": "MRI Data",
                    "inputs": [],
                    "outputs": [{"id": "out-1", "label": "Output", "type": "application/dicom"}],
                }
            ],
            "edges": [],
        }
        mock_genai["response"].parsed = mock_parsed

        result = await engineer_agent.generate_workflow(
            assay_id="assay_1",
            isa_json={},
            identified_tools=[],
            identified_models=[],
            identified_measurements=[],
        )

        assert result["workflow_cwl"] == "cwlVersion: v1.3\nclass: Workflow"
        assert result["metadata"]["agent"] == "engineer"
        assert result["metadata"]["assay_id"] == "assay_1"
        assert result["metadata"]["thinking_level"] == "HIGH"
        assert len(result["graph"]["nodes"]) == 1
        assert result["graph"]["nodes"][0]["data"]["label"] == "MRI Data"

    @pytest.mark.asyncio
    async def test_generate_workflow_fallback(self, engineer_agent, mock_genai):
        """Test fallback workflow generation on error."""
        mock_genai["client"].models.generate_content.side_effect = Exception("Generation Failed")

        result = await engineer_agent.generate_workflow(
            assay_id="assay_1",
            isa_json={},
            identified_tools=[{"name": "dcm2niix"}],
            identified_models=[],
            identified_measurements=[{"name": "MRI", "format": "application/dicom"}],
        )

        assert "fallback" in result["metadata"]
        assert result["metadata"]["fallback"] is True
        assert "error" in result
        assert "Generation Failed" in result["error"]
        assert "workflow_cwl" in result

    def test_find_assay(self, engineer_agent):
        """Test logic for finding assay in ISA hierarchy."""
        isa_json = {
            "studies": [
                {
                    "assays": [
                        {"id": "a1", "name": "Assay 1"},
                        {"id": "a2", "name": "Assay 2"},
                    ]
                }
            ]
        }

        assay = engineer_agent._find_assay(isa_json, "a2")
        assert assay["name"] == "Assay 2"

        assay = engineer_agent._find_assay(isa_json, "non-existent")
        assert assay["name"] == "Assay 1"

        assay = engineer_agent._find_assay({}, "any")
        assert assay["name"] == "Unknown Assay"
