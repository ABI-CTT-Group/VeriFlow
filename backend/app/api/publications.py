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
import logging

logger = logging.getLogger(__name__)

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

            # Queue background analysis
            background_tasks.add_task(
                _process_publication_async,
                upload_id,
                str(temp_pdf_path),
                context_content,
                session_id,
            )
        except Exception as e:
            print(f"Error queuing scholar agent task: {e}")
            # Optionally update session with error status if task queuing fails
    
    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "unknown.pdf",
        status="processing",
        message="Scholar Agent analyzing publication...",
        session_id=session_id,
    )


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

        # Create log directory for this run to store simulated files
        log_dir = Path("logs") / upload_id
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create simulated scholar output file
        scholar_output_path = log_dir / "scholar_isa.json"
        with open(scholar_output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # Update agent session in DB
        database_service.create_or_update_agent_session(
            run_id=upload_id,
            scholar_extraction_complete=True,
            scholar_isa_json_path=str(scholar_output_path.resolve())
        )
        
        # Store conversation message in database
        try:
            message = Message(
                role=MessageRole.ASSISTANT,
                content=f"Extracted ISA hierarchy from publication. Found {len(result.get('identified_tools', []))} tools, {len(result.get('identified_models', []))} models.",
                agent=AgentType.SCHOLAR,
            )
            # Note: db_service is from database_sqlite which is sync. Use a thread pool executor if blocking.
            db_service.add_message(session_id, message) # Assuming add_message is now synchronous
        except Exception as e:
            print(f"Warning: Failed to add conversation message: {e}")
            pass  # Continue even if DB is unavailable
            
    except Exception as e:
        print(f"Scholar agent background task failed: {e}")
        # Update DB session with error status if needed
        database_service.create_or_update_agent_session(
            run_id=upload_id,
            scholar_extraction_complete=False, # Mark as not complete
            # Optionally store error message in DB
        )


@router.post("/publications/{upload_id}/additional-info")
async def add_additional_info(upload_id: str, request: AdditionalInfoRequest):
    """
    Add user-provided additional guidance for the publication.
    This info helps downstream agents (Engineer/Reviewer).
    """
    # If using DB, we would persist this here. For now, it's acknowledged.
    return {"status": "success", "message": "Additional info stored (not persisted in SQLite MVP)"}


@router.get("/study-design/{upload_id}", response_model=StudyDesignResponse)
async def get_study_design(upload_id: str):
    """
    Get the ISA hierarchy extracted from a publication.
    Returns Investigation -> Study -> Assay structure.
    
    Per SPEC.md Section 5.2:
    - Returns hierarchical ISA-JSON structure
    - Includes confidence scores for each property
    """
    # Always try to get session from database
    session = database_service.get_agent_session(upload_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"No study design found for upload {upload_id}. Upload a PDF or load an example first."
        )

    status = "processing"
    hierarchy_data = None
    confidence_scores_data = None

    if session.get("scholar_extraction_complete"):
        scholar_isa_json_path = session.get("scholar_isa_json_path")
        if scholar_isa_json_path and Path(scholar_isa_json_path).exists():
            try:
                with open(scholar_isa_json_path, "r", encoding="utf-8") as f:
                    scholar_result = json.load(f)
                    hierarchy_data = {"investigation": scholar_result.get("isa_json", {})}
                    confidence_scores_data = {
                        "upload_id": upload_id,
                        "generated_at": datetime.utcnow().isoformat() + "Z",
                        "scores": scholar_result.get("confidence_scores", {}),
                    }
                    status = "completed"
            except json.JSONDecodeError:
                status = "error"
        else:
            status = "error" # Path exists but file not found or readable

    return StudyDesignResponse(
        upload_id=upload_id,
        status=status,
        hierarchy=hierarchy_data,
        confidence_scores=confidence_scores_data,
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
class LoadExampleResponse(BaseModel):
    """Response from loading a pre-loaded example."""
    upload_id: str
    filename: str
    status: str
    message: str
    session_id: Optional[str] = None
    hierarchy: Optional[dict] = None
    engineer_output: Optional[dict] = None

class LoadExampleRequest(BaseModel):
    """Request to load a pre-loaded example."""
    example_name: str = "mama-mia"


@router.post("/publications/load-example", response_model=LoadExampleResponse)
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
    examples_dir = Path(__file__).parent.parent.parent / "examples" / example_name
    ground_truth_isa_path = examples_dir / "ground_truth_isa.json"
    mock_engineer_code_path = examples_dir / "mock_engineer_code.json"
    context_path = examples_dir / "context.txt"
    
    if not ground_truth_isa_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Example '{example_name}' not found. Available examples: mama-mia"
        )
    
    # Generate unique upload ID
    upload_id = f"pub_{uuid.uuid4().hex[:12]}"
    
    # Create a log directory for this run to store simulated files
    log_dir = Path("logs") / upload_id
    log_dir.mkdir(parents=True, exist_ok=True)

    # Load ground truth ISA-JSON
    try:
        with open(ground_truth_isa_path, 'r', encoding='utf-8') as f:
            ground_truth_isa = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load ground truth ISA: {str(e)}"
        )

    # Load mock engineer code (or create a default if not exists)
    engineer_output = {"graph": {"nodes": [], "edges": []}, "validation_report": {}}
    if mock_engineer_code_path.exists():
        try:
            with open(mock_engineer_code_path, 'r', encoding='utf-8') as f:
                engineer_output = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load mock engineer code for demo: {e}")

    # Load context file if exists (not persisted to DB for now)
    context_content = None
    if context_path.exists():
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                context_content = f.read()
        except Exception:
            pass

    response_data = LoadExampleResponse(
        upload_id=upload_id,
        filename=f"{example_name}_example.pdf",
        status="completed",
        message=f"Loaded pre-configured {example_name.upper()} example with ground truth ISA hierarchy.",
        session_id=upload_id, # Use upload_id as session_id for consistency
        hierarchy={"investigation": ground_truth_isa.get("isa_json", {})},
        engineer_output=engineer_output
    )
    logger.info(f"[/publications/load-example] Returning response for upload_id: {upload_id}, Response: {response_data.dict()}")
    return response_data
