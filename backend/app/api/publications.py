"""
VeriFlow API - Publications Router
Handles PDF upload and study design extraction.
Per PLAN.md Stage 2/4 and SPEC.md Section 5.2
"""

import uuid
import asyncio
import json
import tempfile
from io import BytesIO
from pathlib import Path
from datetime import datetime
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

# Stage 4: Import Scholar Agent (Gemini 3 SDK)
try:
    from app.agents.scholar import ScholarAgent
    scholar_agent = ScholarAgent()
    SCHOLAR_AVAILABLE = True
except (ImportError, ValueError):
    SCHOLAR_AVAILABLE = False
    scholar_agent = None

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


class AdditionalInfoRequest(BaseModel):
    """Request to add additional info."""
    info: str


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
        try:
            # Save PDF to temp file for Gemini native upload
            temp_dir = tempfile.mkdtemp()
            temp_pdf_path = Path(temp_dir) / (file.filename or "upload.pdf")
            with open(temp_pdf_path, "wb") as f:
                f.write(file_content)

            _upload_cache[upload_id] = {
                "pdf_path": str(temp_pdf_path),
                "context_content": context_content,
                "status": "processing",
                "result": None,
            }
            # Queue background analysis
            background_tasks.add_task(
                _process_publication_async,
                upload_id,
                str(temp_pdf_path),
                context_content,
                session_id,
            )
        except Exception as e:
            _upload_cache[upload_id] = {
                "pdf_path": None,
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
    pdf_path: str,
    context_content: Optional[str],
    session_id: str,
):
    """Background task to process publication with Scholar Agent (Gemini 3)."""
    try:
        result = await scholar_agent.analyze_publication(
            pdf_path=pdf_path,
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


@router.post("/publications/{upload_id}/additional-info")
async def add_additional_info(upload_id: str, request: AdditionalInfoRequest):
    """
    Add user-provided additional guidance for the publication.
    This info helps downstream agents (Engineer/Reviewer).
    """
    if upload_id not in _upload_cache:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Store the info in the cache entry
    _upload_cache[upload_id]["additional_info"] = request.info
    
    # If using DB (Stage 4), we would persist this here
    
    return {"status": "success", "message": "Additional info stored"}


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
    
    # Check if this is a pre-loaded example (prioritize preloaded data)
    if upload_id in _upload_cache:
        cache_entry = _upload_cache[upload_id]
        status = cache_entry.get("status", "processing")
        
        # Handle pre-loaded examples directly
        if cache_entry.get("is_preloaded") and status == "completed":
            result = cache_entry.get("result", {})
            return StudyDesignResponse(
                upload_id=upload_id,
                status="completed",
                hierarchy={"investigation": result.get("isa_json", {})},
                confidence_scores={
                    "upload_id": upload_id,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "scores": result.get("confidence_scores", {}),
                },
            )
        
        # Stage 4: Handle Scholar Agent results
        if status == "completed" and cache_entry.get("result"):
            result = cache_entry["result"]
            return StudyDesignResponse(
                upload_id=upload_id,
                status="completed",
                hierarchy={"investigation": result.get("isa_json", {})},
                confidence_scores={
                    "upload_id": upload_id,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "scores": result.get("confidence_scores", {}),
                },
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
    
    # No data found - return not found error
    raise HTTPException(
        status_code=404,
        detail=f"No study design found for upload {upload_id}. Upload a PDF or load an example first."
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


# Request model for load-example
class LoadExampleRequest(BaseModel):
    """Request to load a pre-loaded example."""
    example_name: str = "mama-mia"


@router.post("/publications/load-example", response_model=UploadResponse)
async def load_example(request: LoadExampleRequest):
    """
    Load a pre-loaded example without file upload.
    
    Per PLAN.md Stage 6:
    - Loads ground truth ISA-JSON from backend/examples/{example_name}/
    - Returns upload_id with pre-populated ISA hierarchy
    - Used for MAMA-MIA demo flow
    """
    example_name = request.example_name
    
    # Determine example directory path
    # backend/examples/mama-mia/
    examples_dir = Path(__file__).parent.parent.parent / "examples" / example_name
    ground_truth_path = examples_dir / "ground_truth_isa.json"
    context_path = examples_dir / "context.txt"
    
    if not ground_truth_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Example '{example_name}' not found. Available examples: mama-mia"
        )
    
    # Generate unique upload ID
    upload_id = f"pub_{uuid.uuid4().hex[:12]}"
    
    # Load ground truth ISA-JSON
    try:
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load ground truth: {str(e)}"
        )
    
    # Load context file if exists
    context_content = None
    if context_path.exists():
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                context_content = f.read()
        except Exception:
            pass
    
    # Store in cache with immediate completion status
    _upload_cache[upload_id] = {
        "pdf_text": context_content or "[Pre-loaded example - no PDF text]",
        "context_content": context_content,
        "status": "completed",
        "result": {
            "isa_json": ground_truth.get("investigation", {}),
            "confidence_scores": ground_truth.get("confidence_scores", {}),
            "identified_tools": ground_truth.get("identified_tools", []),
            "identified_models": ground_truth.get("identified_models", []),
            "identified_measurements": ground_truth.get("identified_measurements", []),
        },
        "is_preloaded": True,
    }
    
    # Create agent session (optional)
    try:
        session = await db_service.create_session(upload_id)
        session_id = session.session_id
    except Exception:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
    return UploadResponse(
        upload_id=upload_id,
        filename=f"{example_name}_example.pdf",
        status="completed",
        message=f"Loaded pre-configured {example_name.upper()} example with ground truth ISA hierarchy.",
        session_id=session_id,
    )
