"""
VeriFlow - Execution Pydantic Models
Per SPEC.md Sections 5.4 and 5.5
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum
import uuid


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class NodeExecutionStatus(BaseModel):
    """Status of a single node in execution."""
    execution_sub_id: Optional[str] = None
    status: str = "pending"
    progress: int = Field(0, ge=0, le=100)


class LogEntry(BaseModel):
    """A single log entry."""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: LogLevel = LogLevel.INFO
    message: str
    node_id: Optional[str] = None
    agent: Optional[str] = None


class ExecutionConfig(BaseModel):
    """Configuration for workflow execution."""
    subjects: List[int] = Field(default=[1])  # Subject IDs to process


class ExecutionRequest(BaseModel):
    """Request to start workflow execution."""
    workflow_id: str
    config: Optional[ExecutionConfig] = None


class ExecutionResponse(BaseModel):
    """Response when execution is triggered."""
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    status: ExecutionStatus = ExecutionStatus.QUEUED
    dag_id: Optional[str] = None


class ExecutionStatusResponse(BaseModel):
    """Detailed execution status response."""
    execution_id: str
    status: ExecutionStatus
    overall_progress: int = Field(0, ge=0, le=100)
    nodes: Dict[str, NodeExecutionStatus] = Field(default_factory=dict)
    logs: List[LogEntry] = Field(default_factory=list)


class ResultFile(BaseModel):
    """A result file from execution."""
    path: str
    node_id: str
    size: int
    download_url: Optional[str] = None
    mime_type: Optional[str] = None


class ExecutionResultsResponse(BaseModel):
    """Response with execution result files."""
    execution_id: str
    files: List[ResultFile] = Field(default_factory=list)


# WebSocket message types per SPEC.md Section 5.5
class AgentStatusMessage(BaseModel):
    """WebSocket message for agent status."""
    type: Literal["agent_status"] = "agent_status"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent: str
    status: str  # idle, thinking, processing, complete, error
    message: Optional[str] = None


class NodeStatusMessage(BaseModel):
    """WebSocket message for node status."""
    type: Literal["node_status"] = "node_status"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_id: str
    execution_sub_id: Optional[str] = None
    node_id: str
    status: str
    progress: int = Field(0, ge=0, le=100)


class LogEntryMessage(BaseModel):
    """WebSocket message for log entry."""
    type: Literal["log"] = "log"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: LogLevel
    message: str
    node_id: Optional[str] = None
    agent: Optional[str] = None


class ExecutionCompleteMessage(BaseModel):
    """WebSocket message for execution completion."""
    type: Literal["execution_complete"] = "execution_complete"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_id: str
    status: str  # success, partial_failure, failed
    results_url: Optional[str] = None
