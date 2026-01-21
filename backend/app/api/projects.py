from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_projects():
    """List all projects."""
    return {"projects": []}
