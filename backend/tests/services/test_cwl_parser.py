import pytest
from app.services.cwl_parser import CWLParser
from app.models.cwl import CWLCommandLineTool, CWLInput, CWLOutput, DockerRequirement


class TestCWLParser:

    @pytest.fixture
    def parser(self):
        return CWLParser()

    # --- parse_yaml ---

    def test_parse_yaml_valid(self, parser):
        """Test parsing valid YAML."""
        result = parser.parse_yaml("key: value\nlist:\n  - a\n  - b")
        assert result == {"key": "value", "list": ["a", "b"]}

    def test_parse_yaml_invalid(self, parser):
        """Test parsing invalid YAML raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YAML"):
            parser.parse_yaml("{{invalid yaml::")

    # --- parse_workflow ---

    def test_parse_workflow_success(self, parser, sample_cwl_workflow):
        """Test parsing a valid CWL workflow."""
        result = parser.parse_workflow(sample_cwl_workflow)

        assert result.success is True
        assert result.workflow is not None
        assert result.workflow.workflow.id == "test-workflow"
        assert len(result.workflow.workflow.steps) == 2
        assert "step1" in result.workflow.workflow.steps
        assert "step2" in result.workflow.workflow.steps

    def test_parse_workflow_unsupported_version(self, parser):
        """Test failure on unsupported CWL version."""
        cwl = "cwlVersion: v0.1\nclass: Workflow\ninputs: {}\noutputs: {}\nsteps: {}"
        result = parser.parse_workflow(cwl)

        assert result.success is False
        assert "Unsupported CWL version" in result.error

    def test_parse_workflow_wrong_class(self, parser):
        """Test failure when class is not Workflow."""
        cwl = "cwlVersion: v1.3\nclass: CommandLineTool\ninputs: {}\noutputs: {}"
        result = parser.parse_workflow(cwl)

        assert result.success is False
        assert "Expected Workflow class" in result.error

    # --- _parse_inputs ---

    def test_parse_inputs_dict_format(self, parser):
        """Test parsing inputs in dict format."""
        inputs = {"input1": {"type": "File"}, "input2": "string"}
        result = parser._parse_inputs(inputs)

        assert len(result) == 2
        assert result["input1"].type == "File"
        assert result["input2"].type == "string"

    def test_parse_inputs_list_format(self, parser):
        """Test parsing inputs in list format."""
        inputs = [
            {"id": "input1", "type": "File"},
            {"id": "input2", "type": "string"},
        ]
        result = parser._parse_inputs(inputs)

        assert len(result) == 2
        assert "input1" in result
        assert "input2" in result

    # --- _parse_outputs ---

    def test_parse_outputs_dict_format(self, parser):
        """Test parsing outputs in dict format."""
        outputs = {
            "output1": {"type": "File", "outputSource": "step1/out"},
            "output2": "Directory",
        }
        result = parser._parse_outputs(outputs)

        assert len(result) == 2
        assert result["output1"].type == "File"
        assert result["output2"].type == "Directory"

    def test_parse_outputs_list_format(self, parser):
        """Test parsing outputs in list format."""
        outputs = [{"id": "output1", "type": "File"}]
        result = parser._parse_outputs(outputs)

        assert len(result) == 1
        assert "output1" in result

    # --- _parse_steps ---

    def test_parse_steps_dict_format(self, parser):
        """Test parsing steps in dict format."""
        steps = {
            "step1": {
                "run": "tools/step1.cwl",
                "in": {"input_file": "input_data"},
                "out": ["output_file"],
            }
        }
        result = parser._parse_steps(steps)

        assert len(result) == 1
        assert "step1" in result
        assert result["step1"].run == "tools/step1.cwl"

    def test_parse_steps_list_format(self, parser):
        """Test parsing steps in list format."""
        steps = [
            {
                "id": "step1",
                "run": "tools/step1.cwl",
                "in": {"input_file": "input_data"},
                "out": ["output_file"],
            }
        ]
        result = parser._parse_steps(steps)

        assert len(result) == 1
        assert "step1" in result

    # --- parse_tool ---

    def test_parse_tool_success(self, parser, sample_cwl_tool):
        """Test parsing a valid CWL CommandLineTool."""
        result = parser.parse_tool(sample_cwl_tool)

        assert result is not None
        assert result.class_ == "CommandLineTool"
        assert result.id == "test-tool"
        assert result.base_command == ["python", "-c"]

    def test_parse_tool_wrong_class(self, parser):
        """Test parse_tool returns None for non-CommandLineTool."""
        cwl = "cwlVersion: v1.3\nclass: Workflow\ninputs: {}\noutputs: {}\nsteps: {}"
        result = parser.parse_tool(cwl)

        assert result is None

    # --- _resolve_dependencies ---

    def test_resolve_dependencies_chain(self, parser, sample_cwl_workflow):
        """Test resolving step dependencies in a linear chain."""
        result = parser.parse_workflow(sample_cwl_workflow)

        assert result.success is True
        deps = result.workflow.step_dependencies
        # step2 depends on step1
        assert "step2" in deps
        assert "step1" in deps["step2"]

    def test_resolve_dependencies_no_deps(self, parser):
        """Test that steps without step sources have no dependencies."""
        cwl = """
cwlVersion: v1.3
class: Workflow
inputs:
  data: File
outputs:
  out:
    type: File
    outputSource: step1/output_file
steps:
  step1:
    run: tools/step1.cwl
    in:
      input_file: data
    out: [output_file]
"""
        result = parser.parse_workflow(cwl)

        assert result.success is True
        deps = result.workflow.step_dependencies
        # step1 only references workflow inputs, not other steps
        assert "step1" not in deps or len(deps.get("step1", [])) == 0

    # --- _topological_sort ---

    def test_topological_sort_linear(self, parser):
        """Test topological sort of a linear dependency chain."""
        deps = {"step2": ["step1"], "step3": ["step2"]}
        order = parser._topological_sort(deps)

        assert order.index("step1") < order.index("step2")
        assert order.index("step2") < order.index("step3")

    def test_topological_sort_diamond(self, parser):
        """Test topological sort of a diamond dependency graph."""
        deps = {"step2": ["step1"], "step3": ["step1"], "step4": ["step2", "step3"]}
        order = parser._topological_sort(deps)

        assert order.index("step1") < order.index("step2")
        assert order.index("step1") < order.index("step3")
        assert order.index("step2") < order.index("step4")
        assert order.index("step3") < order.index("step4")

    # --- _validate_workflow ---

    def test_validate_workflow_undefined_step_ref(self, parser):
        """Test validation catches references to undefined steps."""
        cwl = """
cwlVersion: v1.3
class: Workflow
inputs:
  data: File
outputs:
  out:
    type: File
    outputSource: nonexistent_step/output_file
steps:
  step1:
    run: tools/step1.cwl
    in:
      input_file: nonexistent_step/output_file
    out: [output_file]
"""
        result = parser.parse_workflow(cwl)

        assert result.success is True
        assert result.validation is not None
        assert result.validation.valid is False
        assert any("undefined step" in e for e in result.validation.errors)

    # --- get_docker_requirement ---

    def test_get_docker_requirement_found(self, parser):
        """Test extracting DockerRequirement when present."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3",
            **{"class": "CommandLineTool"},
            requirements=[{"class": "DockerRequirement", "dockerPull": "python:3.11-slim"}],
            inputs={},
            outputs={},
        )
        result = parser.get_docker_requirement(tool)

        assert result is not None
        assert result.docker_pull == "python:3.11-slim"

    def test_get_docker_requirement_not_found(self, parser):
        """Test returns None when no DockerRequirement."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3",
            **{"class": "CommandLineTool"},
            inputs={},
            outputs={},
        )
        result = parser.get_docker_requirement(tool)

        assert result is None
