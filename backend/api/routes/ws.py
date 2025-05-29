# backend/api/ws.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from backend.socket_manager import register, unregister

router = APIRouter()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await register(room_id, websocket)
    try:
        while True:
            await websocket.receive_text()
            # ไม่ต้องทำอะไรกับข้อความนี้ก็ได้
    except WebSocketDisconnect:
        unregister(room_id, websocket)
