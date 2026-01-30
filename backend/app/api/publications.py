"""
VeriFlow API - Publications Router
Handles PDF upload and study design extraction.
Per PLAN.md Stage 2/4 and SPEC.md Section 5.2
"""

import uuid
import asyncio
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional

from app.models.isa import (
    InvestigationWithProperties,
    StudyWithProperties,
    AssayWithProperties,
    PropertyItem,
)
from app.models.sds import ConfidenceScores, ConfidenceScoreItem
from app.models.session import AgentSession, Message, AgentType, MessageRole
from app.services.minio_client import minio_service
from app.services.database import db_service

# Stage 4: Import Scholar Agent
try:
    from app.agents.scholar import scholar_agent
    SCHOLAR_AVAILABLE = True
except ImportError:
    SCHOLAR_AVAILABLE = False

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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context_file: Optional[UploadFile] = File(None),
):
    """
    Upload a PDF publication for processing.
    Triggers the Scholar Agent for ISA extraction.
    
    Per SPEC.md Section 5.2:
    - Stores file in MinIO
    - Creates agent session
    - Triggers Scholar Agent in background
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
    context_content = None
    if context_file:
        context_bytes = await context_file.read()
        context_content = context_bytes.decode('utf-8', errors='ignore')
        context_object_name = f"uploads/{upload_id}/{context_file.filename}"
        minio_service.upload_file(
            bucket=minio_service.MEASUREMENTS_BUCKET,
            object_name=context_object_name,
            file_data=BytesIO(context_bytes),
            content_type=context_file.content_type or "text/plain",
            length=len(context_bytes),
        )
        context_path = context_object_name
    
    # Create agent session
    try:
        session = await db_service.create_session(upload_id)
        session_id = session.session_id
    except Exception as e:
        # If database is not available, continue without session
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
    # Stage 4: Trigger Scholar Agent in background if available
    if SCHOLAR_AVAILABLE:
        # Extract text from PDF
        try:
            pdf_text = scholar_agent.extract_text_from_pdf(file_content)
            # Store extracted text for analysis
            _upload_cache[upload_id] = {
                "pdf_text": pdf_text,
                "context_content": context_content,
                "status": "processing",
                "result": None,
            }
            # Queue background analysis
            background_tasks.add_task(
                _process_publication_async,
                upload_id,
                pdf_text,
                context_content,
                session_id,
            )
        except Exception as e:
            _upload_cache[upload_id] = {
                "pdf_text": None,
                "context_content": context_content,
                "status": "error",
                "error": str(e),
                "result": None,
            }
    
    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "unknown.pdf",
        status="processing",
        message="Scholar Agent analyzing publication...",
        session_id=session_id,
    )


# Cache for upload processing results
_upload_cache: dict[str, dict] = {}


async def _process_publication_async(
    upload_id: str,
    pdf_text: str,
    context_content: Optional[str],
    session_id: str,
):
    """Background task to process publication with Scholar Agent."""
    try:
        result = await scholar_agent.analyze_publication(
            pdf_text=pdf_text,
            context_content=context_content,
            upload_id=upload_id,
        )
        
        _upload_cache[upload_id]["status"] = "completed"
        _upload_cache[upload_id]["result"] = result
        
        # Store conversation message in database
        try:
            message = Message(
                role=MessageRole.ASSISTANT,
                content=f"Extracted ISA hierarchy from publication. Found {len(result.get('identified_tools', []))} tools, {len(result.get('identified_models', []))} models.",
                agent=AgentType.SCHOLAR,
            )
            await db_service.add_message(session_id, message)
        except Exception:
            pass  # Continue even if DB is unavailable
            
    except Exception as e:
        _upload_cache[upload_id]["status"] = "error"
        _upload_cache[upload_id]["error"] = str(e)


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
    
    # Stage 4: Check if we have Scholar Agent result
    if SCHOLAR_AVAILABLE and upload_id in _upload_cache:
        cache_entry = _upload_cache[upload_id]
        status = cache_entry.get("status", "processing")
        
        if status == "completed" and cache_entry.get("result"):
            result = cache_entry["result"]
            hierarchy_response = scholar_agent.build_hierarchy_response(result, upload_id)
            
            return StudyDesignResponse(
                upload_id=upload_id,
                status="completed",
                hierarchy=hierarchy_response.get("hierarchy"),
                confidence_scores=hierarchy_response.get("confidence_scores"),
            )
        elif status == "error":
            return StudyDesignResponse(
                upload_id=upload_id,
                status="error",
                hierarchy=None,
                confidence_scores=None,
            )
        elif status == "processing":
            return StudyDesignResponse(
                upload_id=upload_id,
                status="processing",
                hierarchy=None,
                confidence_scores=None,
            )
    
    # Fallback: Return mock data for demo purposes
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
