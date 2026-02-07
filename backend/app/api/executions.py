"""
VeriFlow API - Executions Router
Handles workflow execution and status tracking.
Per PLAN.md Stage 5 and SPEC.md Sections 5.4, 5.5, and 7

Updated for Stage 5: Integrated with execution engine for real CWL→Airflow execution
"""

import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Response

from app.models.execution import (
    ExecutionStatus,
    LogLevel,
    NodeExecutionStatus,
    LogEntry,
    ExecutionConfig,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatusResponse,
    ResultFile,
    ExecutionResultsResponse,
    NodeStatusMessage,
    LogEntryMessage,
    ExecutionCompleteMessage,
)
from app.services.database import db_service
from app.services.minio_client import minio_service
from app.services.export import sds_exporter

# Stage 5: Import execution engine
try:
    from app.services.execution_engine import execution_engine
    from app.services.cwl_parser import cwl_parser
    EXECUTION_ENGINE_AVAILABLE = True
except ImportError:
    EXECUTION_ENGINE_AVAILABLE = False
    execution_engine = None
    cwl_parser = None

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory execution storage
_executions: Dict[str, Dict[str, Any]] = {}

# In-memory workflow/CWL cache (from workflow assembly)
_workflow_cwl_cache: Dict[str, str] = {}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, execution_id: str):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
        self.active_connections[execution_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, execution_id: str):
        if execution_id in self.active_connections:
            if websocket in self.active_connections[execution_id]:
                self.active_connections[execution_id].remove(websocket)
    
    async def broadcast(self, message: dict, execution_id: str):
        if execution_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[execution_id].remove(conn)


manager = ConnectionManager()


def set_workflow_cwl(workflow_id: str, cwl_content: str):
    """Store CWL content for a workflow (called from workflows API)."""
    _workflow_cwl_cache[workflow_id] = cwl_content


def get_workflow_cwl(workflow_id: str) -> Optional[str]:
    """Get stored CWL content for a workflow."""
    return _workflow_cwl_cache.get(workflow_id)


async def _broadcast_status_update(exec_data: Dict[str, Any]):
    """Callback to broadcast execution status updates via WebSocket."""
    execution_id = exec_data.get("execution_id")
    if not execution_id:
        return
    
    # Broadcast node status updates
    for node_id, node_status in exec_data.get("node_statuses", {}).items():
        status = node_status.get("status", "pending")
        progress = node_status.get("progress", 0)
        
        await manager.broadcast(
            {
                "type": "node_status",
                "timestamp": datetime.utcnow().isoformat(),
                "execution_id": execution_id,
                "node_id": node_id,
                "status": status,
                "progress": progress,
            },
            execution_id,
        )
    
    # Broadcast overall progress
    overall_progress = exec_data.get("overall_progress", 0)
    exec_status = exec_data.get("status")
    
    if exec_status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
        await manager.broadcast(
            {
                "type": "execution_complete",
                "timestamp": datetime.utcnow().isoformat(),
                "execution_id": execution_id,
                "status": exec_status.value if hasattr(exec_status, 'value') else exec_status,
            },
            execution_id,
        )
    
    # Broadcast recent logs
    logs = exec_data.get("logs", [])
    if logs:
        recent_log = logs[-1]
        await manager.broadcast(
            {
                "type": "log",
                "timestamp": recent_log.get("timestamp", datetime.utcnow().isoformat()),
                "level": recent_log.get("level", "INFO"),
                "message": recent_log.get("message", ""),
                "node_id": recent_log.get("node_id"),
            },
            execution_id,
        )


@router.post("/executions", response_model=ExecutionResponse, status_code=202)
async def run_workflow(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """
    Trigger workflow execution via Airflow.
    
    Per SPEC.md Section 5.4:
    - Parses CWL workflow (Stage 5)
    - Generates Airflow DAG (Stage 5)
    - Triggers execution via Airflow API (Stage 5)
    - Returns execution_id for status polling
    """
    config = request.config or ExecutionConfig()
    config_dict = config.model_dump()
    
    # Check if execution engine is available
    if EXECUTION_ENGINE_AVAILABLE and execution_engine:
        # Stage 5: Use real execution engine
        
        # Get CWL content for workflow
        cwl_content = get_workflow_cwl(request.workflow_id)
        
        if not cwl_content:
            # Generate a sample CWL workflow for demo
            cwl_content = _generate_sample_cwl(request.workflow_id)
        
        # Prepare execution
        prep_result = await execution_engine.prepare_execution(
            cwl_content=cwl_content,
            workflow_id=request.workflow_id,
            config=config_dict,
        )
        
        if not prep_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=prep_result.get("error", "Failed to prepare execution"),
            )
        
        execution_id = prep_result["execution_id"]
        dag_id = prep_result["dag_id"]
        
        # Store in local cache for status queries
        _executions[execution_id] = {
            "execution_id": execution_id,
            "workflow_id": request.workflow_id,
            "dag_id": dag_id,
            "status": ExecutionStatus.QUEUED,
            "overall_progress": 0,
            "config": config_dict,
            "node_statuses": {},
            "logs": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Start execution in background
        background_tasks.add_task(
            _start_execution_task,
            execution_id,
        )
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=ExecutionStatus.QUEUED,
            dag_id=dag_id,
        )
    
    else:
        # Fallback: Stage 2 mock implementation
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        dag_id = f"veriflow_{request.workflow_id}_{execution_id}"
        
        _executions[execution_id] = {
            "execution_id": execution_id,
            "workflow_id": request.workflow_id,
            "dag_id": dag_id,
            "status": ExecutionStatus.QUEUED,
            "overall_progress": 0,
            "config": config_dict,
            "node_statuses": {},
            "logs": [
                LogEntry(
                    level=LogLevel.INFO,
                    message=f"Execution queued for workflow {request.workflow_id}",
                ).model_dump(),
            ],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Start mock execution in background
        background_tasks.add_task(
            _run_mock_execution,
            execution_id,
        )
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=ExecutionStatus.QUEUED,
            dag_id=dag_id,
        )


async def _start_execution_task(execution_id: str):
    """Background task to start execution via engine."""
    try:
        result = await execution_engine.start_execution(
            execution_id=execution_id,
            status_callback=_sync_execution_status,
        )
        
        if not result.get("success"):
            logger.error(f"Execution start failed: {result.get('error')}")
            if execution_id in _executions:
                _executions[execution_id]["status"] = ExecutionStatus.FAILED
                _executions[execution_id]["error"] = result.get("error")
    except Exception as e:
        logger.error(f"Execution task error: {e}")
        if execution_id in _executions:
            _executions[execution_id]["status"] = ExecutionStatus.FAILED
            _executions[execution_id]["error"] = str(e)


async def _sync_execution_status(exec_data: Dict[str, Any]):
    """Sync execution status from engine to local cache and broadcast."""
    execution_id = exec_data.get("execution_id")
    if execution_id and execution_id in _executions:
        # Update local cache
        _executions[execution_id].update({
            "status": exec_data.get("status", ExecutionStatus.RUNNING),
            "overall_progress": exec_data.get("overall_progress", 0),
            "node_statuses": exec_data.get("node_statuses", {}),
            "logs": exec_data.get("logs", []),
            "results": exec_data.get("results"),
            "provenance": exec_data.get("provenance"),
            "updated_at": datetime.utcnow().isoformat(),
        })
        
        # Broadcast updates
        await _broadcast_status_update(_executions[execution_id])


async def _run_mock_execution(execution_id: str):
    """Run mock execution for demo when execution engine not available."""
    if execution_id not in _executions:
        return
    
    exec_data = _executions[execution_id]
    
    # Simulate startup delay
    await asyncio.sleep(1)
    
    exec_data["status"] = ExecutionStatus.RUNNING
    exec_data["logs"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "message": "Starting workflow execution (simulation mode)",
    })
    await _broadcast_status_update(exec_data)
    
    # Simulate step execution
    mock_steps = ["preprocessing", "segmentation", "postprocessing"]
    
    for i, step in enumerate(mock_steps):
        # Mark step as running
        exec_data["node_statuses"][step] = {
            "status": "running",
            "progress": 0,
        }
        exec_data["logs"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Starting step: {step}",
            "node_id": step,
        })
        await _broadcast_status_update(exec_data)
        
        # Simulate progress
        for progress in range(0, 101, 25):
            await asyncio.sleep(0.5)
            exec_data["node_statuses"][step]["progress"] = progress
            await _broadcast_status_update(exec_data)
        
        # Mark step complete
        exec_data["node_statuses"][step] = {
            "status": "completed",
            "progress": 100,
        }
        exec_data["overall_progress"] = int(((i + 1) / len(mock_steps)) * 100)
        exec_data["logs"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Completed step: {step}",
            "node_id": step,
        })
        await _broadcast_status_update(exec_data)
    
    # Mark execution complete
    exec_data["status"] = ExecutionStatus.COMPLETED
    exec_data["completed_at"] = datetime.utcnow().isoformat()
    exec_data["logs"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "message": "Workflow execution completed successfully",
    })
    await _broadcast_status_update(exec_data)


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get execution status and node-level progress.
    
    Per SPEC.md Section 5.4:
    - Returns overall progress and per-node status
    - Includes recent log entries
    """
    # Check execution engine first
    if EXECUTION_ENGINE_AVAILABLE and execution_engine:
        engine_status = execution_engine.get_execution_status(execution_id)
        if engine_status:
            return ExecutionStatusResponse(
                execution_id=execution_id,
                status=engine_status.get("status", ExecutionStatus.RUNNING),
                overall_progress=engine_status.get("overall_progress", 0),
                nodes={
                    node_id: NodeExecutionStatus(
                        status=status.get("status", "pending"),
                        progress=status.get("progress", 0),
                    )
                    for node_id, status in engine_status.get("node_statuses", {}).items()
                },
                logs=[
                    LogEntry(**log) if isinstance(log, dict) else log
                    for log in engine_status.get("logs", [])[-20:]
                ],
            )
    
    # Fallback to local cache
    if execution_id not in _executions:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    exec_data = _executions[execution_id]
    
    return ExecutionStatusResponse(
        execution_id=execution_id,
        status=exec_data["status"],
        overall_progress=exec_data.get("overall_progress", 0),
        nodes={
            node_id: NodeExecutionStatus(
                status=status.get("status", "pending"),
                progress=status.get("progress", 0),
            )
            for node_id, status in exec_data.get("node_statuses", {}).items()
        },
        logs=[
            LogEntry(**log) if isinstance(log, dict) else log
            for log in exec_data.get("logs", [])[-20:]
        ],
    )


@router.get("/executions/{execution_id}/results", response_model=ExecutionResultsResponse)
async def get_execution_results(execution_id: str, node_id: Optional[str] = None):
    """
    Get result files from execution.
    
    Per SPEC.md Section 5.4:
    - Lists output files with presigned download URLs
    - Optionally filtered by node_id
    """
    exec_data = None
    
    # Check execution engine first
    if EXECUTION_ENGINE_AVAILABLE and execution_engine:
        exec_data = execution_engine.get_execution_status(execution_id)
    
    # Fallback to local cache
    if not exec_data and execution_id in _executions:
        exec_data = _executions[execution_id]
    
    if not exec_data:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Get results from execution data or use mock
    results = exec_data.get("results", [])
    
    if not results:
        return ExecutionResultsResponse(
            execution_id=execution_id,
            files=[],
        )
    
    # Convert to ResultFile objects
    files = []
    for result in results:
        if node_id and result.get("node_id") != node_id:
            continue
        
        file = ResultFile(
            path=result.get("path", ""),
            node_id=result.get("node_id"),
            size=result.get("size", 0),
            mime_type=result.get("mime_type", "application/octet-stream"),
        )
        
        # Add presigned URL
        try:
            file.download_url = minio_service.get_presigned_download_url(
                bucket=minio_service.PROCESS_BUCKET,
                object_name=f"{execution_id}/{file.path}",
            )
        except Exception:
            file.download_url = f"http://localhost:9000/{minio_service.PROCESS_BUCKET}/{execution_id}/{file.path}"
        
        files.append(file)
    
    return ExecutionResultsResponse(
        execution_id=execution_id,
        files=files,
    )


@router.get("/executions/{execution_id}/provenance")
async def get_execution_provenance(execution_id: str):
    """
    Get provenance information for an execution.
    
    Per SPEC.md Section 8.1:
    - Returns wasDerivedFrom relationships
    - Links inputs to outputs
    """
    exec_data = None
    
    # Check execution engine first
    if EXECUTION_ENGINE_AVAILABLE and execution_engine:
        exec_data = execution_engine.get_execution_status(execution_id)
    
    # Fallback to local cache
    if not exec_data and execution_id in _executions:
        exec_data = _executions[execution_id]
    
    if not exec_data:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    provenance = exec_data.get("provenance", {})
    
    if not provenance:
        # Generate basic provenance
        provenance = {
            "execution_id": execution_id,
            "workflow_id": exec_data.get("workflow_id"),
            "generated_at": datetime.utcnow().isoformat(),
            "entities": {
                "input": {
                    "type": "measurements",
                    "path": "measurements/mama-mia/primary/",
                },
                "output": {
                    "type": "process",
                    "path": f"process/{execution_id}/derivative/",
                    "wasDerivedFrom": "input",
                },
            },
        }
    
    return provenance


@router.get("/executions/{execution_id}/export")
async def export_execution(execution_id: str):
    """
    Export execution results as SDS-compliant ZIP.
    
    Per PLAN.md Stage 6 and SPEC.md Section 8.3:
    - Generates ZIP with manifest.xlsx, dataset_description.json
    - Includes provenance.json with wasDerivedFrom
    - Returns downloadable ZIP file
    """
    exec_data = None
    
    # Check execution engine first
    if EXECUTION_ENGINE_AVAILABLE and execution_engine:
        exec_data = execution_engine.get_execution_status(execution_id)
    
    # Fallback to local cache
    if not exec_data and execution_id in _executions:
        exec_data = _executions[execution_id]
    
    if not exec_data:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Check if execution is complete
    status = exec_data.get("status")
    if hasattr(status, 'value'):
        status = status.value
    
    if status not in ["completed", "success", "COMPLETED", "SUCCESS"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export incomplete execution. Current status: {status}"
        )
    
    workflow_id = exec_data.get("workflow_id", "unknown")
    
    # Prepare inputs
    inputs = [
        {
            "id": "input_measurements",
            "path": "measurements/mama-mia/primary/",
            "format": "application/dicom",
        }
    ]
    
    # Get outputs from execution data or use mock
    results = exec_data.get("results", [])
    if not results:
        results = [
            {
                "id": "output_segmentation",
                "path": "derivative/sub-001/tumor_mask.nii.gz",
                "node_id": "segmentation",
                "format": "application/x-nifti",
                "type": "segmentation",
                "description": "Tumor segmentation mask",
            },
        ]
    
    outputs = []
    for result in results:
        outputs.append({
            "id": result.get("id", f"output_{len(outputs)}"),
            "path": result.get("path", "unknown"),
            "node_id": result.get("node_id"),
            "format": result.get("mime_type", result.get("format", "application/octet-stream")),
            "type": result.get("type", "output"),
            "description": result.get("description", "Output file"),
        })
    
    # Get node statuses
    node_statuses = exec_data.get("node_statuses", {})
    
    # For MVP, we use mock file data since actual files may not exist
    output_file_data = {}
    for out in outputs:
        # Try to get actual file from MinIO
        path = out.get("path", "")
        try:
            file_content = minio_service.download_file(
                bucket=minio_service.PROCESS_BUCKET,
                object_name=f"{execution_id}/{path}",
            )
            output_file_data[path] = file_content
        except Exception:
            # Create placeholder file for demo
            output_file_data[path] = f"[Placeholder for {path}]".encode()
    
    # Generate ZIP
    try:
        zip_bytes = sds_exporter.create_export_zip(
            execution_id=execution_id,
            workflow_id=workflow_id,
            title=f"VeriFlow Execution {execution_id}",
            description="Results from VeriFlow workflow execution",
            inputs=inputs,
            outputs=outputs,
            node_statuses=node_statuses,
            output_file_data=output_file_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate export: {str(e)}"
        )
    
    # Return as downloadable file
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=veriflow_export_{execution_id}.zip"
        }
    )


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, execution_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time log streaming.
    
    Per SPEC.md Section 5.5:
    - Streams NodeStatusMessage, LogEntryMessage, ExecutionCompleteMessage
    - Polls Airflow for real status updates (Stage 5)
    """
    exec_id = execution_id or "default"
    await manager.connect(websocket, exec_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json(
            LogEntryMessage(
                level=LogLevel.INFO,
                message="Connected to execution log stream",
            ).model_dump()
        )
        
        # Send current status if execution exists
        if exec_id in _executions:
            exec_data = _executions[exec_id]
            await websocket.send_json({
                "type": "status",
                "execution_id": exec_id,
                "status": exec_data.get("status", ExecutionStatus.QUEUED).value 
                    if hasattr(exec_data.get("status"), 'value') 
                    else exec_data.get("status", "queued"),
                "progress": exec_data.get("overall_progress", 0),
            })
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                else:
                    # Echo received messages (for debugging)
                    await websocket.send_json({"type": "echo", "data": data})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket, exec_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, exec_id)


def _generate_sample_cwl(workflow_id: str) -> str:
    """Generate a sample CWL workflow for demo purposes."""
    return f"""
cwlVersion: v1.3
class: Workflow
id: {workflow_id}
label: VeriFlow Sample Workflow
doc: Auto-generated workflow for demo

inputs:
  input_data:
    type: Directory
    doc: Input measurement data

outputs:
  output_data:
    type: Directory
    outputSource: postprocessing/output_dir

steps:
  preprocessing:
    run: tools/preprocessing.cwl
    in:
      input_dir: input_data
    out: [output_dir]

  segmentation:
    run: tools/segmentation.cwl
    in:
      input_dir: preprocessing/output_dir
    out: [output_dir]

  postprocessing:
    run: tools/postprocessing.cwl
    in:
      input_dir: segmentation/output_dir
    out: [output_dir]
"""
