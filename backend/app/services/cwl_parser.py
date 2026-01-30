"""
VeriFlow - CWL Parser Service
Parses CWL v1.3 workflow YAML files and resolves dependencies.
Per SPEC.md Section 7.2
"""

import yaml
import os
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
from collections import defaultdict

from app.models.cwl import (
    CWLWorkflow,
    CWLCommandLineTool,
    CWLStep,
    CWLInput,
    CWLOutput,
    ParsedWorkflow,
    CWLValidationResult,
    CWLParseResult,
    DockerRequirement,
)


class CWLParser:
    """
    Parser for CWL v1.3 workflow files.
    
    Supports:
    - Workflow documents
    - CommandLineTool documents
    - Dependency resolution between steps
    - Topological sorting of execution order
    """
    
    SUPPORTED_VERSIONS = ["v1.0", "v1.1", "v1.2", "v1.3"]
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize parser with optional base path for resolving relative references.
        
        Args:
            base_path: Base directory for resolving tool references
        """
        self.base_path = base_path or Path(".")
    
    def parse_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Parse YAML string to dictionary."""
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
    
    def parse_workflow(self, yaml_content: str) -> CWLParseResult:
        """
        Parse a CWL workflow from YAML content.
        
        Args:
            yaml_content: CWL YAML string
            
        Returns:
            CWLParseResult with parsed workflow or error
        """
        try:
            data = self.parse_yaml(yaml_content)
            
            # Validate CWL version
            cwl_version = data.get("cwlVersion", "")
            if not any(v in cwl_version for v in self.SUPPORTED_VERSIONS):
                return CWLParseResult(
                    success=False,
                    error=f"Unsupported CWL version: {cwl_version}. Supported: {self.SUPPORTED_VERSIONS}"
                )
            
            # Validate document class
            doc_class = data.get("class", "")
            if doc_class != "Workflow":
                return CWLParseResult(
                    success=False,
                    error=f"Expected Workflow class, got: {doc_class}"
                )
            
            # Parse inputs
            inputs = self._parse_inputs(data.get("inputs", {}))
            
            # Parse outputs
            outputs = self._parse_outputs(data.get("outputs", {}))
            
            # Parse steps
            steps = self._parse_steps(data.get("steps", {}))
            
            # Create workflow object
            workflow = CWLWorkflow(
                cwlVersion=cwl_version,
                **{"class": doc_class},
                id=data.get("id"),
                label=data.get("label"),
                doc=data.get("doc"),
                inputs=inputs,
                outputs=outputs,
                steps=steps,
                requirements=data.get("requirements"),
                hints=data.get("hints"),
            )
            
            # Resolve step dependencies
            step_dependencies = self._resolve_dependencies(workflow)
            
            # Topologically sort steps
            step_order = self._topological_sort(step_dependencies)
            
            # Load tool definitions (if available)
            tools = self._load_tools(workflow)
            
            parsed = ParsedWorkflow(
                workflow=workflow,
                tools=tools,
                step_order=step_order,
                step_dependencies=step_dependencies,
            )
            
            # Validate
            validation = self._validate_workflow(parsed)
            
            return CWLParseResult(
                success=True,
                workflow=parsed,
                validation=validation,
            )
            
        except Exception as e:
            return CWLParseResult(
                success=False,
                error=str(e),
            )
    
    def parse_tool(self, yaml_content: str) -> Optional[CWLCommandLineTool]:
        """
        Parse a CWL CommandLineTool from YAML content.
        
        Args:
            yaml_content: CWL YAML string
            
        Returns:
            Parsed CommandLineTool or None on error
        """
        try:
            data = self.parse_yaml(yaml_content)
            
            if data.get("class") != "CommandLineTool":
                return None
            
            inputs = self._parse_inputs(data.get("inputs", {}))
            outputs = self._parse_outputs(data.get("outputs", {}))
            
            return CWLCommandLineTool(
                cwlVersion=data.get("cwlVersion", "v1.3"),
                **{"class": "CommandLineTool"},
                id=data.get("id"),
                label=data.get("label"),
                doc=data.get("doc"),
                baseCommand=data.get("baseCommand"),
                arguments=data.get("arguments"),
                inputs=inputs,
                outputs=outputs,
                requirements=data.get("requirements"),
                hints=data.get("hints"),
                stdin=data.get("stdin"),
                stdout=data.get("stdout"),
                stderr=data.get("stderr"),
            )
        except Exception:
            return None
    
    def _parse_inputs(self, inputs_data: Union[Dict, List]) -> Dict[str, CWLInput]:
        """Parse inputs from CWL format (dict or list)."""
        result = {}
        
        if isinstance(inputs_data, list):
            # List format: [{"id": "input1", "type": "File"}, ...]
            for item in inputs_data:
                if isinstance(item, dict) and "id" in item:
                    input_id = item["id"].split("#")[-1]  # Handle URIs
                    result[input_id] = CWLInput(**item)
        elif isinstance(inputs_data, dict):
            # Dict format: {"input1": {"type": "File"}, ...} or {"input1": "File"}
            for key, value in inputs_data.items():
                input_id = key.split("#")[-1]
                if isinstance(value, str):
                    result[input_id] = CWLInput(type=value)
                elif isinstance(value, dict):
                    result[input_id] = CWLInput(**value)
        
        return result
    
    def _parse_outputs(self, outputs_data: Union[Dict, List]) -> Dict[str, CWLOutput]:
        """Parse outputs from CWL format (dict or list)."""
        result = {}
        
        if isinstance(outputs_data, list):
            for item in outputs_data:
                if isinstance(item, dict) and "id" in item:
                    output_id = item["id"].split("#")[-1]
                    result[output_id] = CWLOutput(**item)
        elif isinstance(outputs_data, dict):
            for key, value in outputs_data.items():
                output_id = key.split("#")[-1]
                if isinstance(value, str):
                    result[output_id] = CWLOutput(type=value)
                elif isinstance(value, dict):
                    result[output_id] = CWLOutput(**value)
        
        return result
    
    def _parse_steps(self, steps_data: Union[Dict, List]) -> Dict[str, CWLStep]:
        """Parse workflow steps."""
        result = {}
        
        if isinstance(steps_data, list):
            for item in steps_data:
                if isinstance(item, dict) and "id" in item:
                    step_id = item["id"].split("#")[-1]
                    result[step_id] = self._parse_step(step_id, item)
        elif isinstance(steps_data, dict):
            for key, value in steps_data.items():
                step_id = key.split("#")[-1]
                result[step_id] = self._parse_step(step_id, value)
        
        return result
    
    def _parse_step(self, step_id: str, step_data: Dict) -> CWLStep:
        """Parse a single workflow step."""
        # Parse 'in' - can be dict or list
        in_data = step_data.get("in", {})
        parsed_in = {}
        
        if isinstance(in_data, list):
            for item in in_data:
                if isinstance(item, dict) and "id" in item:
                    parsed_in[item["id"]] = item.get("source", item.get("default"))
                elif isinstance(item, str):
                    parsed_in[item] = item
        elif isinstance(in_data, dict):
            for key, value in in_data.items():
                if isinstance(value, dict):
                    parsed_in[key] = value.get("source", value.get("default", ""))
                else:
                    parsed_in[key] = value
        
        # Parse 'out' - list of strings or dicts
        out_data = step_data.get("out", [])
        parsed_out = []
        
        for item in out_data:
            if isinstance(item, str):
                parsed_out.append(item)
            elif isinstance(item, dict) and "id" in item:
                parsed_out.append(item["id"])
        
        return CWLStep(
            id=step_id,
            run=step_data.get("run", ""),
            **{"in": parsed_in},
            out=parsed_out,
            scatter=step_data.get("scatter"),
            scatterMethod=step_data.get("scatterMethod"),
            when=step_data.get("when"),
        )
    
    def _resolve_dependencies(self, workflow: CWLWorkflow) -> Dict[str, List[str]]:
        """
        Resolve step dependencies based on input sources.
        
        Returns:
            Dict mapping step_id to list of step_ids it depends on
        """
        dependencies: Dict[str, List[str]] = defaultdict(list)
        
        for step_id, step in workflow.steps.items():
            for input_name, source in step.in_.items():
                if isinstance(source, str) and "/" in source:
                    # Format: "step_id/output_name"
                    source_step = source.split("/")[0]
                    if source_step in workflow.steps:
                        if source_step not in dependencies[step_id]:
                            dependencies[step_id].append(source_step)
        
        return dict(dependencies)
    
    def _topological_sort(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """
        Topologically sort steps based on dependencies.
        
        Returns:
            List of step_ids in execution order
        """
        # Get all step IDs
        all_steps = set(dependencies.keys())
        for deps in dependencies.values():
            all_steps.update(deps)
        
        # Kahn's algorithm
        in_degree = {step: 0 for step in all_steps}
        for deps in dependencies.values():
            for dep in deps:
                pass  # Dependencies don't increase in_degree
        
        # Calculate in-degrees
        for step, deps in dependencies.items():
            in_degree[step] = len(deps)
        
        # Start with steps that have no dependencies
        queue = [step for step, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            step = queue.pop(0)
            result.append(step)
            
            # For each step that depends on this one
            for dependent, deps in dependencies.items():
                if step in deps:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0 and dependent not in result and dependent not in queue:
                        queue.append(dependent)
        
        # Add any remaining steps (handles cycles or disconnected steps)
        for step in all_steps:
            if step not in result:
                result.append(step)
        
        return result
    
    def _load_tools(self, workflow: CWLWorkflow) -> Dict[str, CWLCommandLineTool]:
        """
        Load tool definitions referenced by workflow steps.
        
        For MVP, returns empty dict - tools would be loaded from MinIO.
        """
        tools = {}
        
        for step_id, step in workflow.steps.items():
            if step.run and not step.run.startswith("#"):
                # External tool reference - would load from MinIO
                # For MVP, create placeholder tool
                tools[step_id] = CWLCommandLineTool(
                    cwlVersion=workflow.cwl_version,
                    **{"class": "CommandLineTool"},
                    id=step_id,
                    label=step_id.replace("-", " ").title(),
                    baseCommand=["python", "-c", f"print('Running {step_id}')"],
                    inputs={
                        name: CWLInput(type="File")
                        for name in step.in_.keys()
                    },
                    outputs={
                        name: CWLOutput(type="File")
                        for name in step.out
                    },
                )
        
        return tools
    
    def _validate_workflow(self, parsed: ParsedWorkflow) -> CWLValidationResult:
        """Validate the parsed workflow structure."""
        errors = []
        warnings = []
        
        workflow = parsed.workflow
        
        # Check for empty workflow
        if not workflow.steps:
            warnings.append("Workflow has no steps defined")
        
        # Check for undefined input sources
        for step_id, step in workflow.steps.items():
            for input_name, source in step.in_.items():
                if isinstance(source, str):
                    if "/" in source:
                        source_step = source.split("/")[0]
                        if source_step not in workflow.steps:
                            errors.append(
                                f"Step '{step_id}' input '{input_name}' references "
                                f"undefined step '{source_step}'"
                            )
                    elif source not in workflow.inputs:
                        warnings.append(
                            f"Step '{step_id}' input '{input_name}' may reference "
                            f"undefined workflow input '{source}'"
                        )
        
        # Check output sources
        for output_id, output in workflow.outputs.items():
            if output.output_source:
                if "/" in output.output_source:
                    source_step = output.output_source.split("/")[0]
                    if source_step not in workflow.steps:
                        errors.append(
                            f"Output '{output_id}' references undefined step '{source_step}'"
                        )
        
        return CWLValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def get_docker_requirement(self, tool: CWLCommandLineTool) -> Optional[DockerRequirement]:
        """Extract DockerRequirement from tool hints/requirements."""
        for req_list in [tool.requirements or [], tool.hints or []]:
            for req in req_list:
                if isinstance(req, dict) and req.get("class") == "DockerRequirement":
                    return DockerRequirement(**req)
        return None


# Singleton instance
cwl_parser = CWLParser()
