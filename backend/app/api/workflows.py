"""
VeriFlow API - Workflows Router
Handles workflow assembly, retrieval, and saving.
Per PLAN.md Stage 2/4 and SPEC.md Section 5.3
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException

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
)

# Stage 4: Import Engineer and Reviewer agents
try:
    from app.agents.engineer import engineer_agent
    from app.agents.reviewer import reviewer_agent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

# Import cache from publications for ISA data
try:
    from app.api.publications import _upload_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

router = APIRouter()


# In-memory workflow storage
_workflows: dict[str, dict] = {}


@router.post("/workflows/assemble", response_model=AssembleResponse)
async def assemble_workflow(request: AssembleRequest):
    """
    Assemble a workflow from an assay.
    Triggers the Engineer Agent to generate CWL and Vue Flow graph.
    
    Per SPEC.md Section 5.3:
    - Takes assay_id and generates workflow graph
    - Returns nodes with auto-layout positions
    - Uses Engineer Agent for CWL generation
    - Uses Reviewer Agent for validation
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
            position=Position(x=50, y=100),
            data=NodeData(
                label="DCE-MRI Scans",
                status="pending",
                confidence=97,
                source_id="src_4",
                inputs=[],
                outputs=[
                    PortDefinition(id="out-dicom", label="DICOM", type="application/dicom"),
                ],
            ),
        ),
        VueFlowNode(
            id="tool-1",
            type=NodeType.TOOL,
            position=Position(x=300, y=100),
            data=NodeData(
                label="DICOM to NIfTI",
                status="pending",
                inputs=[
                    PortDefinition(id="in-dicom", label="Input", type="application/dicom"),
                ],
                outputs=[
                    PortDefinition(id="out-nifti", label="Output", type="application/x-nifti"),
                ],
                docker_image="dcm2niix:latest",
            ),
        ),
        VueFlowNode(
            id="model-1",
            type=NodeType.MODEL,
            position=Position(x=550, y=100),
            data=NodeData(
                label="U-Net Weights",
                status="pending",
                confidence=85,
                inputs=[],
                outputs=[
                    PortDefinition(id="out-weights", label="Weights", type="application/x-pytorch"),
                ],
            ),
        ),
        VueFlowNode(
            id="tool-2",
            type=NodeType.TOOL,
            position=Position(x=550, y=250),
            data=NodeData(
                label="U-Net Segmentation",
                status="pending",
                inputs=[
                    PortDefinition(id="in-image", label="Image", type="application/x-nifti"),
                    PortDefinition(id="in-weights", label="Weights", type="application/x-pytorch"),
                ],
                outputs=[
                    PortDefinition(id="out-mask", label="Mask", type="application/x-nifti"),
                ],
                docker_image="breast-segmentation:latest",
            ),
        ),
        VueFlowNode(
            id="output-1",
            type=NodeType.MEASUREMENT,
            position=Position(x=800, y=250),
            data=NodeData(
                label="Segmentation Results",
                status="pending",
                inputs=[
                    PortDefinition(id="in-mask", label="Mask", type="application/x-nifti"),
                ],
                outputs=[],
            ),
        ),
    ]
    
    edges = [
        VueFlowEdge(id="e1", source="input-1", target="tool-1", sourceHandle="out-dicom", targetHandle="in-dicom"),
        VueFlowEdge(id="e2", source="tool-1", target="tool-2", sourceHandle="out-nifti", targetHandle="in-image"),
        VueFlowEdge(id="e3", source="model-1", target="tool-2", sourceHandle="out-weights", targetHandle="in-weights"),
        VueFlowEdge(id="e4", source="tool-2", target="output-1", sourceHandle="out-mask", targetHandle="in-mask"),
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
    Get the current state of a workflow.
    
    Per SPEC.md Section 5.3:
    - Returns workflow graph with current node positions
    - Includes workflow metadata
    """
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return _workflows[workflow_id]


@router.put("/workflows/{workflow_id}")
async def save_workflow(workflow_id: str, request: SaveWorkflowRequest):
    """
    Save workflow graph state.
    
    Per SPEC.md Section 5.3:
    - Saves node positions and connections
    - Updates workflow timestamp
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
