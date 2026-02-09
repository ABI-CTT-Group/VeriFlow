from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import logging

from app.services.database_sqlite import database_service
from app.services.veriflow_service import veriflow_service
from app.services.gemini_client import GeminiClient
from app.services.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class RestartRequest(BaseModel):
    directive: str  # The final instruction agreed upon

@router.post("/chat/{run_id}/{agent_name}")
async def chat_with_agent(run_id: str, agent_name: str, request: ChatRequest):
    """
    Consultation Mode: Discuss previous outputs with a specific agent.
    """
    # 1. Fetch State Context
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run ID not found")
        
    context_str = ""
    if agent_name == "scholar":
        # Load Scholar Output
        path = session.get("scholar_isa_json_path")
        if path and os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                context_str = f"Your previous extracted ISA JSON:\n{json.dumps(data, indent=2)}"
                
    elif agent_name == "engineer":
        # Load Engineer Output
        path = session.get("engineer_cwl_path")
        if path and os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                context_str = f"Your previous generated code/CWL:\n{json.dumps(data, indent=2)}"
                
    elif agent_name == "reviewer":
         # Context is usually the decision and errors
         context_str = f"Previous Validation Errors: {session.get('validation_errors', [])}"

    # 2. Construct Prompt
    client = GeminiClient()
    
    system_instruction = f"""
    You are the {agent_name.capitalize()} Agent in the VeriFlow system.
    You previously executed a task. The user is now discussing your output to refine it.
    
    CONTEXT OF YOUR PREVIOUS WORK:
    {context_str[:15000]} # Truncate if too large
    
    GOAL: Discuss the user's concerns. 
    If the user wants changes, help formulate a clear "Directive" that can be applied to the next run.
    """
    
    # Convert chat history to Gemini format if needed, or just append to prompt
    # For simplicity in this endpoint, we concat the history
    chat_history_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in request.messages])
    
    full_prompt = f"{system_instruction}\n\nCONVERSATION:\n{chat_history_text}\n\n{agent_name.capitalize()}:"
    
    # 3. Get LLM Response
    response = await client.generate_content(prompt=full_prompt)
    
    return {"reply": response.get("raw_parsed", response.get("raw", "I could not generate a response."))}


@router.post("/chat/{run_id}/{agent_name}/apply")
async def apply_and_restart(run_id: str, agent_name: str, request: RestartRequest):
    """
    Apply the plan: Update state with directive and restart workflow from this agent.
    """
    logger.info(f"Applying directive for {agent_name} on run {run_id}")
    
    # 1. Retrieve current directives
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    current_directives = session.get("agent_directives", {})
    
    # 2. Update with new directive
    current_directives[agent_name] = request.directive
    
    database_service.create_or_update_agent_session(
        run_id=run_id,
        agent_directives=current_directives
    )
    
    # 3. Trigger Restart (Background Task logic or direct await)
    # We await here for the response, but in prod use BackgroundTasks
    try:
        await veriflow_service.restart_workflow(
            run_id=run_id,
            start_node=agent_name,
            stream_callback=manager.broadcast
        )
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "restarted", "message": f"Workflow restarted from {agent_name} with new directive."}