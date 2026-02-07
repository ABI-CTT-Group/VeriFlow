from pydantic import BaseModel, Field
from typing import List, Optional

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

# --- Main Content Models ---

class Investigation(BaseModel):
    """Structured ISA investigation data."""
    title: str = Field(..., description="The title of the publication or investigation.")
    description: str = Field(..., description="A concise summary of the study.")
    study_factors: List[str] = Field(default_factory=list, description="List of experimental factors (e.g., 'Time', 'Dose').")
    metadata: List[KeyValue] = Field(default_factory=list, description="Additional metadata fields.")

class AnalysisResult(BaseModel):
    """Top-level response structure."""
    
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