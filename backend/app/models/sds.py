"""
VeriFlow - SDS and Confidence Pydantic Models
Per SPEC.md Sections 3.1 and 3.3
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class SDSManifestRow(BaseModel):
    """SDS Manifest row schema per SPEC.md Section 3.1."""
    filename: str  # Relative path from dataset root
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = "Data file"
    file_type: Optional[str] = Field(None, alias="file type")  # text, image, data
    additional_type: Optional[str] = Field(None, alias="additional type")  # MIME type
    
    class Config:
        populate_by_name = True


class ConfidenceScoreItem(BaseModel):
    """A single confidence score with source reference."""
    value: int = Field(ge=0, le=100)  # 0-100 percentage
    source_page: Optional[int] = None
    source_text: Optional[str] = None


class ConfidenceScores(BaseModel):
    """Confidence scores for extracted properties per SPEC.md Section 3.3."""
    upload_id: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    scores: Dict[str, ConfidenceScoreItem] = Field(default_factory=dict)


class DatasetDescription(BaseModel):
    """SDS dataset_description.json schema."""
    name: str
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    license: str = "CC-BY-4.0"
    version: str = "1.0.0"
