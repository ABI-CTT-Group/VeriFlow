"""
VeriFlow API - Workflows Router
Handles workflow assembly, retrieval, saving (Design Mode),
AND execution restart/status (Execution Mode).
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# --- Imports from Original File (Design Mode) ---
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

# --- Imports for New Functionality (Execution Mode) ---
from app.services.veriflow_service import veriflow_service
from app.services.database_sqlite import database_service
from app.services.websocket_manager import manager

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

# --- New Models for Restart Logic ---
class RestartRequest(BaseModel):
    # Optional: Update user context or options on restart
    user_context: Optional[str] = None

    # Optional: Clear previous directives if just retrying
    clear_directives: bool = False


class DynamicAssembleRequest(BaseModel):
    """Request to dynamically assemble a workflow from scholar agent output."""
    run_id: str
    assay_id: str

# ==============================================================================
# EXISTING ENDPOINTS (Design & Assembly)
# ==============================================================================

@router.post("/workflows/mama-mia/assemble", response_model=AssembleResponse)
async def assemble_mama_mia_workflow(request: AssembleRequest):
    """
    Assemble a MAMA-MIA demo workflow (mock data).
    Triggers the Engineer Agent to generate CWL and Vue Flow graph, or falls back to mock.
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
                # Fall through to mock data
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
                status=NodeStatus.COMPLETED,
                totalSubjects=2,
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
            position=Position(x=250, y=50),
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
            position=Position(x=450, y=50),
            data=NodeData(
                label="Run Inference",
                name="Run Inference",
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
            position=Position(x=450, y=200),
            data=NodeData(
                label="nnU-Net Pretrained Weights",
                name="nnU-Net Pretrained Weights",
                status=NodeStatus.COMPLETED,
                outputs=[
                    PortDefinition(id="out-0", label="Weights"),
                ],
            ),
        ),
        VueFlowNode(
            id="output-1",
            type=NodeType.MEASUREMENT,
            position=Position(x=650, y=50),
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
        VueFlowEdge(id="conn-4", source="tool-2", target="output-1", sourceHandle="out-0", targetHandle="in-0"),
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


@router.post("/workflows/assemble", response_model=AssembleResponse)
async def assemble_workflow_from_scholar(request: DynamicAssembleRequest):
    """
    Dynamically assemble a workflow from scholar agent output.
    Reads logs/{run_id}/1_scholar.json, finds the selected assay,
    and converts workflowSteps into VueFlow nodes and edges.
    """
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

    # 1. Read scholar JSON
    scholar_path = Path("logs") / request.run_id / "1_scholar.json"
    if not scholar_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Scholar output not found for run_id: {request.run_id}"
        )

    try:
        with open(scholar_path, "r", encoding="utf-8") as f:
            scholar_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to read scholar output: {e}")

    # 2. Extract assays from scholar output
    study_design = scholar_data.get("final_output", {}).get("studyDesign", {})
    assays = study_design.get("assays", [])

    if not assays:
        raise HTTPException(status_code=404, detail="No assays found in scholar output")

    # 3. Find the selected assay
    selected_assay = None
    for assay in assays:
        if assay.get("id") == request.assay_id:
            selected_assay = assay
            break

    if not selected_assay:
        raise HTTPException(
            status_code=404,
            detail=f"Assay '{request.assay_id}' not found in scholar output"
        )

    workflow_steps = selected_assay.get("workflowSteps", [])
    if not workflow_steps:
        raise HTTPException(
            status_code=400,
            detail=f"Assay '{request.assay_id}' has no workflow steps"
        )

    # 4. Convert workflowSteps to VueFlow nodes and edges
    nodes: List[VueFlowNode] = []
    edges: List[VueFlowEdge] = []

    # Track which output names are produced by which tool node (for edge routing)
    # Maps output_name -> (node_id, port_id)
    output_registry: Dict[str, tuple] = {}

    x_spacing = 200
    current_x = 50

    # --- Input Measurement Node ---
    first_step = workflow_steps[0]
    input_ports = []
    for idx, inp in enumerate(first_step.get("input", [])):
        port_id = f"out-{idx}"
        input_ports.append(
            PortDefinition(
                id=port_id,
                label=inp.get("name", f"Input {idx}"),
                type=inp.get("type", "File"),
            )
        )
        # Register these as available outputs from the input node
        output_registry[inp.get("name", "")] = ("input-1", port_id)

    nodes.append(VueFlowNode(
        id="input-1",
        type=NodeType.MEASUREMENT,
        position=Position(x=current_x, y=50),
        data=NodeData(
            label="Input Data",
            name="Input Data",
            role="input",
            status=NodeStatus.COMPLETED,
            outputs=input_ports,
        ),
    ))
    current_x += x_spacing

    # --- Tool Nodes (one per workflowStep) ---
    for step_idx, step in enumerate(workflow_steps):
        tool_node_id = f"tool-{step_idx + 1}"
        tool_name = step.get("tool", {}).get("name", f"Step {step_idx + 1}")
        description = step.get("description", "")

        # Build input ports
        tool_inputs = []
        for idx, inp in enumerate(step.get("input", [])):
            tool_inputs.append(
                PortDefinition(
                    id=f"in-{idx}",
                    label=inp.get("name", f"Input {idx}"),
                    type=inp.get("type", "File"),
                )
            )

        # Build output ports
        tool_outputs = []
        for idx, out in enumerate(step.get("output", [])):
            port_id = f"out-{idx}"
            tool_outputs.append(
                PortDefinition(
                    id=port_id,
                    label=out.get("name", f"Output {idx}"),
                    type=out.get("type", "File"),
                )
            )
            # Register this output
            output_registry[out.get("name", "")] = (tool_node_id, port_id)

        nodes.append(VueFlowNode(
            id=tool_node_id,
            type=NodeType.TOOL,
            position=Position(x=current_x, y=50),
            data=NodeData(
                label=tool_name,
                name=tool_name,
                description=description,
                status=NodeStatus.PENDING,
                inputs=tool_inputs,
                outputs=tool_outputs,
            ),
        ))

        # Create edges: connect each input to the node that produces it
        for idx, inp in enumerate(step.get("input", [])):
            input_name = inp.get("name", "")
            if input_name in output_registry:
                source_node_id, source_port_id = output_registry[input_name]
                edge_id = f"conn-{tool_node_id}-in-{idx}"
                edges.append(VueFlowEdge(
                    id=edge_id,
                    source=source_node_id,
                    target=tool_node_id,
                    sourceHandle=source_port_id,
                    targetHandle=f"in-{idx}",
                ))

        current_x += x_spacing

    # --- Output Measurement Node ---
    last_step = workflow_steps[-1]
    output_ports = []
    for idx, out in enumerate(last_step.get("output", [])):
        output_ports.append(
            PortDefinition(
                id=f"in-{idx}",
                label=out.get("name", f"Output {idx}"),
                type=out.get("type", "File"),
            )
        )

    output_node_id = "output-1"
    nodes.append(VueFlowNode(
        id=output_node_id,
        type=NodeType.MEASUREMENT,
        position=Position(x=current_x, y=50),
        data=NodeData(
            label="Output Data",
            name="Output Data",
            role="output",
            status=NodeStatus.PENDING,
            inputs=output_ports,
        ),
    ))

    # Connect last tool to output node
    last_tool_id = f"tool-{len(workflow_steps)}"
    for idx, out in enumerate(last_step.get("output", [])):
        edges.append(VueFlowEdge(
            id=f"conn-output-in-{idx}",
            source=last_tool_id,
            target=output_node_id,
            sourceHandle=f"out-{idx}",
            targetHandle=f"in-{idx}",
        ))

    graph = WorkflowGraph(nodes=nodes, edges=edges)

    # Store workflow in memory
    _workflows[workflow_id] = {
        "workflow_id": workflow_id,
        "run_id": request.run_id,
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


# ==============================================================================
# NEW ENDPOINTS (Execution & Restart)
# ==============================================================================

@router.get("/workflows/{run_id}/status")
async def get_workflow_status(run_id: str):
    """
    Get the current state of a workflow run (Execution Mode).
    Retrieved from the SQLite database.
    """
    session = database_service.get_agent_session(run_id)
    if not session:
        raise HTTPException(status_code=404, detail="Run ID not found")
        
    # Reconstruct a summary of the state
    state = database_service.get_full_state_mock(run_id)
    
    return {
        "run_id": run_id,
        "status": "completed" if session.get("workflow_complete") else "in_progress",
        "current_errors": state.get("validation_errors", []),
        "review_decision": state.get("review_decision"),
        "generated_artifacts": list(state.get("generated_code", {}).keys())
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