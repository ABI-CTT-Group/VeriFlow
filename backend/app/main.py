import uvicorn
import os
import uuid
import json
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.graph.workflow import app_graph
from app.state import AgentState
from app.services.veriflow_service import veriflow_service
from app.services.websocket_manager import manager

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veriflow_backend")

app = FastAPI(title="VeriFlow Orchestrator")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Routers
from app.api import publications, workflows, websockets, mamamia_cache, chat

app.include_router(publications.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(mamamia_cache.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(websockets.router)

class OrchestrationRequest(BaseModel):
    pdf_path: str
    repo_path: str
    user_context: Optional[str] = None  # Captured here
    client_id: Optional[str] = None 

class OrchestrationResponse(BaseModel):
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {"message": "VeriFlow Orchestrator is operational."}

@app.post("/api/v1/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_workflow(request: OrchestrationRequest, background_tasks: BackgroundTasks):
    """
    Asynchronously invokes the VeriFlow LangGraph.
    """
    # 1. Validate Paths
    if not os.path.exists(request.pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found at {request.pdf_path}")
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repo not found at {request.repo_path}")

    # 2. Generate Run ID
    # Use the more specific run_ID format from the incoming changes
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    # 3. Start Background Task
    # Use veriflow_service.run_workflow directly in background task
    background_tasks.add_task(
        veriflow_service.run_workflow,
        run_id=run_id,
        pdf_path=request.pdf_path,
        repo_path=request.repo_path,
        stream_callback=manager.broadcast,
        user_context=request.user_context,
        client_id=request.client_id
    )

    return OrchestrationResponse(
        status="started",
        message=f"Orchestration started in background with run_id: {run_id}",
        result={"run_id": run_id}
    )

@app.get("/api/v1/orchestrate/{run_id}/artifacts/{agent_name}")
async def get_orchestration_artifact(run_id: str, agent_name: str):
    """
    Retrieves a specific artifact (log file) for a given run and agent.
    Example: agent_name='scholar' -> returns content of logs/{run_id}/1_scholar.json
    """
    # Map agent name to filename pattern
    filename_map = {
        "scholar": "1_scholar.json",
        "engineer": "2_engineer.json", # Note: engineer might have retries, handling simplest case first or latest?
        # For engineer/validate nodes which have retries, we might need a more robust way or just grab the latest file matching pattern 
        # But per user request "1_scholar.json", let's stick to that for now.
    }
    
    target_filename = filename_map.get(agent_name)
    if not target_filename:
        # Fallback: try to find file starting with agent_name or containing it?
        # For now, simplistic mapping as per "1_scholar.json" request
        if agent_name == "scholar": target_filename = "1_scholar.json"
        else: raise HTTPException(status_code=400, detail=f"Unknown agent artifact: {agent_name}")

    log_dir = os.path.join("logs", run_id)
    file_path = os.path.join(log_dir, target_filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read artifact: {e}")
    
    raise HTTPException(status_code=404, detail="Artifact not found (yet)")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)