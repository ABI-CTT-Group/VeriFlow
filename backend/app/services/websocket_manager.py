import logging
import json
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to clients.
    Maps client_id/run_id to active WebSocket connections.
    """
    def __init__(self):
        # Map client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Sends a JSON message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a message to all connected clients."""
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)

# Global instance
manager = WebSocketManager()
