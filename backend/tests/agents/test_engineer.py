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

    def test_build_workflow_prompt_with_prompt_manager(self, engineer_agent, mock_genai):
        """Test _build_workflow_prompt uses prompt_manager when available."""
        with patch("app.agents.engineer.prompt_manager") as mock_pm:
            mock_pm.get_prompt.return_value = "Template: {assay_info} {identified_tools} {identified_models} {identified_measurements}"

            result = engineer_agent._build_workflow_prompt(
                assay_id="a1",
                isa_json={},
                identified_tools=[],
                identified_models=[],
                identified_measurements=[],
            )

            assert "Template:" in result
            mock_pm.get_prompt.assert_called_once()

    def test_build_workflow_prompt_fallback(self, engineer_agent, mock_genai):
        """Test _build_workflow_prompt uses inline prompt on ValueError."""
        with patch("app.agents.engineer.prompt_manager") as mock_pm:
            mock_pm.get_prompt.side_effect = ValueError("Prompt not found")

            result = engineer_agent._build_workflow_prompt(
                assay_id="a1",
                isa_json={},
                identified_tools=[],
                identified_models=[],
                identified_measurements=[],
            )

            assert "Generate a CWL v1.3 workflow" in result

    def test_parse_response_nodes_edges(self, engineer_agent, mock_genai):
        """Test _parse_response converts flat positions to nested structure."""
        response = {
            "workflow_cwl": "cwl content",
            "tool_cwls": {},
            "dockerfiles": {},
            "adapters": [],
            "nodes": [
                {
                    "id": "tool-1",
                    "type": "tool",
                    "position_x": 100,
                    "position_y": 200,
                    "label": "My Tool",
                    "inputs": [{"id": "in-1", "label": "Input"}],
                    "outputs": [{"id": "out-1", "label": "Output"}],
                }
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "tool-1", "source_handle": "out-1", "target_handle": "in-1"},
            ],
        }

        result = engineer_agent._parse_response(response, "assay_1")

        node = result["graph"]["nodes"][0]
        assert node["position"] == {"x": 100, "y": 200}
        assert node["data"]["label"] == "My Tool"

        edge = result["graph"]["edges"][0]
        assert edge["sourceHandle"] == "out-1"
        assert edge["targetHandle"] == "in-1"

    def test_generate_fallback_workflow_structure(self, engineer_agent, mock_genai):
        """Test _generate_fallback_workflow returns valid structure."""
        result = engineer_agent._generate_fallback_workflow(
            assay_id="a1",
            identified_tools=[{"name": "dcm2niix"}],
            identified_measurements=[{"name": "MRI", "format": "application/dicom"}],
            error="Test error",
        )

        assert result["error"] == "Test error"
        assert result["metadata"]["fallback"] is True
        assert "graph" in result
        assert len(result["graph"]["nodes"]) >= 1

    def test_generate_basic_cwl(self, engineer_agent, mock_genai):
        """Test _generate_basic_cwl returns valid CWL template."""
        cwl = engineer_agent._generate_basic_cwl("assay_1")

        assert "cwlVersion: v1.3" in cwl
        assert "class: Workflow" in cwl
        assert "assay_1" in cwl
        assert "inputs:" in cwl
        assert "outputs:" in cwl

    def test_quick_validate_cwl_valid(self, engineer_agent, mock_genai):
        """Test _quick_validate_cwl returns no errors for valid CWL."""
        cwl = "cwlVersion: v1.3\nclass: Workflow\ninputs:\n  x: File\noutputs:\n  y: File"
        errors = engineer_agent._quick_validate_cwl(cwl)
        assert len(errors) == 0

    def test_quick_validate_cwl_missing_sections(self, engineer_agent, mock_genai):
        """Test _quick_validate_cwl catches missing sections."""
        errors = engineer_agent._quick_validate_cwl("just some text")
        assert any("cwlVersion" in e for e in errors)
        assert any("class" in e for e in errors)
