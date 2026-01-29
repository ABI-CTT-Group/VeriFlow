"""
VeriFlow API - Executions Router
Handles workflow execution and status tracking.
Per PLAN.md Stage 2 and SPEC.md Sections 5.4 and 5.5
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

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

router = APIRouter()

# In-memory execution storage (Stage 5 will use database)
_executions: dict[str, dict] = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}
    
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
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.post("/executions", response_model=ExecutionResponse, status_code=202)
async def run_workflow(request: ExecutionRequest):
    """
    Trigger workflow execution via Airflow.
    
    Per SPEC.md Section 5.4:
    - Creates execution record
    - Stage 5 will implement CWL→Airflow DAG conversion
    - Returns execution_id for status polling
    """
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    dag_id = f"veriflow_{request.workflow_id}_{execution_id}"
    
    config = request.config or ExecutionConfig()
    
    # Store execution in memory
    _executions[execution_id] = {
        "execution_id": execution_id,
        "workflow_id": request.workflow_id,
        "dag_id": dag_id,
        "status": ExecutionStatus.QUEUED,
        "overall_progress": 0,
        "config": config.model_dump(),
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
    
    # Try to persist to database
    try:
        await db_service.create_execution(
            workflow_id=request.workflow_id,
            dag_id=dag_id,
            config=config.model_dump(),
        )
    except Exception:
        pass  # Continue with in-memory storage
    
    return ExecutionResponse(
        execution_id=execution_id,
        status=ExecutionStatus.QUEUED,
        dag_id=dag_id,
    )


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get execution status and node-level progress.
    
    Per SPEC.md Section 5.4:
    - Returns overall progress and per-node status
    - Includes recent log entries
    """
    if execution_id not in _executions:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    exec_data = _executions[execution_id]
    
    return ExecutionStatusResponse(
        execution_id=execution_id,
        status=exec_data["status"],
        overall_progress=exec_data["overall_progress"],
        nodes={
            node_id: NodeExecutionStatus(**status)
            for node_id, status in exec_data.get("node_statuses", {}).items()
        },
        logs=[LogEntry(**log) for log in exec_data.get("logs", [])[-20:]],  # Last 20 logs
    )


@router.get("/executions/{execution_id}/results", response_model=ExecutionResultsResponse)
async def get_execution_results(execution_id: str, node_id: Optional[str] = None):
    """
    Get result files from execution.
    
    Per SPEC.md Section 5.4:
    - Lists output files with presigned download URLs
    - Optionally filtered by node_id
    """
    if execution_id not in _executions:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Mock result files for MVP
    # Stage 5 will list actual files from MinIO process bucket
    mock_files = [
        ResultFile(
            path=f"derivative/sub-001/tumor_mask.nii.gz",
            node_id="tool-2",
            size=1048576,
            mime_type="application/x-nifti",
        ),
        ResultFile(
            path=f"derivative/sub-001/segmentation_overlay.png",
            node_id="tool-2",
            size=524288,
            mime_type="image/png",
        ),
    ]
    
    if node_id:
        mock_files = [f for f in mock_files if f.node_id == node_id]
    
    # Add presigned URLs
    for file in mock_files:
        try:
            file.download_url = minio_service.get_presigned_download_url(
                bucket=minio_service.PROCESS_BUCKET,
                object_name=f"{execution_id}/{file.path}",
            )
        except Exception:
            file.download_url = f"http://localhost:9000/{minio_service.PROCESS_BUCKET}/{execution_id}/{file.path}"
    
    return ExecutionResultsResponse(
        execution_id=execution_id,
        files=mock_files,
    )


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, execution_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time log streaming.
    
    Per SPEC.md Section 5.5:
    - Streams NodeStatusMessage, LogEntryMessage, ExecutionCompleteMessage
    - Stage 5 will poll Airflow for real status updates
    """
    exec_id = execution_id or "default"
    await manager.connect(websocket, exec_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json(
            LogEntryMessage(
                level=LogLevel.INFO,
                message=f"Connected to execution log stream",
            ).model_dump()
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo received messages (for debugging)
                await websocket.send_json({"type": "echo", "data": data})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket, exec_id)
    except Exception:
        manager.disconnect(websocket, exec_id)
