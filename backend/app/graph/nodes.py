import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List

# Service Imports
from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.services.database_sqlite import database_service
from app.config import config
from app.state import AgentState

logger = logging.getLogger(__name__)

# --- Logging Helper ---

def _log_node_execution(run_id: str, step_name: str, data: Dict[str, Any]):
    """
    Saves node execution details to logs/<run_id>/<step_name>.json.
    Standardized observability for all nodes.
    """
    try:
        if not run_id:
            run_id = "unknown_run"
            
        log_dir = Path("logs") / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = log_dir / f"{step_name}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"Failed to log node execution for {step_name}: {e}")

# --- Helper Functions ---

def _resolve_model_name(agent_name: str) -> str:
    """Resolves correct API model name from config."""
    agent_conf = config.get_agent_config(agent_name)
    model_alias = agent_conf.get("default_model", "gemini-2.0-flash")
    model_params = config.get_model_params(model_alias)
    return model_params.get("api_model_name", model_alias)

def _get_prompt_version(agent_name: str) -> str:
    agent_conf = config.get_agent_config(agent_name)
    return agent_conf.get("default_prompt_version", "v1_standard")

def _read_repo_context(repo_path: str) -> str:
    context = []
    MAX_CHARS = 50000 
    total_chars = 0
    try:
        for root, _, files in os.walk(repo_path):
            if total_chars >= MAX_CHARS:
                break
            for file in files:
                if file.endswith(('.py', '.txt', '.md', '.sh', '.yaml', '.yml', 'Dockerfile')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            rel_path = os.path.relpath(file_path, repo_path)
                            entry = f"--- File: {rel_path} ---\n{content}\n"
                            context.append(entry)
                            total_chars += len(entry)
                    except Exception:
                        continue 
    except Exception:
        return "Error reading repository context."
    return "\n".join(context)

def _mock_validate_artifacts(artifacts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mocks the build/validation process and returns a structured report.
    """
    report = {}
    
    if not isinstance(artifacts, dict):
        return {"workflow": {"status": "invalid", "errors": ["Artifact generation failed or returned invalid format."]}}

    # Validate each tool CWL file
    tool_cwls = artifacts.get("tool_cwls", {})
    if isinstance(tool_cwls, dict):
        for filename, content in tool_cwls.items():
            errors = []
            if "cwlVersion" not in str(content):
                errors.append("Missing or invalid 'cwlVersion'.")
            if "class: CommandLineTool" not in str(content):
                errors.append("Missing or invalid 'class: CommandLineTool'.")
            
            status = "invalid" if errors else "valid"
            report[filename] = {"status": status, "errors": errors}

    # Validate the main workflow CWL
    workflow_cwl = artifacts.get("workflow_cwl", "")
    wf_errors = []
    if "cwlVersion" not in str(workflow_cwl):
        wf_errors.append("Missing or invalid 'cwlVersion'.")
    if "class: Workflow" not in str(workflow_cwl):
        wf_errors.append("Missing or invalid 'class: Workflow'.")
    
    report["workflow.cwl"] = {"status": "invalid" if wf_errors else "valid", "errors": wf_errors}

    # Validate Dockerfile
    dockerfile = artifacts.get("dockerfiles", {}).get("Dockerfile", "")
    docker_errors = []
    if "FROM" not in str(dockerfile):
        docker_errors.append("Dockerfile is missing a 'FROM' instruction.")
    
    report["Dockerfile"] = {"status": "invalid" if docker_errors else "valid", "errors": docker_errors}

    return report

# --- Node Implementations ---

async def scholar_node(state: AgentState) -> Dict[str, Any]:
    """Scholar Agent: Extracts ISA JSON from PDF."""
    run_id = state.get("run_id", str(uuid.uuid4()))
    step_name = "1_scholar"
    
    client = GeminiClient()
    model_name = _resolve_model_name("scholar")
    prompt_version = _get_prompt_version("scholar")
    
    system_prompt = prompt_manager.get_prompt("scholar_system", version=prompt_version)
    extraction_prompt = prompt_manager.get_prompt("scholar_extraction", version=prompt_version)
    full_prompt = f"{system_prompt}\n\n{extraction_prompt}"
    
    response = await client.analyze_file(
        file_path=state["pdf_path"],
        prompt=full_prompt,
        model=model_name
    )
    
    result = response
    
    _log_node_execution(run_id, step_name, {
        "inputs": {"pdf_path": state["pdf_path"]},
        "prompt_truncated": full_prompt[:200] + "...",
        "final_output": result
    })
    
    # --- Persist to DB ---
    pdf_path = Path(state["pdf_path"])
    log_dir = Path("logs") / run_id
    isa_json_path = log_dir / "scholar_isa.json"
    with open(isa_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    database_service.create_or_update_agent_session(
        run_id=run_id,
        scholar_extraction_complete=True,
        scholar_isa_json_path=str(isa_json_path.resolve())
    )
    
    return {"isa_json": result, "run_id": run_id}


async def engineer_node(state: AgentState) -> Dict[str, Any]:
    """Engineer Agent: Generates CWL/Dockerfile."""
    run_id = state.get("run_id")
    step_name = f"2_engineer_retry_{state.get('retry_count', 0)}"
    
    client = GeminiClient()
    model_name = _resolve_model_name("engineer")
    prompt_version = _get_prompt_version("engineer")
    
    isa_json = state.get("isa_json", {})
    repo_path = state.get("repo_path")
    repo_context = state.get("repo_context")
    if not repo_context:
        repo_context = _read_repo_context(repo_path)
    
    base_prompt = prompt_manager.get_prompt("engineer_cwl_gen", version=prompt_version)
    prompt = base_prompt.format(
        isa_json=json.dumps(isa_json, indent=2),
        repo_context=repo_context,
        previous_errors=state.get("validation_errors", [])
    )
    
    response = await client.generate_content(
        prompt=prompt,
        model=model_name
    )
    
    result = response
    
    _log_node_execution(run_id, step_name, {
        "inputs": {
            "isa_summary": "ISA JSON present",
            "repo_path": repo_path
        },
        "prompt_truncated": prompt[:200] + "...",
        "final_output": result
    })
    
    # --- Persist to DB ---
    log_dir = Path("logs") / run_id
    engineer_code_path = log_dir / "engineer_code.json"
    with open(engineer_code_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    database_service.create_or_update_agent_session(
        run_id=run_id,
        engineer_workflow_id=f"wf_{run_id}",
        engineer_cwl_path=str(engineer_code_path.resolve())
    )
    
    return {
        "repo_context": repo_context,
        "generated_code": result,
        "retry_count": state["retry_count"] + 1
    }


async def validate_node(state: AgentState) -> Dict[str, Any]:
    """Validation Node: Mocks execution."""
    run_id = state.get("run_id")
    step_name = f"3_validate_retry_{state.get('retry_count', 0)}"
    
    generated_code = state.get("generated_code", {})
    report = _mock_validate_artifacts(generated_code)
    
    # Check if there are any invalid statuses in the report
    has_errors = any(v["status"] == "invalid" for v in report.values() if isinstance(v, dict))

    _log_node_execution(run_id, step_name, {
        "inputs": {"generated_code_keys": list(generated_code.keys()) if isinstance(generated_code, dict) else "Invalid Format"},
        "final_output": report
    })
    
    return {
        "generated_code": generated_code, # Pass through for the service layer
        "validation_report": report,
        "validation_errors": ["Validation failed"] if has_errors else [] # Keep for conditional logic
    }


async def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Reviewer Agent: Critiques the solution."""
    run_id = state.get("run_id")
    step_name = "4_reviewer"
    
    client = GeminiClient()
    model_name = _resolve_model_name("reviewer")
    prompt_version = _get_prompt_version("reviewer")
    
    isa_json = state.get("isa_json")
    # Correct Key Usage: generated_code (Fixes crash)
    generated_code = state.get("generated_code")
    validation_errors = state.get("validation_errors", [])
    
    prompt_template = prompt_manager.get_prompt("reviewer_critique", version=prompt_version)
    
    # Format prompt safely even if generated_code is malformed
    prompt = prompt_template.format(
        isa_json=json.dumps(isa_json, indent=2),
        generated_code=json.dumps(generated_code, indent=2),
        validation_errors=validation_errors
    )
    
    response = await client.generate_content(
        prompt=prompt,
        model=model_name
    )
    
    result = response
    
    # Normalize Decision
    decision = "rejected"
    feedback_text = str(result)
    
    if isinstance(result, dict):
        feedback_text = json.dumps(result)
        if "decision" in result:
             decision = result["decision"].lower()
    
    if "APPROVED" in feedback_text.upper() and not validation_errors:
        decision = "approved"

    _log_node_execution(run_id, step_name, {
        "inputs": {
            "validation_status": "Passed" if not validation_errors else "Failed",
            "validation_errors": validation_errors
        },
        "prompt_truncated": prompt[:200] + "...",
        "raw_output": result,
        "derived_decision": decision
    })
    
    database_service.create_or_update_agent_session(
        run_id=run_id,
        workflow_complete=True
    )
    
    return {
        "review_decision": decision,
        "review_feedback": feedback_text
    }