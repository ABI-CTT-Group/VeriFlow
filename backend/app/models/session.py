"""
VeriFlow - Session and Message Pydantic Models
Per SPEC.md Section 3.6
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
import uuid


class AgentType(str, Enum):
    SCHOLAR = "scholar"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in the conversation history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent: AgentType


class ScholarState(BaseModel):
    """Scholar agent state."""
    extraction_complete: bool = False
    isa_json_path: Optional[str] = None
    confidence_scores_path: Optional[str] = None
    context_used: Optional[str] = None


class EngineerState(BaseModel):
    """Engineer agent state."""
    workflow_id: Optional[str] = None
    cwl_path: Optional[str] = None
    tools_generated: List[str] = Field(default_factory=list)
    adapters_generated: List[str] = Field(default_factory=list)


class ReviewerState(BaseModel):
    """Reviewer agent state."""
    validations_passed: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class AgentSession(BaseModel):
    """Complete agent session state."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    upload_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Agent-specific state
    scholar_state: ScholarState = Field(default_factory=ScholarState)
    engineer_state: EngineerState = Field(default_factory=EngineerState)
    reviewer_state: ReviewerState = Field(default_factory=ReviewerState)
    
    # Conversation history
    conversation_history: List[Message] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    upload_id: str


class SessionUpdateRequest(BaseModel):
    """Request to update session state."""
    scholar_state: Optional[ScholarState] = None
    engineer_state: Optional[EngineerState] = None
    reviewer_state: Optional[ReviewerState] = None
