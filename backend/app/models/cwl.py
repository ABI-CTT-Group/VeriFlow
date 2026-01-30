"""
VeriFlow - CWL Pydantic Models
Per SPEC.md Section 3.4 and 7.2
Supports CWL v1.3 workflow parsing
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from enum import Enum


class CWLClass(str, Enum):
    """CWL document class types."""
    WORKFLOW = "Workflow"
    COMMAND_LINE_TOOL = "CommandLineTool"
    EXPRESSION_TOOL = "ExpressionTool"


class CWLType(str, Enum):
    """Common CWL types."""
    FILE = "File"
    DIRECTORY = "Directory"
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NULL = "null"
    ARRAY = "array"
    RECORD = "record"


class CWLInput(BaseModel):
    """CWL workflow or tool input definition."""
    id: Optional[str] = None
    type: Union[str, List[str], Dict[str, Any]]
    doc: Optional[str] = None
    default: Optional[Any] = None
    format: Optional[str] = None
    secondary_files: Optional[List[str]] = Field(None, alias="secondaryFiles")
    
    class Config:
        populate_by_name = True


class CWLOutput(BaseModel):
    """CWL workflow or tool output definition."""
    id: Optional[str] = None
    type: Union[str, List[str], Dict[str, Any]]
    doc: Optional[str] = None
    output_source: Optional[str] = Field(None, alias="outputSource")
    output_binding: Optional[Dict[str, Any]] = Field(None, alias="outputBinding")
    format: Optional[str] = None
    
    class Config:
        populate_by_name = True


class CWLStepInput(BaseModel):
    """Input mapping for a workflow step."""
    id: Optional[str] = None
    source: Optional[Union[str, List[str]]] = None
    default: Optional[Any] = None
    value_from: Optional[str] = Field(None, alias="valueFrom")
    
    class Config:
        populate_by_name = True


class CWLStepOutput(BaseModel):
    """Output definition for a workflow step."""
    id: str


class CWLStep(BaseModel):
    """A step in a CWL workflow."""
    id: Optional[str] = None
    run: str  # Path to tool CWL or inline tool definition
    in_: Dict[str, Union[str, CWLStepInput]] = Field(default_factory=dict, alias="in")
    out: List[Union[str, CWLStepOutput]] = Field(default_factory=list)
    scatter: Optional[Union[str, List[str]]] = None
    scatter_method: Optional[str] = Field(None, alias="scatterMethod")
    when: Optional[str] = None
    
    class Config:
        populate_by_name = True


class DockerRequirement(BaseModel):
    """Docker requirement for tool execution."""
    class_: str = Field("DockerRequirement", alias="class")
    docker_pull: Optional[str] = Field(None, alias="dockerPull")
    docker_load: Optional[str] = Field(None, alias="dockerLoad")
    docker_file: Optional[str] = Field(None, alias="dockerFile")
    docker_import: Optional[str] = Field(None, alias="dockerImport")
    docker_image_id: Optional[str] = Field(None, alias="dockerImageId")
    docker_output_directory: Optional[str] = Field(None, alias="dockerOutputDirectory")
    
    class Config:
        populate_by_name = True


class ResourceRequirement(BaseModel):
    """Resource requirements for tool execution."""
    class_: str = Field("ResourceRequirement", alias="class")
    cores_min: Optional[int] = Field(None, alias="coresMin")
    cores_max: Optional[int] = Field(None, alias="coresMax")
    ram_min: Optional[int] = Field(None, alias="ramMin")  # MB
    ram_max: Optional[int] = Field(None, alias="ramMax")  # MB
    tmpdir_min: Optional[int] = Field(None, alias="tmpdirMin")  # MB
    tmpdir_max: Optional[int] = Field(None, alias="tmpdirMax")  # MB
    outdir_min: Optional[int] = Field(None, alias="outdirMin")  # MB
    outdir_max: Optional[int] = Field(None, alias="outdirMax")  # MB
    
    class Config:
        populate_by_name = True


class CWLRequirements(BaseModel):
    """Container for CWL requirements."""
    docker: Optional[DockerRequirement] = None
    resource: Optional[ResourceRequirement] = None
    inline_javascript: Optional[bool] = Field(None, alias="InlineJavascriptRequirement")
    scatter: Optional[bool] = Field(None, alias="ScatterFeatureRequirement")
    subworkflow: Optional[bool] = Field(None, alias="SubworkflowFeatureRequirement")
    
    class Config:
        populate_by_name = True


class CWLCommandLineTool(BaseModel):
    """CWL CommandLineTool definition."""
    cwl_version: str = Field(..., alias="cwlVersion")
    class_: str = Field(..., alias="class")
    id: Optional[str] = None
    label: Optional[str] = None
    doc: Optional[str] = None
    base_command: Optional[Union[str, List[str]]] = Field(None, alias="baseCommand")
    arguments: Optional[List[Union[str, Dict[str, Any]]]] = None
    inputs: Dict[str, CWLInput] = Field(default_factory=dict)
    outputs: Dict[str, CWLOutput] = Field(default_factory=dict)
    requirements: Optional[List[Dict[str, Any]]] = None
    hints: Optional[List[Dict[str, Any]]] = None
    stdin: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    success_codes: Optional[List[int]] = Field(None, alias="successCodes")
    temporary_fail_codes: Optional[List[int]] = Field(None, alias="temporaryFailCodes")
    permanent_fail_codes: Optional[List[int]] = Field(None, alias="permanentFailCodes")
    
    class Config:
        populate_by_name = True


class CWLWorkflow(BaseModel):
    """CWL Workflow definition - main document type."""
    cwl_version: str = Field(..., alias="cwlVersion")
    class_: str = Field(..., alias="class")
    id: Optional[str] = None
    label: Optional[str] = None
    doc: Optional[str] = None
    inputs: Dict[str, CWLInput] = Field(default_factory=dict)
    outputs: Dict[str, CWLOutput] = Field(default_factory=dict)
    steps: Dict[str, CWLStep] = Field(default_factory=dict)
    requirements: Optional[List[Dict[str, Any]]] = None
    hints: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        populate_by_name = True


class ParsedWorkflow(BaseModel):
    """Parsed workflow with resolved dependencies."""
    workflow: CWLWorkflow
    tools: Dict[str, CWLCommandLineTool] = Field(default_factory=dict)
    step_order: List[str] = Field(default_factory=list)  # Topologically sorted steps
    step_dependencies: Dict[str, List[str]] = Field(default_factory=dict)  # step_id -> [dependency_ids]


# Response models for API
class CWLValidationResult(BaseModel):
    """Result of CWL validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CWLParseResult(BaseModel):
    """Result of CWL parsing."""
    success: bool
    workflow: Optional[ParsedWorkflow] = None
    error: Optional[str] = None
    validation: Optional[CWLValidationResult] = None
