
import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
# Assuming running from 'backend' directory
EXAMPLES_DIR = os.path.join(os.getcwd(), "examples", "f7417a90")

class OrchestrationResponse(BaseModel):
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None

async def stream_mock_data(client_id: str):
    """
    Streams mock data from the examples directory to the client via WebSocket.
    """
    logger.info(f"Starting mock data stream for client {client_id}")
    
    try:
        if not os.path.exists(EXAMPLES_DIR):
            logger.error(f"Examples directory not found: {EXAMPLES_DIR}")
            await manager.send_message(client_id, {
                "type": "error",
                "message": "Examples directory not found on server."
            })
            return

        # Get all JSON files and sort them
        files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith('.json')]
        files.sort() # Assumes files are named 1_*, 2_*, etc.
        
        logger.info(f"Found {len(files)} example files to stream.")

        for filename in files:
            file_path = os.path.join(EXAMPLES_DIR, filename)
            
            # Determine agent name from filename
            agent_name = "system"
            if "scholar" in filename.lower():
                agent_name = "scholar"
            elif "engineer" in filename.lower():
                agent_name = "engineer"
            elif "reviewer" in filename.lower():
                agent_name = "reviewer"
            elif "validate" in filename.lower():
                agent_name = "curator" # Or validate agent?
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Format message for console
                # We want to show the content. 
                # If it's 1_scholar.json, it has 'model_thoughts' etc.
                # We'll stream the whole content or specific parts?
                # The user requirement: "all files as each agent's name matched then send mock data to console"
                
                # Send a "thinking" status first (optional, adds realism)
                await manager.send_message(client_id, {
                    "type": "status_update",
                    "status": "info",
                    "message": f"{agent_name.capitalize()} Agent: Analyzing..."
                })
                
                await asyncio.sleep(1.0) # Simulate processing delay

                # Send the actual content
                # For better display in console, we might want to send it as a code block or just raw text
                # The console handles JSON specifically if we look at previous interactions, or we can just dump it stringified.
                
                content_str = json.dumps(data, indent=2)
                
                await manager.send_message(client_id, {
                    "type": "status_update",
                    "status": "success",
                    "message": f"{agent_name.capitalize()} Agent: {content_str}"
                })
                
                # Specific delay between agents
                await asyncio.sleep(1.5)

            except Exception as e:
                logger.error(f"Error reading/sending {filename}: {e}")
                
    except Exception as e:
        logger.error(f"Error in stream_mock_data: {e}")

@router.get("/mama-mia-cache", response_model=OrchestrationResponse)
async def get_mama_mia_cache(client_id: Optional[str] = None, background_tasks: BackgroundTasks = None):
    """
    Returns the cached MAMA-MIA result immediately and streams logs.
    """
    scholar_file = "1_scholar.json"
    scholar_path = os.path.join(EXAMPLES_DIR, scholar_file)
    
    if not os.path.exists(scholar_path):
        raise HTTPException(status_code=404, detail="MAMA-MIA example data not found.")
        
    try:
        with open(scholar_path, 'r', encoding='utf-8') as f:
            scholar_data = json.load(f)
            
        # The result to return immediately to populate UI
        # User requested: "http/http directly s return @[backend/examples/f7417a90/1_scholar.json]"
        # We need to extract the 'final_output' if that's what the UI expects for 'isa_json'
        
        result_payload = {
            "isa_json": scholar_data.get("final_output", {}),
            "generated_code": {}, # Example might not have this, or we can look for it
            "review_decision": "approved", # Mock success
            "review_feedback": "Excellent work.",
            "errors": []
        }
        
        # Trigger background streaming if client_id provided
        if client_id:
            background_tasks.add_task(stream_mock_data, client_id)
            
        return OrchestrationResponse(
            status="completed",
            message="MAMA-MIA cached data loaded.",
            result=result_payload
        )
        
    except Exception as e:
        logger.error(f"Failed to load mama-mia cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
