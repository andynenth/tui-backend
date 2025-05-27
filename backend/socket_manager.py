# backend/socket_manager.py
from fastapi.websockets import WebSocket
from typing import Dict, List

room_connections: Dict[str, List[WebSocket]] = {}

async def register(room_id: str, websocket: WebSocket):
    await websocket.accept()
    room_connections.setdefault(room_id, []).append(websocket)

def unregister(room_id: str, websocket: WebSocket):
    room_connections[room_id].remove(websocket)

async def broadcast(room_id: str, event: str, data: dict):
    for ws in list(room_connections.get(room_id, [])):
        try:
            await ws.send_json({"event": event, "data": data})
        except:
            # Remove dead connections
            unregister(room_id, ws)
