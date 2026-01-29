"""
VeriFlow API - Publications Router
Handles PDF upload and study design extraction.
Per PLAN.md Stage 2 and SPEC.md Section 5.2
"""

import uuid
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional

from app.models.isa import (
    InvestigationWithProperties,
    StudyWithProperties,
    AssayWithProperties,
    PropertyItem,
)
from app.models.sds import ConfidenceScores, ConfidenceScoreItem
from app.models.session import AgentSession
from app.services.minio_client import minio_service
from app.services.database import db_service

router = APIRouter()


# Response models
from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response from PDF upload."""
    upload_id: str
    filename: str
    status: str
    message: str
    session_id: Optional[str] = None


class StudyDesignResponse(BaseModel):
    """Response with ISA hierarchy."""
    upload_id: str
    status: str
    hierarchy: Optional[dict] = None
    confidence_scores: Optional[dict] = None


class PropertyUpdateRequest(BaseModel):
    """Request to update a property."""
    property_id: str
    value: str


@router.post("/publications/upload", response_model=UploadResponse)
async def upload_publication(
    file: UploadFile = File(...),
    context_file: Optional[UploadFile] = File(None),
):
    """
    Upload a PDF publication for processing.
    Triggers the Scholar Agent for ISA extraction.
    
    Per SPEC.md Section 5.2:
    - Stores file in MinIO
    - Creates agent session
    - Returns upload_id for subsequent operations
    """
    # Generate unique upload ID
    upload_id = f"pub_{uuid.uuid4().hex[:12]}"
    
    # Read file content
    file_content = await file.read()
    
    # Store PDF in MinIO (measurements bucket for now)
    object_name = f"uploads/{upload_id}/{file.filename}"
    try:
        minio_service.upload_file(
            bucket=minio_service.MEASUREMENTS_BUCKET,
            object_name=object_name,
            file_data=BytesIO(file_content),
            content_type=file.content_type or "application/pdf",
            length=len(file_content),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")
    
    # Store context file if provided
    context_path = None
    if context_file:
        context_content = await context_file.read()
        context_object_name = f"uploads/{upload_id}/{context_file.filename}"
        minio_service.upload_file(
            bucket=minio_service.MEASUREMENTS_BUCKET,
            object_name=context_object_name,
            file_data=BytesIO(context_content),
            content_type=context_file.content_type or "text/plain",
            length=len(context_content),
        )
        context_path = context_object_name
    
    # Create agent session
    try:
        session = await db_service.create_session(upload_id)
        session_id = session.session_id
    except Exception as e:
        # If database is not available, continue without session
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "unknown.pdf",
        status="processing",
        message="Scholar Agent analyzing... (Stage 4 will implement full agent logic)",
        session_id=session_id,
    )


@router.get("/study-design/{upload_id}", response_model=StudyDesignResponse)
async def get_study_design(upload_id: str):
    """
    Get the ISA hierarchy extracted from a publication.
    Returns Investigation -> Study -> Assay structure.
    
    Per SPEC.md Section 5.2:
    - Returns hierarchical ISA-JSON structure
    - Includes confidence scores for each property
    """
    # Try to get session from database
    session = None
    try:
        session = await db_service.get_session_by_upload(upload_id)
    except Exception:
        pass
    
    # For MVP, return mock data until Stage 4 (Agent Integration)
    # The Scholar Agent will populate this in Stage 4
    mock_hierarchy = {
        "investigation": {
            "id": "inv_1",
            "title": "Automated Breast Cancer Detection using DCE-MRI",
            "description": "A study on automated tumor segmentation from dynamic contrast-enhanced MRI scans.",
            "properties": [
                {"id": "inv-title", "value": "Automated Breast Cancer Detection", "source_id": "src_1", "confidence": 95},
                {"id": "inv-description", "value": "Study on automated tumor segmentation", "source_id": "src_2", "confidence": 88},
            ],
            "studies": [
                {
                    "id": "study_1",
                    "title": "MAMA-MIA Segmentation Study",
                    "description": "Segmentation of breast tumors using U-Net architecture.",
                    "properties": [
                        {"id": "study-subjects", "value": "384 patients", "source_id": "src_3", "confidence": 92},
                        {"id": "study-modality", "value": "DCE-MRI", "source_id": "src_4", "confidence": 97},
                    ],
                    "assays": [
                        {
                            "id": "assay_1",
                            "name": "U-Net Training Pipeline",
                            "description": "Training pipeline for breast tumor segmentation.",
                            "steps": [
                                {"id": "step_1", "description": "Data acquisition and preprocessing"},
                                {"id": "step_2", "description": "DICOM to NIfTI conversion"},
                                {"id": "step_3", "description": "U-Net model training"},
                                {"id": "step_4", "description": "Inference and evaluation"},
                            ],
                        },
                        {
                            "id": "assay_2",
                            "name": "Inference Pipeline",
                            "description": "Inference pipeline for new patient scans.",
                            "steps": [
                                {"id": "step_1", "description": "Load pre-trained model"},
                                {"id": "step_2", "description": "Process input scan"},
                                {"id": "step_3", "description": "Generate segmentation mask"},
                            ],
                        },
                    ],
                },
            ],
        },
    }
    
    mock_confidence = {
        "upload_id": upload_id,
        "generated_at": "2026-01-29T12:00:00Z",
        "scores": {
            "inv-title": {"value": 95, "source_page": 1, "source_text": "Automated Breast Cancer Detection..."},
            "inv-description": {"value": 88, "source_page": 1, "source_text": "This study presents..."},
            "study-subjects": {"value": 92, "source_page": 3, "source_text": "384 patients were enrolled..."},
            "study-modality": {"value": 97, "source_page": 2, "source_text": "Dynamic contrast-enhanced MRI..."},
        },
    }
    
    return StudyDesignResponse(
        upload_id=upload_id,
        status="completed",
        hierarchy=mock_hierarchy,
        confidence_scores=mock_confidence,
    )


@router.put("/study-design/nodes/{node_id}/properties")
async def update_node_property(node_id: str, request: PropertyUpdateRequest):
    """
    Update a property value in the study design.
    
    Per SPEC.md Section 5.2:
    - Updates editable properties in the ISA structure
    - Persists changes to database/storage
    """
    # For MVP, return success without actual persistence
    # Stage 4 will implement full database updates
    return {
        "node_id": node_id,
        "property_id": request.property_id,
        "value": request.value,
        "updated": True,
        "message": "Property updated (Stage 4 will implement full persistence)",
    }
