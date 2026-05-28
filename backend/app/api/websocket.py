from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

WS_MAX_CONNECTIONS = 100
WS_MAX_MESSAGE_BYTES = 4096


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= WS_MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Too many connections")
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

price_manager = ConnectionManager()
risk_manager = ConnectionManager()

@router.websocket("/ws/prices")
async def websocket_prices(
    websocket: WebSocket,
    token: str | None = Query(None),
    api_key: str | None = Query(None, alias="api_key"),
):
    if not token and not api_key:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connected = await price_manager.connect(websocket)
    if not connected:
        return
    try:
        while True:
            data = await websocket.receive_text()
            if len(data.encode()) > WS_MAX_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                break
            await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket prices error: {e}")
    finally:
        price_manager.disconnect(websocket)

@router.websocket("/ws/risk")
async def websocket_risk(
    websocket: WebSocket,
    token: str | None = Query(None),
    api_key: str | None = Query(None, alias="api_key"),
):
    if not token and not api_key:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connected = await risk_manager.connect(websocket)
    if not connected:
        return
    try:
        while True:
            data = await websocket.receive_text()
            if len(data.encode()) > WS_MAX_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                break
            await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket risk error: {e}")
    finally:
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


async def price_broadcaster():
    """Background task to broadcast price updates every 30 seconds."""
    while True:
        try:
            # Only run if there are connected clients
            if not price_manager.active_connections:
                await asyncio.sleep(30)
                continue

            from app.db.base import SessionLocal
            from app.data.models import DailyBar, Instrument
            from sqlalchemy import select

            db = SessionLocal()
            try:
                instruments = list(db.execute(select(Instrument)).scalars().all())
                for inst in instruments:
                    bars = list(
                        db.execute(
                            select(DailyBar)
                            .where(DailyBar.instrument_id == inst.id)
                            .order_by(DailyBar.trade_date.desc())
                            .limit(2)
                        ).scalars().all()
                    )

                    if bars and len(bars) >= 1:
                        latest = bars[0]
                        previous = bars[1] if len(bars) > 1 else None

                        change = 0.0
                        change_pct = 0.0
                        if previous and previous.close > 0:
                            change = latest.close - previous.close
                            change_pct = (change / previous.close) * 100

                        await broadcast_price_update(
                            symbol=inst.symbol,
                            price=latest.close,
                            change=round(change, 4),
                            change_pct=round(change_pct, 2),
                        )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Price broadcaster error: {e}")

        await asyncio.sleep(30)
