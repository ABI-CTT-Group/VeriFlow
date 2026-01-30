"""
VeriFlow API - Catalogue Router
Handles data object catalogue and viewer endpoints.
Per PLAN.md Stage 2 and SPEC.md
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException

from app.models.catalogue import (
    CatalogueItemType,
    CatalogueItem,
    CatalogueResponse,
    CatalogueUpdateRequest,
    SourceSnippet,
)
from app.services.minio_client import minio_service

router = APIRouter()

# Mock catalogue data (Stage 4/5 will populate from MinIO)
MOCK_CATALOGUE: List[CatalogueItem] = [
    CatalogueItem(
        id="tool-dcm2niix",
        type=CatalogueItemType.TOOL,
        name="DICOM to NIfTI Converter",
        category="preprocessing",
        description="Convert DICOM series to NIfTI format using dcm2niix",
        docker_image="neurolabusc/dcm2niix:latest",
    ),
    CatalogueItem(
        id="tool-breast-seg",
        type=CatalogueItemType.TOOL,
        name="Breast Tumor Segmentation",
        category="segmentation",
        description="U-Net based breast tumor segmentation from DCE-MRI",
        docker_image="breast-segmentation:latest",
    ),
    CatalogueItem(
        id="model-unet-weights",
        type=CatalogueItemType.MODEL,
        name="U-Net Pretrained Weights",
        category="segmentation",
        description="Pre-trained U-Net weights for breast tumor segmentation",
        minio_path="workflow-tool/models/unet_breast.pth",
    ),
    CatalogueItem(
        id="meas-mama-mia",
        type=CatalogueItemType.MEASUREMENT,
        name="MAMA-MIA DCE-MRI Dataset",
        category="imaging",
        description="Dynamic Contrast-Enhanced MRI scans from MAMA-MIA study",
        minio_path="measurements/mama-mia",
    ),
    CatalogueItem(
        id="tool-n4-bias",
        type=CatalogueItemType.TOOL,
        name="N4 Bias Field Correction",
        category="preprocessing",
        description="N4 bias field correction for MRI images",
        docker_image="ants/n4:latest",
    ),
]

# Mock source snippets for viewer
MOCK_SOURCES: dict[str, SourceSnippet] = {
    "src_1": SourceSnippet(
        id="src_1",
        text="This paper presents an automated approach for breast cancer detection using deep learning techniques applied to dynamic contrast-enhanced MRI (DCE-MRI) scans.",
        pdf_location={"page": 1, "rect": [72, 150, 540, 180]},
    ),
    "src_2": SourceSnippet(
        id="src_2",
        text="We propose a U-Net based architecture for automated tumor segmentation, achieving state-of-the-art performance on the MAMA-MIA dataset.",
        pdf_location={"page": 1, "rect": [72, 200, 540, 230]},
    ),
    "src_3": SourceSnippet(
        id="src_3",
        text="A total of 384 patients were enrolled in this study, with DCE-MRI scans acquired between 2018 and 2023.",
        pdf_location={"page": 3, "rect": [72, 300, 540, 330]},
    ),
    "src_4": SourceSnippet(
        id="src_4",
        text="Dynamic contrast-enhanced MRI was performed using a 3T scanner with the following acquisition parameters...",
        pdf_location={"page": 2, "rect": [72, 150, 540, 180]},
    ),
}


@router.get("/catalogue", response_model=CatalogueResponse)
async def list_catalogue(
    workflow_id: Optional[str] = None,
    type: Optional[str] = None,
):
    """
    List all data objects, tools, and models.
    
    Per SPEC.md:
    - Returns catalogue items from MinIO buckets
    - Marks items as in_use if they appear in the specified workflow
    """
    items = MOCK_CATALOGUE.copy()
    
    # Filter by type if specified
    if type:
        try:
            item_type = CatalogueItemType(type)
            items = [item for item in items if item.type == item_type]
        except ValueError:
            pass
    
    # Mark items as in_use if workflow_id is provided
    if workflow_id:
        # For MVP, mark specific items as in use
        in_use_ids = {"tool-dcm2niix", "tool-breast-seg", "model-unet-weights", "meas-mama-mia"}
        for item in items:
            item.in_use = item.id in in_use_ids
    
    return CatalogueResponse(items=items)


@router.put("/catalogue/{item_id}")
async def update_catalogue_item(item_id: str, request: CatalogueUpdateRequest):
    """
    Update metadata for a catalogue item.
    
    Per SPEC.md:
    - Updates item name, description, or other metadata
    - Stage 4/5 will persist to MinIO
    """
    # Find item in mock catalogue
    item = next((i for i in MOCK_CATALOGUE if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Catalogue item {item_id} not found")
    
    # Update fields
    updates = request.model_dump(exclude_none=True)
    for field, value in updates.items():
        if hasattr(item, field):
            setattr(item, field, value)
    
    return {
        "id": item_id,
        "updated": True,
        "changes": updates,
        "message": "Catalogue item updated (Stage 4/5 will implement full persistence)",
    }


@router.get("/sources/{source_id}", response_model=SourceSnippet)
async def get_source_snippet(source_id: str):
    """
    Get PDF citation snippet for a source reference.
    
    Per SPEC.md:
    - Returns text snippet and PDF location for highlighting
    - Stage 4 will extract real snippets from PDFs
    """
    if source_id not in MOCK_SOURCES:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    
    source = MOCK_SOURCES[source_id]
    
    # Try to add presigned URL for the PDF
    # This would be set when a publication is uploaded
    source.pdf_url = None  # Stage 4 will populate this
    
    return source
