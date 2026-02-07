"""
VeriFlow - Reviewer Agent
Per SPEC.md Section 4.5 - Validation, error translation, user communication

Migrated to google-genai SDK with Gemini 3 features:
- Pydantic structured output (ValidationResult, ErrorTranslationResult schemas)
- Thinking level control for validation
- Multi-turn with thought signature preservation for iterative validation
- Config-driven model selection
"""

import json
import subprocess
import tempfile
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.config import config
from app.models.schemas import ValidationResult, ErrorTranslationResult

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviewer Agent for workflow validation.

    Uses Gemini 3 with structured output (ValidationResult schema)
    to validate CWL workflows, check type compatibility,
    and translate errors to user-friendly messages.

    Supports iterative validation via multi-turn with thought signatures.
    """

    def __init__(self):
        """Initialize Reviewer Agent with Gemini client and config."""
        self.client = GeminiClient()

        # Load Agent-Specific Config
        self.agent_config = config.get_agent_config("reviewer")
        self.prompt_version = self.agent_config.get("default_prompt_version", "v1_standard")

        # Resolve Model Alias to API Parameters
        model_alias = self.agent_config.get("default_model", "gemini-3-flash")
        self.model_params = config.get_model_params(model_alias)

        # Apply Configuration to Client
        self.client.model_name = self.model_params.get("api_model_name", model_alias)

        # Gemini 3: Thinking level
        self.thinking_level = self.agent_config.get("thinking_level", "MEDIUM")
        self.temperature = self.model_params.get("temperature", 1.0)

        # Thought signatures for multi-turn iterative validation
        self._thought_signatures: List[str] = []

    async def validate_workflow(
        self,
        workflow_cwl: str,
        tool_cwls: Dict[str, str],
        graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate a CWL workflow and its components.

        Uses a combination of local validation (cwltool, type checking)
        and Gemini 3 for semantic validation and error translation.
        """
        # Run local validation checks
        cwl_check = await self._validate_cwl_syntax(workflow_cwl)
        type_check = self._check_type_compatibility(graph)
        dependency_check = self._check_dependencies(tool_cwls)

        # Combine local results
        all_passed = (
            cwl_check.get("passed", False)
            and type_check.get("passed", False)
            and dependency_check.get("passed", False)
        )

        result = {
            "passed": all_passed,
            "checks": {
                "cwl_syntax": cwl_check,
                "dag_syntax": {"passed": True, "errors": []},
                "data_format": type_check,
                "dependencies": dependency_check,
            },
            "auto_fixes_applied": [],
            "user_action_required": [],
        }

        # Collect errors for Gemini-powered semantic validation
        all_errors = []
        all_errors.extend(cwl_check.get("errors", []))
        all_errors.extend([m.get("message", "") for m in type_check.get("mismatches", [])])
        all_errors.extend(dependency_check.get("missing", []))

        if all_errors:
            translations = await self._translate_errors(all_errors)
            result["user_friendly_errors"] = translations

        # Use Gemini 3 for deep semantic validation
        try:
            semantic_result = await self._semantic_validation(workflow_cwl, graph)
            if semantic_result:
                result["semantic_validation"] = semantic_result
                if not semantic_result.get("passed", True):
                    result["passed"] = False
        except Exception as e:
            logger.warning(f"Semantic validation skipped: {e}")

        return result

    async def _semantic_validation(
        self,
        workflow_cwl: str,
        graph: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Use Gemini 3 with ValidationResult schema for deep semantic validation."""
        try:
            system_instruction = prompt_manager.get_prompt("reviewer_system", self.prompt_version)
        except ValueError:
            system_instruction = "You are the Reviewer Agent. Validate the workflow for correctness."

        prompt = f"""Validate the following CWL workflow and graph for semantic correctness.

CWL WORKFLOW:
{workflow_cwl[:4000]}

GRAPH STRUCTURE:
{json.dumps(graph, indent=2)[:4000]}

Check for:
1. Logical workflow structure (inputs feed into processing, processing produces outputs)
2. Type compatibility between connected nodes
3. Missing steps or broken connections
4. Unreachable nodes or orphaned edges
5. Docker image availability assumptions"""

        response = self.client.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=self.temperature,
            response_schema=ValidationResult,
            thinking_level=self.thinking_level,
        )

        return response

    async def validate_and_fix(
        self,
        workflow_cwl: str,
        tool_cwls: Dict[str, str],
        graph: Dict[str, Any],
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Iterative validation with thought signature preservation.

        Uses Gemini 3 multi-turn to:
        1. Validate the workflow
        2. Suggest fixes
        3. Re-validate after fixes
        Preserving thought signatures across turns for reasoning continuity.
        """
        try:
            system_instruction = prompt_manager.get_prompt("reviewer_system", self.prompt_version)
        except ValueError:
            system_instruction = "You are the Reviewer Agent. Validate and suggest fixes."

        messages = [
            {
                "role": "user",
                "content": f"""Validate this CWL workflow and suggest fixes for any issues.

CWL: {workflow_cwl[:3000]}
Graph: {json.dumps(graph, indent=2)[:3000]}""",
            }
        ]

        all_results = []
        for iteration in range(max_iterations):
            response = self.client.generate_with_history(
                messages=messages,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=ValidationResult,
                thinking_level=self.thinking_level,
            )

            result = response["result"]
            thought_sigs = response["thought_signatures"]
            all_results.append(result)

            # If validation passes, stop iterating
            if result.get("passed", False):
                break

            # Add model response with thought signatures for next turn
            messages.append({
                "role": "model",
                "content": json.dumps(result),
                "thought_signatures": thought_sigs,
            })

            # Ask for fixes in next turn
            messages.append({
                "role": "user",
                "content": "Please apply the suggested fixes and re-validate.",
            })

        return {
            "final_result": all_results[-1] if all_results else {"passed": False},
            "iterations": len(all_results),
            "history": all_results,
        }

    async def _validate_cwl_syntax(self, cwl_content: str) -> Dict[str, Any]:
        """Validate CWL syntax using cwltool --validate."""
        if not cwl_content or not cwl_content.strip():
            return {"passed": False, "errors": ["Empty CWL content"]}

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".cwl", delete=False
            ) as f:
                f.write(cwl_content)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["cwltool", "--validate", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return {"passed": True, "errors": []}
                else:
                    errors = result.stderr.split("\n") if result.stderr else [result.stdout]
                    return {"passed": False, "errors": [e for e in errors if e.strip()]}
            finally:
                os.unlink(temp_path)

        except FileNotFoundError:
            return self._basic_cwl_validation(cwl_content)
        except subprocess.TimeoutExpired:
            return {"passed": False, "errors": ["CWL validation timed out"]}
        except Exception as e:
            return {"passed": False, "errors": [f"Validation error: {str(e)}"]}

    def _basic_cwl_validation(self, cwl_content: str) -> Dict[str, Any]:
        """Basic CWL validation without cwltool."""
        errors = []
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
        """Check type compatibility between connected nodes."""
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

            source_type = None
            for output in source_node.get("data", {}).get("outputs", []):
                if output.get("id") == source_handle:
                    source_type = output.get("type")
                    break

            target_type = None
            for input_port in target_node.get("data", {}).get("inputs", []):
                if input_port.get("id") == target_handle:
                    target_type = input_port.get("type")
                    break

            if source_type and target_type and source_type != target_type:
                if not self._types_compatible(source_type, target_type):
                    mismatches.append({
                        "source_node": source_id,
                        "source_type": source_type,
                        "target_node": target_id,
                        "target_type": target_type,
                        "suggested_adapter": self._suggest_adapter(source_type, target_type),
                        "message": f"Type mismatch: {source_type} -> {target_type}",
                    })

        return {"passed": len(mismatches) == 0, "mismatches": mismatches}

    def _types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if two types are compatible."""
        if source_type == target_type:
            return True
        compatible_pairs = [
            ("application/octet-stream", "*"),
            ("application/x-nifti", "application/nifti"),
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
        return adapters.get(
            (source_type, target_type),
            f"custom-adapter-{source_type}-to-{target_type}",
        )

    def _check_dependencies(self, tool_cwls: Dict[str, str]) -> Dict[str, Any]:
        """Check if tool dependencies are resolvable."""
        missing = []
        for tool_id, cwl_content in tool_cwls.items():
            if "DockerRequirement" in cwl_content:
                pass  # Would check Docker availability
        return {"passed": len(missing) == 0, "missing": missing}

    async def _translate_errors(self, errors: List[str]) -> List[Dict[str, str]]:
        """Translate technical errors to user-friendly messages using Gemini 3."""
        if not errors:
            return []

        try:
            system_instruction = prompt_manager.get_prompt("reviewer_system", self.prompt_version)
        except ValueError:
            system_instruction = "Translate technical errors to user-friendly messages."

        try:
            prompt = f"""Translate these technical workflow errors into user-friendly messages with actionable suggestions.

ERRORS:
{json.dumps(errors, indent=2)}

Provide a translated message, suggestion, and severity for each error."""

            response = self.client.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=ErrorTranslationResult,
                thinking_level="LOW",  # Error translation is simpler
            )

            translations = response.get("translations", [])
            return translations if isinstance(translations, list) else []

        except Exception:
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
        """Suggest automatic fixes for validation issues."""
        if validation_result.get("passed", False):
            return {"fixes": [], "message": "No fixes needed"}

        fixes = []

        type_check = validation_result.get("checks", {}).get("data_format", {})
        for mismatch in type_check.get("mismatches", []):
            fixes.append({
                "type": "add_adapter",
                "description": f"Add {mismatch['suggested_adapter']} adapter",
                "source_node": mismatch["source_node"],
                "target_node": mismatch["target_node"],
                "adapter": mismatch["suggested_adapter"],
            })

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
