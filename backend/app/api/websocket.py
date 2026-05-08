from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

price_manager = ConnectionManager()
risk_manager = ConnectionManager()

@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await price_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        price_manager.disconnect(websocket)

@router.websocket("/ws/risk")
async def websocket_risk(websocket: WebSocket):
    await risk_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        risk_manager.disconnect(websocket)

async def broadcast_price_update(symbol: str, price: float, change: float, change_pct: float):
    await price_manager.broadcast({
        "type": "PRICE_UPDATE",
        "data": {
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_pct": change_pct
        }
    })

async def broadcast_risk_change(old_state: str, new_state: str, reason: str):
    await risk_manager.broadcast({
        "type": "RISK_STATE_CHANGE",
        "data": {
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason
        }
    })
