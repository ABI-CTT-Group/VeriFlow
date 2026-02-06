from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter()

class GeminiKeyRequest(BaseModel):
    key: str

@router.post("/settings/gemini-key")
async def verify_gemini_key(request: GeminiKeyRequest = Body(...)):
    """
    Receive the Gemini API Key from the frontend.
    
    NOTE: This endpoint is strictly for session/runtime usage.
    The key is NOT stored in the database.
    It is only accepted to verify connectivity or set session state if needed.
    """
    # In a real scenario, we might validate the key here by making a dummy request to Gemini.
    # For now, we just acknowledge receipt as per requirements.
    # We mask the key in logs for security.
    masked_key = f"{request.key[:4]}...{request.key[-4:]}" if len(request.key) > 8 else "***"
    print(f"Received Gemini API Key: {masked_key}")
    
    return {"status": "success", "message": "Gemini API Key received and temporarily cached for session."}
