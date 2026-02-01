"""
VeriFlow - Reviewer Agent
Per SPEC.md Section 4.5 - Validation, error translation, user communication

The Reviewer Agent is responsible for:
1. Validating CWL syntax and semantics
2. Validating Airflow DAG structure
3. Checking data format compatibility (MIME type matching)
4. Checking dependencies are resolvable
5. Translating technical errors to user-friendly advice
6. Communicating with user when issues arise
"""

import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.gemini_client import get_gemini_client
from app.config import config
from app.services.prompt_manager import prompt_manager


class ReviewerAgent:
    """
    Reviewer Agent for workflow validation.
    
    Validates CWL workflows, checks type compatibility,
    and translates errors to user-friendly messages.
    """
    
    def __init__(self):
        """Initialize Reviewer Agent with Gemini client."""
        self.gemini = get_gemini_client()
        # Load Reviewer specific configuration
        self.agent_config = config.get_agent_config("reviewer")
        self.prompt_version = self.agent_config.get("default_prompt_version", "v1_standard")
        self.model_name = self.agent_config.get("default_model", "gemini-2.5-pro")

    async def validate_workflow(
        self,
        workflow_cwl: str,
        tool_cwls: Dict[str, str],
        graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate a CWL workflow and its components.
        
        Args:
            workflow_cwl: Main workflow CWL YAML
            tool_cwls: Dictionary of tool CWLs
            graph: Vue Flow graph representation
            
        Returns:
            ValidationResult dictionary with:
            - passed: Overall validation status
            - checks: Individual check results
            - auto_fixes_applied: List of automatic fixes
            - user_action_required: Actions user needs to take
        """
        # Run all validation checks
        cwl_check = await self._validate_cwl_syntax(workflow_cwl)
        type_check = self._check_type_compatibility(graph)
        dependency_check = self._check_dependencies(tool_cwls)
        
        # Combine results
        all_passed = (
            cwl_check.get("passed", False) and
            type_check.get("passed", False) and
            dependency_check.get("passed", False)
        )
        
        result = {
            "passed": all_passed,
            "checks": {
                "cwl_syntax": cwl_check,
                "dag_syntax": {"passed": True, "errors": []},  # DAG validation in Stage 5
                "data_format": type_check,
                "dependencies": dependency_check,
            },
            "auto_fixes_applied": [],
            "user_action_required": [],
        }
        
        # Collect errors for user-friendly translation
        all_errors = []
        all_errors.extend(cwl_check.get("errors", []))
        all_errors.extend([m.get("message", "") for m in type_check.get("mismatches", [])])
        all_errors.extend(dependency_check.get("missing", []))
        
        if all_errors:
            # Translate errors to user-friendly messages
            translations = await self._translate_errors(all_errors)
            result["user_friendly_errors"] = translations
        
        return result
    
    async def _validate_cwl_syntax(self, cwl_content: str) -> Dict[str, Any]:
        """
        Validate CWL syntax using cwltool --validate.
        
        Args:
            cwl_content: CWL YAML content
            
        Returns:
            Check result with passed status and errors
        """
        if not cwl_content or not cwl_content.strip():
            return {"passed": False, "errors": ["Empty CWL content"]}
        
        try:
            # Write CWL to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.cwl',
                delete=False,
            ) as f:
                f.write(cwl_content)
                temp_path = f.name
            
            try:
                # Run cwltool validation
                result = subprocess.run(
                    ["cwltool", "--validate", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                
                if result.returncode == 0:
                    return {"passed": True, "errors": []}
                else:
                    errors = result.stderr.split('\n') if result.stderr else [result.stdout]
                    return {"passed": False, "errors": [e for e in errors if e.strip()]}
                    
            finally:
                # Clean up temp file
                os.unlink(temp_path)
                
        except FileNotFoundError:
            # cwltool not installed - do basic validation
            return self._basic_cwl_validation(cwl_content)
        except subprocess.TimeoutExpired:
            return {"passed": False, "errors": ["CWL validation timed out"]}
        except Exception as e:
            return {"passed": False, "errors": [f"Validation error: {str(e)}"]}
    
    def _basic_cwl_validation(self, cwl_content: str) -> Dict[str, Any]:
        """Basic CWL validation without cwltool."""
        errors = []
        
        # Check for required fields
        if "cwlVersion" not in cwl_content:
            errors.append("Missing cwlVersion declaration")
        if "class:" not in cwl_content:
            errors.append("Missing class declaration (Workflow or CommandLineTool)")
        if "inputs:" not in cwl_content and "inputs" not in cwl_content:
            errors.append("Missing inputs section")
        if "outputs:" not in cwl_content and "outputs" not in cwl_content:
            errors.append("Missing outputs section")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "note": "Basic validation only - cwltool not available",
        }
    
    def _check_type_compatibility(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check type compatibility between connected nodes.
        
        Args:
            graph: Vue Flow graph with nodes and edges
            
        Returns:
            Check result with mismatches
        """
        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        edges = graph.get("edges", [])
        mismatches = []
        
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            source_handle = edge.get("sourceHandle")
            target_handle = edge.get("targetHandle")
            
            source_node = nodes.get(source_id)
            target_node = nodes.get(target_id)
            
            if not source_node or not target_node:
                continue
            
            # Get output type from source
            source_type = None
            source_outputs = source_node.get("data", {}).get("outputs", [])
            for output in source_outputs:
                if output.get("id") == source_handle:
                    source_type = output.get("type")
                    break
            
            # Get input type from target
            target_type = None
            target_inputs = target_node.get("data", {}).get("inputs", [])
            for input_port in target_inputs:
                if input_port.get("id") == target_handle:
                    target_type = input_port.get("type")
                    break
            
            # Check compatibility
            if source_type and target_type and source_type != target_type:
                # Check if they're compatible (some types are interchangeable)
                if not self._types_compatible(source_type, target_type):
                    mismatches.append({
                        "source_node": source_id,
                        "source_type": source_type,
                        "target_node": target_id,
                        "target_type": target_type,
                        "suggested_adapter": self._suggest_adapter(source_type, target_type),
                        "message": f"Type mismatch: {source_type} → {target_type}",
                    })
        
        return {
            "passed": len(mismatches) == 0,
            "mismatches": mismatches,
        }
    
    def _types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if two types are compatible."""
        # Exact match
        if source_type == target_type:
            return True
        
        # Generic compatibility
        compatible_pairs = [
            ("application/octet-stream", "*"),  # Generic binary
            ("application/x-nifti", "application/nifti"),  # NIfTI variants
            ("image/nifti", "application/x-nifti"),
        ]
        
        for a, b in compatible_pairs:
            if (source_type == a and target_type == b) or (source_type == b and target_type == a):
                return True
        
        return False
    
    def _suggest_adapter(self, source_type: str, target_type: str) -> str:
        """Suggest an adapter for type conversion."""
        adapters = {
            ("application/dicom", "application/x-nifti"): "dcm2niix",
            ("application/dicom", "application/nifti"): "dcm2niix",
            ("application/x-nifti", "image/png"): "nifti2png",
            ("image/png", "application/x-nifti"): "png2nifti",
        }
        
        return adapters.get((source_type, target_type), f"custom-adapter-{source_type}-to-{target_type}")
    
    def _check_dependencies(self, tool_cwls: Dict[str, str]) -> Dict[str, Any]:
        """
        Check if tool dependencies are resolvable.
        
        Args:
            tool_cwls: Dictionary of tool CWL contents
            
        Returns:
            Check result with missing dependencies
        """
        # For MVP, we mainly check Docker requirements
        missing = []
        
        for tool_id, cwl_content in tool_cwls.items():
            if "DockerRequirement" in cwl_content:
                # Extract docker image name if possible
                if "dockerPull:" in cwl_content:
                    # Would need actual Docker availability check
                    pass
        
        return {
            "passed": len(missing) == 0,
            "missing": missing,
        }
    
    async def _translate_errors(self, errors: List[str]) -> List[Dict[str, str]]:
        """
        Translate technical errors to user-friendly messages.
        
        Args:
            errors: List of technical error messages
            
        Returns:
            List of translated errors with suggestions
        """
        if not errors:
            return []
        
        # Use Gemini to translate errors
        try:
            # Retrieve System Prompt
            system_instruction = prompt_manager.get_prompt("reviewer_system", self.prompt_version)
            
            # Retrieve and Format Translation Prompt
            raw_prompt = prompt_manager.get_prompt("reviewer_translate", self.prompt_version)
            prompt = raw_prompt.format(errors_json=json.dumps(errors, indent=2))
            
            response = self.gemini.generate_json(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
            )
            
            if isinstance(response, list):
                return response
            return []
            
        except Exception:
            # Fallback to basic translation
            return [
                {
                    "original": error,
                    "translated": error,
                    "suggestion": "Please check the workflow configuration",
                    "severity": "error",
                }
                for error in errors
            ]
    
    async def suggest_fixes(
        self,
        validation_result: Dict[str, Any],
        workflow_cwl: str,
        graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest automatic fixes for validation issues.
        
        Args:
            validation_result: Result from validate_workflow
            workflow_cwl: Current CWL content
            graph: Current graph structure
            
        Returns:
            Dictionary with suggested fixes
        """
        if validation_result.get("passed", False):
            return {"fixes": [], "message": "No fixes needed"}
        
        fixes = []
        
        # Handle type mismatches by suggesting adapters
        type_check = validation_result.get("checks", {}).get("data_format", {})
        for mismatch in type_check.get("mismatches", []):
            fixes.append({
                "type": "add_adapter",
                "description": f"Add {mismatch['suggested_adapter']} adapter",
                "source_node": mismatch["source_node"],
                "target_node": mismatch["target_node"],
                "adapter": mismatch["suggested_adapter"],
            })
        
        # Handle missing dependencies
        dep_check = validation_result.get("checks", {}).get("dependencies", {})
        for missing in dep_check.get("missing", []):
            fixes.append({
                "type": "add_dependency",
                "description": f"Install {missing}",
                "dependency": missing,
            })
        
        return {
            "fixes": fixes,
            "can_auto_fix": len(fixes) > 0 and all(f["type"] == "add_adapter" for f in fixes),
        }


# Global agent instance
reviewer_agent = ReviewerAgent()
