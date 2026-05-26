import logging
from typing import List, Any

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.connections: List[Any] = []
    
    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"WebSocket connected: {len(self.connections)} total")
    
    def disconnect(self, websocket):
        self.connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {len(self.connections)} total")
    
    async def broadcast(self, message: dict):
        for conn in self.connections:
            try:
                await conn.send_json(message)
            except:
                pass
