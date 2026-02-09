import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Union

# Service Imports
from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.services.websocket_manager import manager 
from app.config import config
from app.state import AgentState

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_repo_value(isa_json: Dict[str, Any]) -> str:
    try:
        if not isa_json: return ""
        return isa_json.get("studyDesign", {}).get("paper", {}).get("github", "")
    except Exception: return ""

def _create_stream_callback(client_id: str, agent_name: str):
    async def callback(chunk: str):
        if client_id:
            await manager.send_message(client_id, {
                "type": "agent_stream",
                "agent": agent_name,
                "chunk": chunk
            })
    return callback if client_id else None

async def _notify_status(client_id: str, message: str, status: str = "running"):
    if client_id:
        await manager.send_message(client_id, {
            "type": "status_update",
            "status": status,
            "message": message
        })

def _log_node_execution(run_id: str, step_name: str, data: Dict[str, Any]):
    try:
        if not run_id: run_id = "unknown_run"
        # Anchor log dir to project root
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs" / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / f"{step_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to log node execution for {step_name}: {e}")

def _clean_and_parse_json(content: Union[str, Dict]) -> Dict[str, Any]:
    """Ensures content is a dict, stripping Markdown if necessary."""
    if isinstance(content, dict):
        return content
    
    # It's a string, try to clean
    cleaned = str(content).strip()
    
    # Remove Markdown Code Blocks if present
    if "```" in cleaned:
        lines = cleaned.splitlines()
        # Filter out lines starting with ```
        cleaned_lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(cleaned_lines)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON content: {cleaned[:100]}...")
        return {"error": "JSON Parse Error", "raw_content": content}

def _persist_artifact(run_id: str, filename: str, data: Any) -> str:
    """Saves artifact to disk using PROJECT ABSOLUTE PATH and returns it."""
    # Anchor to project root (backend/)
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "data" / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / filename
    
    # Ensure data is clean JSON before saving
    clean_data = _clean_and_parse_json(data)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2, default=str)
        
    logger.info(f"Saved artifact to: {file_path}")
    return str(file_path.absolute())

def _resolve_model_name(agent_name: str) -> str:
    agent_conf = config.get_agent_config(agent_name)
    model_alias = agent_conf.get("default_model", "gemini-2.0-flash")
    model_params = config.get_model_params(model_alias)
    return model_params.get("api_model_name", model_alias)

def _get_prompt_version(agent_name: str) -> str:
    agent_conf = config.get_agent_config(agent_name)
    default = "v3_standard" if agent_name == "engineer" else "v1_standard"
    return agent_conf.get("default_prompt_version", default)

def _read_repo_context(repo_path: str) -> str:
    context = []
    MAX_CHARS = 100000 
    total_chars = 0
    try:
        for root, _, files in os.walk(repo_path):
            if total_chars >= MAX_CHARS: break
            for file in files:
                if file.endswith(('.py', '.txt', '.md', '.sh', '.yaml', '.yml', 'Dockerfile', 'CWL', 'cwl')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            entry = f"--- File: {file} ---\n{content}\n"
                            context.append(entry)
                            total_chars += len(entry)
                    except Exception: continue 
    except Exception: return "Error reading repository context."
    return "\n".join(context)

def _mock_validate_artifacts(artifacts: Dict[str, Any]) -> List[str]:
    errors = []
    # Ensure it's a dict (handle stringified input case)
    if isinstance(artifacts, str):
        artifacts = _clean_and_parse_json(artifacts)

    if not isinstance(artifacts, dict):
        return ["Artifact generation failed or returned invalid format."]
    
    workflow = artifacts.get("workflow", {})
    components = artifacts.get("components", [])
    
    if not workflow and not components:
        if "dockerfile" not in str(artifacts).lower() and "cwl" not in str(artifacts).lower():
             errors.append("Output missing essential 'workflow' or 'components' sections.")
    
    return errors

# --- Node Implementations ---

async def scholar_node(state: AgentState) -> Dict[str, Any]:
    run_id = state.get("run_id", str(uuid.uuid4()))
    client_id = state.get("client_id")
    user_context = state.get("user_context", None)
    directive = state.get("agent_directives", {}).get("scholar")
    step_name = "1_scholar"
    
    await _notify_status(client_id, "Scholar Agent: Analyzing publication...", status="running")
    
    client = GeminiClient()
    model_name = _resolve_model_name("scholar")
    prompt_version = _get_prompt_version("scholar")
    
    system_prompt = prompt_manager.get_prompt("scholar_system", version=prompt_version)
    extraction_prompt = prompt_manager.get_prompt("scholar_extraction", version=prompt_version)
    full_prompt = f"{system_prompt}\n\n{extraction_prompt}"
    
    if user_context: full_prompt += f"\n\nINITIAL USER CONTEXT:\n{user_context}"
    if directive: full_prompt += f"\n\nIMPORTANT USER DIRECTIVE:\n'{directive}'"
    
    response = await client.analyze_file(
        file_path=state["pdf_path"],
        prompt=full_prompt,
        model=model_name,
        stream_callback=_create_stream_callback(client_id, "Scholar")
    )
    
    result = _clean_and_parse_json(response["result"])
    
    # Save & Update DB
    isa_path = _persist_artifact(run_id, "scholar_isa.json", result)
    from app.services.database_sqlite import database_service
    database_service.create_or_update_agent_session(
        run_id=run_id,
        scholar_extraction_complete=True,
        scholar_isa_json_path=isa_path
    )

    _log_node_execution(run_id, step_name, {
        "inputs": {"pdf_path": state["pdf_path"], "directive": directive},
        "final_output": result
    })
    
    await _notify_status(client_id, "Scholar Agent: Analysis complete.", status="completed")
    return {"isa_json": result, "run_id": run_id}


async def engineer_node(state: AgentState) -> Dict[str, Any]:
    run_id = state.get("run_id")
    client_id = state.get("client_id")
    current_retry_count = state.get("retry_count", 0)
    step_name = f"2_engineer_retry_{current_retry_count}"

    directive = state.get("agent_directives", {}).get("engineer")
    
    msg = "Engineer Agent: Applying user directives..." if directive else f"Engineer Agent: Generating artifacts (Attempt {current_retry_count + 1})..."
    await _notify_status(client_id, msg, status="running")
    
    client = GeminiClient()
    model_name = _resolve_model_name("engineer")
    
    prompt_version = _get_prompt_version("engineer")
    if prompt_version == "v1_standard": prompt_version = "v3_standard"

    isa_json = state.get("isa_json", {})
    repo_path = state.get("repo_path")
    repo_context = state.get("repo_context") or _read_repo_context(repo_path)
    
    base_prompt = prompt_manager.get_prompt("engineer_cwl_gen", version=prompt_version)
    
    # Format Prompt
    if '**ISA JSON:**' not in base_prompt:
        prompt = base_prompt.format(
            isa_json=json.dumps(isa_json, indent=2),
            repo_context=repo_context,
            previous_errors=state.get("validation_errors", [])
        )
    else:
        repo_url = get_repo_value(isa_json)
        prompt = base_prompt.replace("{isa_json}", json.dumps(isa_json, indent=2)) \
                            .replace("{repo_url}", str(repo_url)) \
                            .replace("{repo_context}", str(repo_context)) \
                            .replace("{previous_errors}", str(state.get("validation_errors", [])))

    if directive:
        prompt += f"""
        \nIMPORTANT USER DIRECTIVE:
        The user has reviewed your previous work and requests the following changes:
        '{directive}'
        Please regenerate the code strictly following this directive.
        CRITICAL: Return ONLY valid JSON matching the structure (mapping_logic, components, workflow). 
        Do not wrap in Markdown code blocks.
        """
    
    response = await client.generate_content(
        prompt=prompt,
        model=model_name,
        stream_callback=_create_stream_callback(client_id, "Engineer")
    )
    
    result = _clean_and_parse_json(response["result"])

    # Save & Update DB
    engineer_path = _persist_artifact(run_id, "engineer_output.json", result)
    from app.services.database_sqlite import database_service
    database_service.create_or_update_agent_session(
        run_id=run_id,
        engineer_cwl_path=engineer_path
    )
    
    await _notify_status(client_id, "Engineer Agent: Generation complete.", status="completed")
    
    _log_node_execution(run_id, step_name, {
        "inputs": {"directive": directive},
        "final_output": result
    })
    
    return {
        "repo_context": repo_context,
        "generated_code": result,
        "retry_count": current_retry_count + 1
    }


async def validate_node(state: AgentState) -> Dict[str, Any]:
    run_id = state.get("run_id")
    client_id = state.get("client_id")
    current_retry_count = state.get("retry_count", 0)
    step_name = f"3_validate_retry_{current_retry_count}"
    
    await _notify_status(client_id, "System: Validating artifacts...", status="running")
    
    generated_code = state.get("generated_code", {})
    errors = _mock_validate_artifacts(generated_code)
    
    _log_node_execution(run_id, step_name, {"errors": errors})
    
    msg = f"System: Validation failed with {len(errors)} errors." if errors else "System: Validation successful."
    await _notify_status(client_id, msg, status="completed")
    
    return {"validation_errors": errors}


async def reviewer_node(state: AgentState) -> Dict[str, Any]:
    run_id = state.get("run_id")
    client_id = state.get("client_id")
    step_name = "4_reviewer"
    
    directive = state.get("agent_directives", {}).get("reviewer")
    await _notify_status(client_id, "Reviewer Agent: Validating...", status="running")
    
    client = GeminiClient()
    model_name = _resolve_model_name("reviewer")
    prompt_version = _get_prompt_version("reviewer")
    
    isa_json = state.get("isa_json")
    generated_code = state.get("generated_code")
    validation_errors = state.get("validation_errors", [])
    
    prompt = prompt_manager.get_prompt("reviewer_critique", version=prompt_version).format(
        isa_json=json.dumps(isa_json, indent=2),
        generated_code=json.dumps(generated_code, indent=2),
        validation_errors=validation_errors
    )
    
    if directive: prompt += f"\n\nUSER DIRECTIVE:\n'{directive}'"

    response = await client.generate_content(
        prompt=prompt,
        model=model_name,
        stream_callback=_create_stream_callback(client_id, "Reviewer")
    )
    
    result = response["result"]
    decision = "rejected"
    feedback = str(result)
    
    if isinstance(result, dict):
        feedback = json.dumps(result)
        decision = result.get("decision", "rejected").lower()
    elif "APPROVED" in str(result).upper() and not validation_errors:
        decision = "approved"

    # Update DB
    from app.services.database_sqlite import database_service
    database_service.create_or_update_agent_session(run_id=run_id, workflow_complete=True)

    await _notify_status(client_id, "Reviewer Agent: Review complete.", status="completed")
    
    _log_node_execution(run_id, step_name, {"decision": decision})
    
    return {"review_decision": decision, "review_feedback": feedback}