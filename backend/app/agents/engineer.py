"""
VeriFlow - Engineer Agent
Per SPEC.md Section 4.4 - CWL generation, Dockerfile creation, adapter logic

Migrated to google-genai SDK with Gemini 3 features:
- Pydantic structured output (WorkflowResult schema)
- Thinking level control for complex CWL generation
- Config-driven model selection
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.config import config
from app.models.schemas import WorkflowResult

logger = logging.getLogger(__name__)


class EngineerAgent:
    """
    Engineer Agent for CWL workflow generation.

    Uses Gemini 3 with structured output (WorkflowResult schema)
    to generate executable CWL workflows, Dockerfiles, and adapters
    from ISA hierarchy and identified tools/models.
    """

    def __init__(self):
        """Initialize Engineer Agent with Gemini client and config."""
        self.client = GeminiClient()

        # Load Agent-Specific Config
        self.agent_config = config.get_agent_config("engineer")
        self.prompt_version = self.agent_config.get("default_prompt_version", "v1_standard")

        # Resolve Model Alias to API Parameters
        model_alias = self.agent_config.get("default_model", "gemini-3-pro")
        self.model_params = config.get_model_params(model_alias)

        # Apply Configuration to Client
        self.client.model_name = self.model_params.get("api_model_name", model_alias)

        # Gemini 3: Thinking level for complex generation
        self.thinking_level = self.agent_config.get("thinking_level", "HIGH")
        self.temperature = self.model_params.get("temperature", 1.0)

    async def generate_workflow(
        self,
        assay_id: str,
        isa_json: Dict[str, Any],
        identified_tools: List[Dict[str, Any]],
        identified_models: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate CWL workflow from ISA hierarchy and identified components.

        Uses Gemini 3 with WorkflowResult structured output schema.
        """
        # Build the prompt
        prompt = self._build_workflow_prompt(
            assay_id, isa_json, identified_tools, identified_models, identified_measurements
        )

        try:
            # Retrieve system instruction from prompt manager
            system_instruction = prompt_manager.get_prompt("engineer_system", self.prompt_version)

            # Generate with Gemini 3 structured output
            response = self.client.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=WorkflowResult,
                thinking_level=self.thinking_level,
            )

            # Parse and enhance the response
            result = self._parse_response(response, assay_id)
            return result

        except Exception as e:
            logger.error(f"Engineer Agent error: {e}")
            return self._generate_fallback_workflow(assay_id, identified_tools, identified_measurements, str(e))

    def _build_workflow_prompt(
        self,
        assay_id: str,
        isa_json: Dict[str, Any],
        identified_tools: List[Dict[str, Any]],
        identified_models: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
    ) -> str:
        """Build the workflow generation prompt."""
        assay_info = self._find_assay(isa_json, assay_id)

        try:
            base_prompt = prompt_manager.get_prompt("engineer_workflow", self.prompt_version)
            return base_prompt.format(
                assay_info=json.dumps(assay_info, indent=2),
                identified_tools=json.dumps(identified_tools, indent=2),
                identified_models=json.dumps(identified_models, indent=2),
                identified_measurements=json.dumps(identified_measurements, indent=2),
            )
        except (ValueError, KeyError):
            # Fallback: build prompt inline
            return f"""Generate a CWL v1.3 workflow for the following assay and components.

ASSAY INFORMATION:
{json.dumps(assay_info, indent=2)}

IDENTIFIED TOOLS:
{json.dumps(identified_tools, indent=2)}

IDENTIFIED MODELS:
{json.dumps(identified_models, indent=2)}

IDENTIFIED MEASUREMENTS (INPUT DATA TYPES):
{json.dumps(identified_measurements, indent=2)}

Generate a complete CWL v1.3 workflow with tool definitions, Dockerfiles, adapters, and a graph layout.
Position nodes left-to-right based on processing order."""

    def _find_assay(self, isa_json: Dict[str, Any], assay_id: str) -> Dict[str, Any]:
        """Find the assay by ID in the ISA hierarchy."""
        if not isa_json:
            return {"id": assay_id, "name": "Unknown Assay", "steps": []}

        studies = isa_json.get("studies", [])
        for study in studies:
            assays = study.get("assays", [])
            for assay in assays:
                if assay.get("id") == assay_id:
                    return assay

        if studies and studies[0].get("assays"):
            return studies[0]["assays"][0]

        return {"id": assay_id, "name": "Unknown Assay", "steps": []}

    def _parse_response(
        self,
        response: Dict[str, Any],
        assay_id: str,
    ) -> Dict[str, Any]:
        """Parse the Gemini structured response into the format expected by the API."""
        # Convert flat nodes/edges to nested graph structure
        nodes = []
        for node in response.get("nodes", []):
            nodes.append({
                "id": node.get("id", ""),
                "type": node.get("type", "tool"),
                "position": {"x": node.get("position_x", 0), "y": node.get("position_y", 0)},
                "data": {
                    "label": node.get("label", ""),
                    "inputs": [p for p in node.get("inputs", [])],
                    "outputs": [p for p in node.get("outputs", [])],
                },
            })

        edges = []
        for edge in response.get("edges", []):
            edges.append({
                "id": edge.get("id", ""),
                "source": edge.get("source", ""),
                "target": edge.get("target", ""),
                "sourceHandle": edge.get("source_handle", "out-1"),
                "targetHandle": edge.get("target_handle", "in-1"),
            })

        return {
            "workflow_cwl": response.get("workflow_cwl", ""),
            "tool_cwls": response.get("tool_cwls", {}),
            "dockerfiles": response.get("dockerfiles", {}),
            "adapters": response.get("adapters", []),
            "graph": {"nodes": nodes, "edges": edges},
            "metadata": {
                "assay_id": assay_id,
                "generated_at": datetime.utcnow().isoformat(),
                "agent": "engineer",
                "model": self.client.model_name,
                "thinking_level": self.thinking_level,
            },
        }

    def _generate_fallback_workflow(
        self,
        assay_id: str,
        identified_tools: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
        error: str,
    ) -> Dict[str, Any]:
        """Generate a fallback workflow when Gemini fails."""
        nodes = []
        edges = []

        for i, measurement in enumerate(identified_measurements[:3]):
            name = measurement.get("name", f"Input {i+1}") if isinstance(measurement, dict) else str(measurement)
            fmt = measurement.get("format", "application/octet-stream") if isinstance(measurement, dict) else "application/octet-stream"
            nodes.append({
                "id": f"measurement-{i+1}",
                "type": "measurement",
                "position": {"x": 50, "y": 100 + i * 150},
                "data": {
                    "label": name,
                    "inputs": [],
                    "outputs": [{"id": "out-1", "label": "Output", "type": fmt}],
                },
            })

        tool_x = 300
        for i, tool in enumerate(identified_tools[:3]):
            name = tool.get("name", f"Tool {i+1}") if isinstance(tool, dict) else str(tool)
            node_id = f"tool-{i+1}"
            nodes.append({
                "id": node_id,
                "type": "tool",
                "position": {"x": tool_x, "y": 100 + i * 150},
                "data": {
                    "label": name,
                    "inputs": [{"id": "in-1", "label": "Input", "type": "application/octet-stream"}],
                    "outputs": [{"id": "out-1", "label": "Output", "type": "application/octet-stream"}],
                },
            })

            if i < len(identified_measurements):
                edges.append({
                    "id": f"e-m{i+1}-t{i+1}",
                    "source": f"measurement-{i+1}",
                    "target": node_id,
                    "sourceHandle": "out-1",
                    "targetHandle": "in-1",
                })
            tool_x += 200

        return {
            "workflow_cwl": self._generate_basic_cwl(assay_id),
            "tool_cwls": {},
            "dockerfiles": {},
            "adapters": [],
            "graph": {"nodes": nodes, "edges": edges},
            "error": error,
            "metadata": {
                "assay_id": assay_id,
                "generated_at": datetime.utcnow().isoformat(),
                "agent": "engineer",
                "fallback": True,
            },
        }

    def _generate_basic_cwl(self, assay_id: str) -> str:
        """Generate a basic CWL workflow template."""
        return f"""cwlVersion: v1.3
class: Workflow

label: VeriFlow Generated Workflow - {assay_id}
doc: Automatically generated workflow from VeriFlow

inputs:
  input_data:
    type: Directory
    label: Input Data Directory
    doc: SDS primary folder containing subject data

outputs:
  output_data:
    type: Directory
    label: Output Data Directory
    outputSource: process/output_dir

steps:
  process:
    run: tools/process.cwl
    in:
      input_dir: input_data
    out: [output_dir]
"""


    async def generate_workflow_agentic(
        self,
        assay_id: str,
        isa_json: Dict[str, Any],
        identified_tools: List[Dict[str, Any]],
        identified_models: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Agentic workflow generation with tool-use loops.

        Uses Gemini 3's function calling to iteratively:
        1. Generate CWL workflow
        2. Call validate_cwl tool to check syntax
        3. Observe errors
        4. Fix and regenerate

        This is the Gemini 3-native agentic pattern using
        think-act-observe loops with thought signature preservation.
        """
        try:
            system_instruction = prompt_manager.get_prompt("engineer_system", self.prompt_version)
        except ValueError:
            system_instruction = "You are the Engineer Agent. Generate CWL workflows."

        # Define tools for function calling
        validate_cwl_tool = {
            "name": "validate_cwl",
            "description": "Validate CWL workflow syntax. Returns errors if any.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cwl_content": {
                        "type": "string",
                        "description": "The CWL YAML content to validate",
                    }
                },
                "required": ["cwl_content"],
            },
        }

        check_docker_image_tool = {
            "name": "check_docker_image",
            "description": "Check if a Docker image exists and is pullable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_name": {
                        "type": "string",
                        "description": "Docker image name with tag",
                    }
                },
                "required": ["image_name"],
            },
        }

        # Build initial prompt
        prompt = self._build_workflow_prompt(
            assay_id, isa_json, identified_tools, identified_models, identified_measurements
        )

        messages = [{"role": "user", "content": prompt}]
        all_results = []

        for iteration in range(max_iterations):
            # Generate with thinking and tool awareness
            response = self.client.generate_with_history(
                messages=messages,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=WorkflowResult,
                thinking_level=self.thinking_level,
            )

            result = response["result"]
            thought_sigs = response["thought_signatures"]
            all_results.append(result)

            # Validate the generated CWL locally
            cwl_content = result.get("workflow_cwl", "")
            validation_errors = self._quick_validate_cwl(cwl_content)

            if not validation_errors:
                # CWL is valid, return the result
                parsed = self._parse_response(result, assay_id)
                parsed["metadata"]["iterations"] = iteration + 1
                parsed["metadata"]["agentic"] = True
                return parsed

            # Feed errors back for next iteration
            messages.append({
                "role": "model",
                "content": json.dumps(result),
                "thought_signatures": thought_sigs,
            })
            messages.append({
                "role": "user",
                "content": f"The CWL validation found these errors: {json.dumps(validation_errors)}. Please fix them and regenerate.",
            })

        # Return the last attempt even if not perfect
        if all_results:
            parsed = self._parse_response(all_results[-1], assay_id)
            parsed["metadata"]["iterations"] = max_iterations
            parsed["metadata"]["agentic"] = True
            parsed["metadata"]["validation_incomplete"] = True
            return parsed

        return self._generate_fallback_workflow(assay_id, identified_tools, identified_measurements, "Agentic generation failed")

    def _quick_validate_cwl(self, cwl_content: str) -> List[str]:
        """Quick local CWL validation without cwltool."""
        errors = []
        if not cwl_content or not cwl_content.strip():
            errors.append("Empty CWL content")
            return errors
        if "cwlVersion" not in cwl_content:
            errors.append("Missing cwlVersion declaration")
        if "class:" not in cwl_content:
            errors.append("Missing class declaration")
        if "inputs:" not in cwl_content:
            errors.append("Missing inputs section")
        if "outputs:" not in cwl_content:
            errors.append("Missing outputs section")
        return errors


# Global agent instance
engineer_agent = EngineerAgent()
