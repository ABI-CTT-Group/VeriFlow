from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --- Helper Models ---

class KeyValue(BaseModel):
    """Represents a dynamic key-value pair for metadata."""
    key: str = Field(..., description="The parameter name.")
    value: str = Field(..., description="The parameter value.")

class Metric(BaseModel):
    """Represents a confidence score or measurement."""
    name: str = Field(..., description="Name of the metric (e.g., 'sample_size').")
    score: float = Field(..., description="Confidence score between 0.0 and 1.0.")

class Tool(BaseModel):
    """Represents an identified software or hardware tool."""
    name: str = Field(..., description="Name of the tool.")
    description: str = Field(..., description="Brief context of how it is used.")

# --- Scholar Agent Schema ---

class Investigation(BaseModel):
    """Structured ISA investigation data."""
    title: str = Field(..., description="The title of the publication or investigation.")
    description: str = Field(..., description="A concise summary of the study.")
    study_factors: List[str] = Field(default_factory=list, description="List of experimental factors (e.g., 'Time', 'Dose').")
    metadata: List[KeyValue] = Field(default_factory=list, description="Additional metadata fields.")

class AnalysisResult(BaseModel):
    """Top-level response structure for Scholar Agent."""

    # The "Thinking" Field
    thought_process: str = Field(..., description="Step-by-step reasoning trace used to analyze the document.")

    # Core Data
    investigation: Investigation = Field(..., description="The extracted ISA investigation details.")

    # Replaced Dict with List[Metric] to satisfy Schema requirements
    confidence_scores: List[Metric] = Field(default_factory=list, description="Confidence scores for extractions.")

    # Structured Tools instead of just strings
    identified_tools: List[Tool] = Field(default_factory=list, description="Software or hardware tools mentioned.")

    identified_models: List[str] = Field(default_factory=list, description="Computational models mentioned.")
    identified_measurements: List[str] = Field(default_factory=list, description="Measurements or assays found.")

# --- Engineer Agent Schema ---

class PortDefinition(BaseModel):
    """Input/output port for a workflow node."""
    id: str = Field(..., description="Unique port identifier.")
    label: str = Field(..., description="Display label for the port.")
    type: str = Field(default="application/octet-stream", description="MIME type of the port.")

class GraphNode(BaseModel):
    """A node in the workflow graph."""
    id: str = Field(..., description="Unique node identifier.")
    type: str = Field(..., description="Node type: measurement, tool, or model.")
    position_x: float = Field(default=0, description="X position for layout.")
    position_y: float = Field(default=0, description="Y position for layout.")
    label: str = Field(..., description="Display name for the node.")
    inputs: List[PortDefinition] = Field(default_factory=list, description="Input ports.")
    outputs: List[PortDefinition] = Field(default_factory=list, description="Output ports.")

class GraphEdge(BaseModel):
    """An edge connecting two nodes in the workflow graph."""
    id: str = Field(..., description="Unique edge identifier.")
    source: str = Field(..., description="Source node ID.")
    target: str = Field(..., description="Target node ID.")
    source_handle: str = Field(default="out-1", description="Output port ID on source.")
    target_handle: str = Field(default="in-1", description="Input port ID on target.")

class Adapter(BaseModel):
    """Type conversion adapter between incompatible nodes."""
    id: str = Field(..., description="Unique adapter identifier.")
    name: str = Field(..., description="Adapter name.")
    source_type: str = Field(..., description="Source MIME type.")
    target_type: str = Field(..., description="Target MIME type.")
    cwl: str = Field(default="", description="CWL definition for the adapter.")
    dockerfile: str = Field(default="", description="Dockerfile for the adapter.")

class WorkflowResult(BaseModel):
    """Top-level response structure for Engineer Agent."""

    thought_process: str = Field(..., description="Step-by-step reasoning for workflow generation.")

    workflow_cwl: str = Field(..., description="Complete CWL v1.3 workflow YAML.")
    tool_cwls: Dict[str, str] = Field(default_factory=dict, description="CWL CommandLineTool YAML per tool.")
    dockerfiles: Dict[str, str] = Field(default_factory=dict, description="Dockerfile content per tool.")
    adapters: List[Adapter] = Field(default_factory=list, description="Type mismatch adapters.")

    nodes: List[GraphNode] = Field(default_factory=list, description="Workflow graph nodes.")
    edges: List[GraphEdge] = Field(default_factory=list, description="Workflow graph edges.")

# --- Reviewer Agent Schema ---

class ValidationIssue(BaseModel):
    """A single validation issue found in the workflow."""
    id: str = Field(..., description="Unique issue identifier.")
    severity: str = Field(..., description="Severity: error, warning, or info.")
    category: str = Field(..., description="Category: cwl_syntax, type_mismatch, dependency, or logic.")
    message: str = Field(..., description="Technical description of the issue.")
    user_friendly_message: str = Field(..., description="User-friendly explanation.")
    suggestion: str = Field(..., description="Actionable fix suggestion.")
    node_id: Optional[str] = Field(default=None, description="Related node ID if applicable.")
    auto_fixable: bool = Field(default=False, description="Whether this can be automatically fixed.")

class ValidationResult(BaseModel):
    """Top-level response structure for Reviewer Agent."""

    thought_process: str = Field(..., description="Step-by-step reasoning for validation.")

    passed: bool = Field(..., description="Whether all critical checks passed.")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues found.")
    summary: str = Field(..., description="Brief summary of validation results.")

# --- Error Translation Schema ---

class TranslatedError(BaseModel):
    """A technical error translated to user-friendly language."""
    original: str = Field(..., description="The original technical error message.")
    translated: str = Field(..., description="User-friendly explanation.")
    suggestion: str = Field(..., description="What the user should do to fix it.")
    severity: str = Field(..., description="Severity: error, warning, or info.")

class ErrorTranslationResult(BaseModel):
    """Response from error translation."""
    thought_process: str = Field(..., description="Reasoning about the errors.")
    translations: List[TranslatedError] = Field(default_factory=list, description="Translated error messages.")
