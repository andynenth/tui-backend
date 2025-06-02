# backend/api/routes/ws.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from backend.socket_manager import register, unregister, broadcast
# from backend.engine.room_manager import RoomManager # นำเข้า RoomManager
from backend.shared_instances import shared_room_manager
import asyncio

router = APIRouter()
# room_manager = RoomManager() # สร้าง instance
room_manager = shared_room_manager

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # ✅ รับ WebSocket object ที่ถูก register กลับมา
    registered_ws = await register(room_id, websocket) 

    try:
        while True:
            message = await websocket.receive_json()
            event_name = message.get("event")
            event_data = message.get("data", {})

            print(f"DEBUG_WS_RECEIVE: Received event '{event_name}' from client in room {room_id} with data: {event_data}")

            if event_name == "client_ready":
                # ไม่ต้องใช้ await asyncio.sleep(0) ตรงนี้แล้ว
                # เพราะการ clean up ใน socket_manager.py และ await register() น่าจะเพียงพอ

                room = room_manager.get_room(room_id)
                if room:
                    updated_summary = room.summary()
                    # ✅ ส่ง initial room state กลับไปหา registered_ws โดยตรง
                    await registered_ws.send_json({
                        "event": "room_state_update",
                        "data": {"slots": updated_summary["slots"], "host_name": updated_summary["host_name"]}
                    })
                    await asyncio.sleep(0) # Yield control หลังส่ง
                    print(f"DEBUG_WS_RECEIVE: Sent initial room state to client in room {room_id} after client_ready.")
                else:
                    print(f"DEBUG_WS_RECEIVE: Room {room_id} not found for client_ready event.")
                    await registered_ws.send_json({"event": "room_closed", "data": {"message": "Room not found."}})
                    await asyncio.sleep(0) # Yield control
            # ...
    except WebSocketDisconnect:
        unregister(room_id, websocket)
        print(f"DEBUG_WS_DISCONNECT: WebSocket client disconnected from room {room_id}.")
    except Exception as e:
        print(f"DEBUG_WS_ERROR: WebSocket error in room {room_id}: {e}")
        unregister(room_id, websocket)