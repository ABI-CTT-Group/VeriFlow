import uvicorn
import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.graph.workflow import app_graph
from app.state import AgentState

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
from app.api import publications, workflows, websockets, mamamia_cache

app.include_router(publications.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(mamamia_cache.router, prefix="/api/v1")
app.include_router(websockets.router) # WebSocket endpoint /ws/{client_id}

class OrchestrationRequest(BaseModel):
    pdf_path: str
    repo_path: str
    client_id: Optional[str] = None # Optional client_id for real-time updates

class OrchestrationResponse(BaseModel):
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {"message": "VeriFlow Orchestrator is operational."}

@app.post("/api/v1/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_workflow(request: OrchestrationRequest):
    """
    Asynchronously invokes the VeriFlow LangGraph.
    Generates Docker/CWL/Airflow artifacts from PDF and Repo.
    """
    # 1. Validate Paths
    if not os.path.exists(request.pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found at {request.pdf_path}")
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repo not found at {request.repo_path}")

    # 2. Initialize State
    initial_state: AgentState = {
        "pdf_path": request.pdf_path,
        "repo_path": request.repo_path,
        "client_id": request.client_id, # Pass client_id to graph state
        "isa_json": None,
        "repo_context": None,
        "generated_code": {},
        "validation_errors": [],
        "retry_count": 0,
        "review_decision": None,
        "review_feedback": None
    }

    try:
        logger.info(f"Starting workflow for {request.pdf_path}")
        
        # 3. Invoke Graph (Async)
        # Using ainvoke directly awaits the result. 
        # In a real heavy-load scenario, we would use BackgroundTasks and a DB 
        # to store state, but for this specific instruction we await execution.
        final_state = await app_graph.ainvoke(initial_state)
        
        # 4. Process Result
        decision = final_state.get("review_decision", "unknown")
        
        return OrchestrationResponse(
            status="completed",
            message=f"Workflow finished with decision: {decision}",
            result={
                "isa_json": final_state.get("isa_json"),
                "generated_code": final_state.get("generated_code"),
                "review_decision": decision,
                "review_feedback": final_state.get("review_feedback"),
                "errors": final_state.get("validation_errors")
            }
        )

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)