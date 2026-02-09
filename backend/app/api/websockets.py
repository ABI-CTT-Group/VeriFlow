from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.config import config
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def _get_agent_response(agent_name: str, user_content: str) -> str:
    """
    Generates a response from the specified agent using Gemini.
    """
    try:
        # Resolve model and prompt version
        agent_conf = config.get_agent_config(agent_name)
        model_alias = agent_conf.get("default_model", "gemini-2.0-flash")
        model_name = config.get_model_params(model_alias).get("api_model_name", model_alias)
        prompt_version = agent_conf.get("default_prompt_version", "v1_standard")

        # Get System Prompt
        # Use _chat suffix for conversational interactions
        system_prompt_key = f"{agent_name}_chat"
        try:
            system_prompt = prompt_manager.get_prompt(system_prompt_key, version=prompt_version)
        except Exception:
            # Fallback to standard system prompt or generic message
            try:
                system_prompt = prompt_manager.get_prompt(f"{agent_name}_system", version=prompt_version)
            except Exception:
                system_prompt = f"You are the {agent_name.capitalize()} Agent in the VeriFlow system. Assist the user with their queries."

        # Construct Prompt
        full_prompt = f"{system_prompt}\n\nUser: {user_content}"
        
        # Call Gemini
        client = GeminiClient()
        response = await client.generate_content(
            prompt=full_prompt,
            model=model_name
        )
        
        # Extract text result
        result = response.get("result", "")
        if isinstance(result, dict):
            return json.dumps(result)
        return str(result)

    except Exception as e:
        logger.error(f"Error getting response from {agent_name}: {e}")
        return f"I'm sorry, I encountered an error: {str(e)}"

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Receive text data
            data = await websocket.receive_text()
            
            try:
                # Parse JSON
                message = json.loads(data)
                
                # Handle User Message
                if message.get("type") == "user_message":
                    content = message.get("content", "")
                    agent = message.get("agent", "system")
                    
                    # Notify user that agent is thinking
                    await manager.send_message(client_id, {
                        "type": "status_update",
                        "status": "info",
                        "message": f"{agent.capitalize()} Agent: Thinking..."
                    })

                    # Get actual response from Agent
                    if agent.lower() == "system":
                        response_text = f"System: Received '{content}'"
                    else:
                        response_text = await _get_agent_response(agent.lower(), content)
                    
                    # Send response back
                    await manager.send_message(client_id, {
                        "type": "status_update",
                        "status": "info",
                        "message": f"{agent.capitalize()} Agent: {response_text}"
                    })
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
