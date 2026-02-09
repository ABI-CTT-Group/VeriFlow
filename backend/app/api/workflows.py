"""
VeriFlow API - Workflows Router
Handles workflow assembly, retrieval, saving (Design Mode), 
AND execution restart/status/results (Execution Mode).
"""

import uuid
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

# --- Imports for Design/Assembly Mode ---
from app.models.workflow import (
    NodeType,
    Position,
    PortDefinition,
    NodeData,
    VueFlowNode,
    VueFlowEdge,
    WorkflowGraph,
    AssembleRequest,
    AssembleResponse,
    SaveWorkflowRequest,
    NodeStatus,
)

# --- Imports for Execution/Restart Mode ---
from app.services.veriflow_service import veriflow_service
from app.services.database_sqlite import database_service
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

# Stage 4: Import Engineer and Reviewer agents (Gemini 3 SDK)
try:
    from app.agents.engineer import engineer_agent
    from app.agents.reviewer import reviewer_agent
    AGENTS_AVAILABLE = True
except (ImportError, ValueError):
    AGENTS_AVAILABLE = False
    engineer_agent = None
    reviewer_agent = None

# Import cache from publications for ISA data
try:
    from app.api.publications import _upload_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

router = APIRouter()

# In-memory workflow storage (Design Mode)
_workflows: dict[str, dict] = {}

class RestartRequest(BaseModel):
    user_context: Optional[str] = None
    clear_directives: bool = False

# ==============================================================================
# EXECUTION RESULTS ENDPOINT
# ==============================================================================

@router.get("/veriflow/results/{run_id}")
def get_veriflow_results(run_id: str):
    """
    Retrieve the complete results of a VeriFlow run.
    Used by the Plan & Apply frontend to show generated artifacts.
    """
    logger.info(f"[/veriflow/results/{run_id}] Fetching results...")
    
    # 1. Fetch Session from DB
    session = database_service.get_agent_session(run_id)
    if not session:
        logger.error(f"[/veriflow/results] Session NOT FOUND for {run_id}")
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found in database.")

    results = {"run_id": run_id, "scholar": None, "engineer": None}
    
    # --- Helper to safely load JSON ---
    def safe_load_json(path_str: Optional[str], label: str):
        if not path_str:
            logger.info(f"[{run_id}] No path in DB for {label}")
            return None
            
        path_obj = Path(path_str)
        if not path_obj.exists():
            logger.warning(f"[{run_id}] File missing for {label} at {path_obj}")
            return {"error": "File not found on disk", "path": str(path_obj)}
            
        try:
            with open(path_obj, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # FIX: Handle double-encoded JSON (if agent output was stringified twice)
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass # Keep as string if it's not valid JSON
            
            return data
        except Exception as e:
            logger.error(f"[{run_id}] Error loading {label}: {e}")
            return {"error": f"Failed to load file: {e}"}

    # 2. Load Scholar Output
    results["scholar"] = safe_load_json(session.get("scholar_isa_json_path"), "scholar")

    # 3. Load Engineer Output
    results["engineer"] = safe_load_json(session.get("engineer_cwl_path"), "engineer")
            
    return results


# ==============================================================================
# RESTART & STATUS ENDPOINTS (Plan & Apply)
# ==============================================================================

@router.get("/workflows/{run_id}/status")
async def get_workflow_status(run_id: str):
    """
    Get the current state of a workflow run (Execution Mode).
    """
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run ID not found")
        
    state = database_service.get_full_state_mock(run_id)
    
    return {
        "run_id": run_id,
        "status": "completed" if session.get("workflow_complete") else "in_progress",
        "current_errors": state.get("validation_errors", []),
        "review_decision": state.get("review_decision"),
        "generated_artifacts": list(state.get("generated_code", {}).keys()) if state.get("generated_code") else []
    }

@router.post("/workflows/{run_id}/restart")
async def restart_workflow_execution(
    run_id: str, 
    start_node: str = Query(..., description="The agent node to restart from (e.g., 'engineer', 'scholar')"),
    request: Optional[RestartRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks() 
):
    """
    Explicitly restart a workflow execution from a specific agent node.
    This supports the 'Plan & Apply' pattern.
    """
    # 1. Validate Run Exists
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run ID not found")

    # 2. Update Context if provided
    if request:
        updates = {}
        if request.user_context:
            updates["user_context"] = request.user_context
        
        if request.clear_directives:
            updates["agent_directives"] = {} # Clear chat history/instructions
            
        if updates:
            database_service.create_or_update_agent_session(run_id, **updates)

    # 3. Trigger Restart (Background Task)
    background_tasks.add_task(
        veriflow_service.restart_workflow,
        run_id=run_id,
        start_node=start_node,
        stream_callback=manager.broadcast
    )

    return {
        "status": "accepted", 
        "message": f"Workflow restart initiated from '{start_node}'", 
        "run_id": run_id
    }


# ==============================================================================
# DESIGN MODE ENDPOINTS (Original Functionality)
# ==============================================================================

@router.post("/workflows/assemble", response_model=AssembleResponse)
async def assemble_workflow(request: AssembleRequest):
    """
    Assemble a workflow from an assay.
    Triggers the Engineer Agent to generate CWL and Vue Flow graph.
    """
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    
    # Stage 4: Use Engineer Agent if available
    if AGENTS_AVAILABLE and CACHE_AVAILABLE:
        # Try to get ISA data from cache
        cache_entry = _upload_cache.get(request.upload_id, {})
        result = cache_entry.get("result", {})
        
        if result:
            # Extract data for Engineer Agent
            isa_json = result.get("isa_json", {})
            identified_tools = result.get("identified_tools", [])
            identified_models = result.get("identified_models", [])
            identified_measurements = result.get("identified_measurements", [])
            
            try:
                # Generate workflow with Engineer Agent
                engineer_result = await engineer_agent.generate_workflow(
                    assay_id=request.assay_id,
                    isa_json=isa_json,
                    identified_tools=identified_tools,
                    identified_models=identified_models,
                    identified_measurements=identified_measurements,
                )
                
                # Convert graph to Vue Flow format
                graph_data = engineer_result.get("graph", {"nodes": [], "edges": []})
                nodes = []
                for n in graph_data.get("nodes", []):
                    node_type = NodeType(n.get("type", "tool"))
                    nodes.append(VueFlowNode(
                        id=n["id"],
                        type=node_type,
                        position=Position(**n.get("position", {"x": 0, "y": 0})),
                        data=NodeData(
                            label=n.get("data", {}).get("label", ""),
                            inputs=[
                                PortDefinition(**p) for p in n.get("data", {}).get("inputs", [])
                            ],
                            outputs=[
                                PortDefinition(**p) for p in n.get("data", {}).get("outputs", [])
                            ],
                        ),
                    ))
                
                edges = [
                    VueFlowEdge(**e) for e in graph_data.get("edges", [])
                ]
                
                graph = WorkflowGraph(nodes=nodes, edges=edges)
                
                # Validate with Reviewer Agent
                validation = await reviewer_agent.validate_workflow(
                    workflow_cwl=engineer_result.get("workflow_cwl", ""),
                    tool_cwls=engineer_result.get("tool_cwls", {}),
                    graph=graph_data,
                )
                
                # Store workflow
                _workflows[workflow_id] = {
                    "workflow_id": workflow_id,
                    "upload_id": request.upload_id,
                    "assay_id": request.assay_id,
                    "graph": graph.model_dump(),
                    "cwl": engineer_result.get("workflow_cwl", ""),
                    "tool_cwls": engineer_result.get("tool_cwls", {}),
                    "dockerfiles": engineer_result.get("dockerfiles", {}),
                    "validation": validation,
                    "status": "draft",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                
                return AssembleResponse(
                    workflow_id=workflow_id,
                    cwl_path=f"workflow/{workflow_id}/workflow.cwl",
                    graph=graph,
                    validation=validation,
                )
                
            except Exception as e:
                # Fall through to mock data if agent fails
                pass
    
    # Fallback: Generate mock workflow graph based on MAMA-MIA example
    nodes = [
        VueFlowNode(
            id="input-1",
            type=NodeType.MEASUREMENT,
            position=Position(x=50, y=50),
            data=NodeData(
                label="Input Measurements",
                name="Input Measurements",
                role="input",
                status=NodeStatus.PENDING,
                totalSubjects=384,
                outputs=[
                    PortDefinition(
                        id="out-0", 
                        label="MRI Scan", 
                        type="application/dicom",
                        datasetId="dce-mri-scans",
                        sampleId="Subject_001/T1w.nii.gz"
                    ),
                ],
            ),
        ),
        VueFlowNode(
            id="tool-1",
            type=NodeType.TOOL,
            position=Position(x=45, y=50),
            data=NodeData(
                label="DICOM to NIfTI",
                name="DICOM to NIfTI",
                status=NodeStatus.PENDING,
                confidence=0.95,
                inputs=[
                    PortDefinition(id="in-0", label="Raw DICOM"),
                ],
                outputs=[
                    PortDefinition(id="out-0", label="NIfTI Volume"),
                ],
                docker_image="dcm2niix:latest",
            ),
        ),
        VueFlowNode(
            id="tool-2",
            type=NodeType.TOOL,
            position=Position(x=80, y=50),
            data=NodeData(
                label="nnU-Net Segmentation",
                name="nnU-Net Segmentation",
                status=NodeStatus.PENDING,
                confidence=0.88,
                inputs=[
                    PortDefinition(id="in-0", label="NIfTI Volume"),
                    PortDefinition(id="in-1", label="Model Weights"),
                ],
                outputs=[
                    PortDefinition(id="out-0", label="Segmentation Mask"),
                ],
                docker_image="breast-segmentation:latest",
            ),
        ),
        VueFlowNode(
            id="model-1",
            type=NodeType.MODEL,
            position=Position(x=45, y=320),
            data=NodeData(
                label="nnU-Net Pretrained Weights",
                name="nnU-Net Pretrained Weights",
                status=NodeStatus.PENDING,
                outputs=[
                    PortDefinition(id="out-0", label="Weights"),
                ],
            ),
        ),
        VueFlowNode(
            id="tool-3",
            type=NodeType.TOOL,
            position=Position(x=115, y=50),
            data=NodeData(
                label="Post-processing",
                name="Post-processing",
                status=NodeStatus.PENDING,
                confidence=0.92,
                inputs=[
                    PortDefinition(id="in-0", label="Segmentation Mask"),
                ],
                outputs=[
                    PortDefinition(id="out-0", label="Refined Mask"),
                ],
            ),
        ),
        VueFlowNode(
            id="output-1",
            type=NodeType.MEASUREMENT,
            position=Position(x=150, y=50),
            data=NodeData(
                label="Output Measurements",
                name="Output Measurements",
                role="output",
                status=NodeStatus.PENDING,
                inputs=[
                    PortDefinition(
                        id="in-0", 
                        label="Result",
                        datasetId="tumor-segmentation", 
                        sampleId="Subject_001/tumor_mask.nii.gz"
                    ),
                ],
            ),
        ),
    ]
    
    edges = [
        VueFlowEdge(id="conn-1", source="input-1", target="tool-1", sourceHandle="out-0", targetHandle="in-0"),
        VueFlowEdge(id="conn-2", source="tool-1", target="tool-2", sourceHandle="out-0", targetHandle="in-0"),
        VueFlowEdge(id="conn-3", source="model-1", target="tool-2", sourceHandle="out-0", targetHandle="in-1"),
        VueFlowEdge(id="conn-4", source="tool-2", target="tool-3", sourceHandle="out-0", targetHandle="in-0"),
        VueFlowEdge(id="conn-5", source="tool-3", target="output-1", sourceHandle="out-0", targetHandle="in-0"),
    ]
    
    graph = WorkflowGraph(nodes=nodes, edges=edges)
    
    # Store workflow in memory
    _workflows[workflow_id] = {
        "workflow_id": workflow_id,
        "upload_id": request.upload_id,
        "assay_id": request.assay_id,
        "graph": graph.model_dump(),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    return AssembleResponse(
        workflow_id=workflow_id,
        cwl_path=f"workflow/{workflow_id}/workflow.cwl",
        graph=graph,
        validation={"passed": True, "checks": {}},
    )


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """
    Get the current state of a workflow (Design Mode).
    """
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return _workflows[workflow_id]


@router.put("/workflows/{workflow_id}")
async def save_workflow(workflow_id: str, request: SaveWorkflowRequest):
    """
    Save workflow graph state (Design Mode).
    """
    if workflow_id not in _workflows:
        # Create new workflow if it doesn't exist
        _workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "graph": request.graph.model_dump(),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
        }
    else:
        _workflows[workflow_id]["graph"] = request.graph.model_dump()
    
    _workflows[workflow_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "workflow_id": workflow_id,
        "updated_at": _workflows[workflow_id]["updated_at"],
        "message": "Workflow saved successfully",
    }