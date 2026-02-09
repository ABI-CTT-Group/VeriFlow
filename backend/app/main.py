import uvicorn
import os
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
    if not os.path.exists(request.pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found at {request.pdf_path}")
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repo not found at {request.repo_path}")

    import uuid
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    try:
        # Pass user_context explicitly to the service
        await veriflow_service.run_workflow(
            run_id=run_id,
            pdf_path=request.pdf_path,
            repo_path=request.repo_path,
            stream_callback=manager.broadcast,
            user_context=request.user_context,  # <--- CRITICAL PASS
            client_id=request.client_id
        )
        
        return OrchestrationResponse(
            status="completed",
            message=f"Workflow run {run_id} finished.",
            result={"run_id": run_id}
        )

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)