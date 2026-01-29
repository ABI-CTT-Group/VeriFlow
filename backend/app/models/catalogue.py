"""
VeriFlow - Catalogue Pydantic Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class CatalogueItemType(str, Enum):
    MEASUREMENT = "measurement"
    TOOL = "tool"
    MODEL = "model"


class CatalogueItem(BaseModel):
    """A data object, tool, or model in the catalogue."""
    id: str
    type: CatalogueItemType
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    in_use: bool = False
    # Additional metadata
    minio_path: Optional[str] = None
    docker_image: Optional[str] = None
    cwl_path: Optional[str] = None


class CatalogueResponse(BaseModel):
    """Response listing catalogue items."""
    items: List[CatalogueItem] = Field(default_factory=list)


class CatalogueUpdateRequest(BaseModel):
    """Request to update catalogue item metadata."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[dict] = None


class SourceSnippet(BaseModel):
    """PDF citation source snippet."""
    id: str
    text: str
    pdf_location: Optional[dict] = None  # {page, rect}
    pdf_url: Optional[str] = None
