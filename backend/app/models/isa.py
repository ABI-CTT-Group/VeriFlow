"""
VeriFlow - ISA-JSON Pydantic Models
Per SPEC.md Section 3.2
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OntologyAnnotation(BaseModel):
    """ISA-JSON Ontology Annotation."""
    term: str
    term_source: Optional[str] = None
    term_accession: Optional[str] = None


class Assay(BaseModel):
    """ISA-JSON Assay definition."""
    id: str = Field(default_factory=lambda: f"assay_{datetime.now().timestamp()}")
    filename: str
    name: Optional[str] = None
    measurement_type: Optional[OntologyAnnotation] = None
    technology_type: Optional[OntologyAnnotation] = None
    
    class Config:
        populate_by_name = True


class Study(BaseModel):
    """ISA-JSON Study definition."""
    id: str = Field(default_factory=lambda: f"study_{datetime.now().timestamp()}")
    identifier: str
    title: str
    description: str = ""
    assays: List[Assay] = Field(default_factory=list)


class Investigation(BaseModel):
    """ISA-JSON Investigation definition - root of hierarchy."""
    id: str = Field(default_factory=lambda: f"inv_{datetime.now().timestamp()}")
    identifier: str
    title: str
    description: str = ""
    studies: List[Study] = Field(default_factory=list)


class PropertyItem(BaseModel):
    """A single property with confidence metadata."""
    id: str
    value: str
    source_id: Optional[str] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)


class InvestigationWithProperties(BaseModel):
    """Investigation with extracted properties for UI display."""
    id: str
    title: str
    description: str = ""
    properties: List[PropertyItem] = Field(default_factory=list)
    studies: List["StudyWithProperties"] = Field(default_factory=list)


class StudyWithProperties(BaseModel):
    """Study with extracted properties for UI display."""
    id: str
    title: str
    description: str = ""
    properties: List[PropertyItem] = Field(default_factory=list)
    assays: List["AssayWithProperties"] = Field(default_factory=list)


class AssayWithProperties(BaseModel):
    """Assay with extracted properties for UI display."""
    id: str
    name: str
    description: str = ""
    properties: List[PropertyItem] = Field(default_factory=list)
    steps: List[dict] = Field(default_factory=list)


# Update forward references
InvestigationWithProperties.model_rebuild()
StudyWithProperties.model_rebuild()
