"""
VeriFlow - Engineer Agent
Per SPEC.md Section 4.4 - CWL generation, Dockerfile creation, adapter logic

The Engineer Agent is responsible for:
1. Generating CWL v1.3 workflow definitions from extracted methodology
2. Creating Dockerfiles for each tool
3. Inferring dependencies from requirements.txt, import statements, code timestamps
4. Generating adapters for type mismatches (e.g., DICOM → NIfTI)
5. Mapping SDS inputs/outputs to CWL ports
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.gemini_client import get_gemini_client


# System prompt per SPEC.md Section 4.4
ENGINEER_SYSTEM_PROMPT = """You are the Engineer Agent for VeriFlow, a Research Reliability Engineer system.

Your role is to:

1. Generate CWL v1.3 workflow definitions from extracted methodology
2. Create Dockerfiles for each tool
3. Infer dependencies from:
   - requirements.txt (if available)
   - import statements in code
   - Code timestamps for version inference
4. Generate adapters for type mismatches:
   - Check additional_type (MIME type) compatibility
   - Insert conversion tools (e.g., DICOM → NIfTI)
5. Map SDS inputs/outputs to CWL ports

Use CommandLineTool for executable tools, Workflow for orchestration.

CWL Best Practices:
- Use cwlVersion: v1.3
- Define clear input/output types with format specifications
- Use DockerRequirement for containerized execution
- Include meaningful labels and documentation
- Handle scatter operations for batch processing

IMPORTANT: Your response must be valid JSON following the exact schema provided in the prompt."""


class EngineerAgent:
    """
    Engineer Agent for CWL workflow generation.
    
    Generates executable CWL workflows, Dockerfiles, and adapters
    from ISA hierarchy and identified tools/models.
    """
    
    def __init__(self):
        """Initialize Engineer Agent with Gemini client."""
        self.gemini = get_gemini_client()
    
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
        
        Args:
            assay_id: The selected assay ID
            isa_json: ISA hierarchy from Scholar Agent
            identified_tools: List of identified processing tools
            identified_models: List of identified ML models
            identified_measurements: List of identified data types
            
        Returns:
            Dictionary with:
            - workflow_cwl: Main workflow CWL YAML
            - tool_cwls: CWL for each tool
            - dockerfiles: Dockerfile for each tool
            - adapters: Type mismatch adapters
            - graph: Vue Flow graph representation
        """
        # Build the prompt
        prompt = self._build_workflow_prompt(
            assay_id, isa_json, identified_tools, identified_models, identified_measurements
        )
        
        try:
            response = self.gemini.generate_json(
                prompt=prompt,
                system_instruction=ENGINEER_SYSTEM_PROMPT,
                temperature=0.3,
            )
            
            # Parse and enhance the response
            result = self._parse_response(response, assay_id)
            return result
            
        except Exception as e:
            # Return error structure with mock workflow
            return self._generate_fallback_workflow(assay_id, identified_tools, identified_measurements, str(e))
    
    def _build_workflow_prompt(
        self,
        assay_id: str,
        isa_json: Dict[str, Any],
        identified_tools: List[Dict[str, Any]],
        identified_models: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
    ) -> str:
        """Build the workflow generation prompt for Gemini."""
        
        # Find the target assay
        assay_info = self._find_assay(isa_json, assay_id)
        
        prompt = f"""Generate a CWL v1.3 workflow for the following assay and components.

ASSAY INFORMATION:
{json.dumps(assay_info, indent=2)}

IDENTIFIED TOOLS:
{json.dumps(identified_tools, indent=2)}

IDENTIFIED MODELS:
{json.dumps(identified_models, indent=2)}

IDENTIFIED MEASUREMENTS (INPUT DATA TYPES):
{json.dumps(identified_measurements, indent=2)}

Generate a complete workflow with the following structure:

{{
  "workflow_cwl": "string - Complete CWL v1.3 workflow YAML",
  "tool_cwls": {{
    "tool_id": "string - CWL CommandLineTool YAML for each tool"
  }},
  "dockerfiles": {{
    "tool_id": "string - Dockerfile content for each tool"
  }},
  "adapters": [
    {{
      "id": "adapter_1",
      "name": "string",
      "source_type": "string - MIME type like application/dicom",
      "target_type": "string - MIME type like application/x-nifti",
      "cwl": "string - Adapter CWL",
      "dockerfile": "string - Adapter Dockerfile"
    }}
  ],
  "graph": {{
    "nodes": [
      {{
        "id": "string - unique node id",
        "type": "measurement" | "tool" | "model",
        "position": {{"x": number, "y": number}},
        "data": {{
          "label": "string - display name",
          "inputs": [{{"id": "string", "label": "string", "type": "string - MIME type"}}],
          "outputs": [{{"id": "string", "label": "string", "type": "string - MIME type"}}]
        }}
      }}
    ],
    "edges": [
      {{
        "id": "string",
        "source": "string - source node id",
        "target": "string - target node id",
        "sourceHandle": "string - output port id",
        "targetHandle": "string - input port id"
      }}
    ]
  }}
}}

REQUIREMENTS:
1. Create a logical workflow connecting inputs → processing → outputs
2. Include adapters for any type mismatches between connected nodes
3. Generate realistic Dockerfiles with proper base images and dependencies
4. Position nodes left-to-right based on processing order (x: 50, 250, 450, etc)
5. Include at least one measurement node (input data), tool nodes (processing), and output
6. Use proper CWL v1.3 syntax with DockerRequirement

For medical imaging workflows:
- Common conversions: DICOM → NIfTI, NIfTI → segmentation mask
- Common tools: dcm2niix, nnU-Net, ITK-SNAP
- Base images: python:3.10-slim, pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime"""
        
        return prompt
    
    def _find_assay(self, isa_json: Dict[str, Any], assay_id: str) -> Dict[str, Any]:
        """Find the assay by ID in the ISA hierarchy."""
        if not isa_json:
            return {"id": assay_id, "name": "Unknown Assay", "steps": []}
        
        # Search through studies
        studies = isa_json.get("studies", [])
        for study in studies:
            assays = study.get("assays", [])
            for assay in assays:
                if assay.get("id") == assay_id:
                    return assay
        
        # Return first assay if not found
        if studies and studies[0].get("assays"):
            return studies[0]["assays"][0]
        
        return {"id": assay_id, "name": "Unknown Assay", "steps": []}
    
    def _parse_response(
        self,
        response: Dict[str, Any],
        assay_id: str,
    ) -> Dict[str, Any]:
        """Parse and validate the Gemini response."""
        
        result = {
            "workflow_cwl": response.get("workflow_cwl", ""),
            "tool_cwls": response.get("tool_cwls", {}),
            "dockerfiles": response.get("dockerfiles", {}),
            "adapters": response.get("adapters", []),
            "graph": response.get("graph", {"nodes": [], "edges": []}),
            "metadata": {
                "assay_id": assay_id,
                "generated_at": datetime.utcnow().isoformat(),
                "agent": "engineer",
                "model": self.gemini.model_name,
            }
        }
        
        return result
    
    def _generate_fallback_workflow(
        self,
        assay_id: str,
        identified_tools: List[Dict[str, Any]],
        identified_measurements: List[Dict[str, Any]],
        error: str,
    ) -> Dict[str, Any]:
        """Generate a fallback workflow when Gemini fails."""
        
        # Create basic workflow structure
        nodes = []
        edges = []
        
        # Add measurement nodes
        for i, measurement in enumerate(identified_measurements[:3]):
            nodes.append({
                "id": f"measurement-{i+1}",
                "type": "measurement",
                "position": {"x": 50, "y": 100 + i * 150},
                "data": {
                    "label": measurement.get("name", f"Input {i+1}"),
                    "inputs": [],
                    "outputs": [{"id": "out-1", "label": "Output", "type": measurement.get("format", "application/octet-stream")}],
                },
            })
        
        # Add tool nodes
        tool_x = 300
        for i, tool in enumerate(identified_tools[:3]):
            node_id = f"tool-{i+1}"
            nodes.append({
                "id": node_id,
                "type": "tool",
                "position": {"x": tool_x, "y": 100 + i * 150},
                "data": {
                    "label": tool.get("name", f"Tool {i+1}"),
                    "inputs": [{"id": "in-1", "label": "Input", "type": "application/octet-stream"}],
                    "outputs": [{"id": "out-1", "label": "Output", "type": "application/octet-stream"}],
                },
            })
            
            # Connect from measurement if available
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
            }
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
    
    def generate_dockerfile(self, tool_name: str, dependencies: List[str]) -> str:
        """
        Generate a Dockerfile for a tool.
        
        Args:
            tool_name: Name of the tool
            dependencies: List of Python packages
            
        Returns:
            Dockerfile content
        """
        deps_str = " ".join(dependencies) if dependencies else "numpy"
        
        return f"""# Dockerfile for {tool_name}
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir {deps_str}

# Copy tool scripts
COPY . /app/

# Set entrypoint
ENTRYPOINT ["python", "-m", "{tool_name.lower().replace(' ', '_')}"]
"""


# Global agent instance
engineer_agent = EngineerAgent()
