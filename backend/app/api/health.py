from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
    )
