"""
VeriFlow API - VeriFlow Router
Handles the execution of the langraph-based workflow.
"""
import uuid, json
import tempfile
import zipfile
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.veriflow_service import veriflow_service
from app.services.database_sqlite import database_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Cleanup Function ---
def cleanup_run_directory(temp_dir: Path):
    """Safely removes the temporary directory for a run."""
    try:
        if temp_dir.exists() and temp_dir.is_dir():
            shutil.rmtree(temp_dir)
            print(f"Successfully cleaned up directory: {temp_dir}")
    except Exception as e:
        print(f"Error cleaning up directory {temp_dir}: {e}")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, run_id: str):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, run_id: str):
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)
    
    async def broadcast(self, message: dict, run_id: str):
        if run_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[run_id].remove(conn)

manager = ConnectionManager()

class RunResponse(BaseModel):
    """Response from the run endpoint."""
    run_id: str
    status: str
    message: str

@router.post("/veriflow/run", response_model=RunResponse)
async def run_veriflow(
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    context_file: Optional[UploadFile] = File(None),
):
    """
    Upload a PDF and context file to run the VeriFlow langraph workflow.
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    logger.info(f"[/veriflow/run] New run initiated. run_id: {run_id}, pdf_file: {pdf_file.filename}, context_file: {context_file.filename if context_file else 'N/A'}")
    
    # Create a temporary directory for the run
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{run_id}_"))
    
    # Save the PDF file
    pdf_path = temp_dir / pdf_file.filename
    with open(pdf_path, "wb") as f:
        f.write(await pdf_file.read())
        
    # Create a temporary directory for the repo
    repo_path = temp_dir / "repo"
    repo_path.mkdir()

    # Save the context file if it exists
    if context_file:
        # We assume the context file is a zip file containing the repo
        context_zip_path = temp_dir / context_file.filename
        with open(context_zip_path, "wb") as f:
            f.write(await context_file.read())
        
        # Unzip the context file
        with zipfile.ZipFile(context_zip_path, 'r') as zip_ref:
            zip_ref.extractall(repo_path)

    background_tasks.add_task(
        veriflow_service.run_workflow,
        run_id=run_id,
        pdf_path=pdf_path,
        repo_path=repo_path,
        stream_callback=manager.broadcast,
        temp_dir=temp_dir
    )
    
    return RunResponse(
        run_id=run_id,
        status="queued",
        message="VeriFlow workflow execution has been queued.",
    )

@router.get("/veriflow/results/{run_id}")
def get_veriflow_results(run_id: str):
    logger.info(f"[/veriflow/results/{run_id}] Fetching results for run_id: {run_id}")
    """
    Retrieve the complete results of a VeriFlow run.
    """
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run not found.")

    results = {"run_id": run_id, "scholar": None, "engineer": None}
    
    scholar_path = session.get("scholar_isa_json_path")
    if scholar_path and Path(scholar_path).exists():
        try:
            with open(scholar_path, "r") as f:
                results["scholar"] = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding scholar ISA JSON for run_id {run_id} at {scholar_path}")
            results["scholar"] = {"error": "Failed to decode scholar ISA JSON"}

    engineer_path = session.get("engineer_cwl_path")
    if engineer_path and Path(engineer_path).exists():
        try:
            with open(engineer_path, "r") as f:
                engineer_data = json.load(f)
                results["engineer"] = {
                    "graph": engineer_data.get("graph", {"nodes": [], "edges": []}),
                    "validation_report": engineer_data.get("validation_report", {})
                }
        except json.JSONDecodeError:
            logger.error(f"Error decoding engineer CWL JSON for run_id {run_id} at {engineer_path}")
            results["engineer"] = {"graph": {"nodes": [], "edges": []}, "validation_report": {"error": "Failed to decode engineer CWL JSON"}}
    else:
        logger.warning(f"Engineer CWL path not found or does not exist for run_id {run_id}")
        results["engineer"] = {"graph": {"nodes": [], "edges": []}, "validation_report": {}}

    logger.info(f"[/veriflow/results/{run_id}] Returning results: {json.dumps(results, indent=2)}")
    return results

@router.get("/veriflow/health")
async def health_check():
    """
    Health check endpoint for the VeriFlow router.
    """
    return {"status": "ok"}

@router.websocket("/ws/veriflow/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await manager.connect(websocket, run_id)
    
    # Check if the workflow is already complete
    session = database_service.get_agent_session(run_id)
    if session and session.get("workflow_complete"):
        # If so, immediately notify the client so it can fetch the results
        await websocket.send_json({"type": "workflow_complete", "data": {"run_id": run_id}})

    try:
        while True:
            # Keep the connection alive to receive subsequent messages if the workflow wasn't complete
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
