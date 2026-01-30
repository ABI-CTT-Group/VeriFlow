"""
VeriFlow - Workflow Pydantic Models
Per SPEC.md Section 3.5
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class NodeType(str, Enum):
    MEASUREMENT = "measurement"
    TOOL = "tool"
    MODEL = "model"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Position(BaseModel):
    """Node position in the canvas."""
    x: float
    y: float


class PortDefinition(BaseModel):
    """Input/Output port definition for nodes."""
    id: str
    label: str
    type: str  # MIME type or CWL type


class NodeData(BaseModel):
    """Data payload for a VueFlow node."""
    label: str
    status: Optional[NodeStatus] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)
    source_id: Optional[str] = None
    inputs: List[PortDefinition] = Field(default_factory=list)
    outputs: List[PortDefinition] = Field(default_factory=list)
    # Additional metadata
    description: Optional[str] = None
    docker_image: Optional[str] = None
    cwl_path: Optional[str] = None


class VueFlowNode(BaseModel):
    """A node in the VueFlow graph."""
    id: str
    type: NodeType
    position: Position
    data: NodeData


class VueFlowEdge(BaseModel):
    """An edge connecting two nodes in the VueFlow graph."""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = Field(None, alias="sourceHandle")
    target_handle: Optional[str] = Field(None, alias="targetHandle")
    
    class Config:
        populate_by_name = True


class WorkflowGraph(BaseModel):
    """Complete workflow graph with nodes and edges."""
    nodes: List[VueFlowNode] = Field(default_factory=list)
    edges: List[VueFlowEdge] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Complete workflow state including metadata."""
    workflow_id: str
    upload_id: Optional[str] = None
    assay_id: Optional[str] = None
    graph: WorkflowGraph
    cwl_path: Optional[str] = None
    status: str = "draft"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AssembleRequest(BaseModel):
    """Request to assemble a workflow from an assay."""
    assay_id: str
    upload_id: Optional[str] = None


class AssembleResponse(BaseModel):
    """Response from workflow assembly."""
    workflow_id: str
    cwl_path: Optional[str] = None
    graph: WorkflowGraph
    validation: Optional[dict] = None


class SaveWorkflowRequest(BaseModel):
    """Request to save workflow graph state."""
    graph: WorkflowGraph
