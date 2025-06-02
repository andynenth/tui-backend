# backend/socket_manager.py
from fastapi.websockets import WebSocket
from typing import Dict, List, Optional
import asyncio
import weakref

room_connections: Dict[str, List[weakref.ReferenceType[WebSocket]]] = {}


# ✅ เพิ่ม Queue สำหรับการ Broadcast Message (เพื่อแก้ปัญหา Race Condition)
# Dict[room_id, asyncio.Queue]
broadcast_queues: Dict[str, asyncio.Queue] = {}

# ✅ เพิ่ม Task สำหรับจัดการ Broadcast Queue แต่ละห้อง
broadcast_tasks: Dict[str, asyncio.Task] = {}


async def _process_broadcast_queue(room_id: str):
    """Background task to process messages from the broadcast queue for a specific room."""
    queue = broadcast_queues[room_id]
    print(f"DEBUG_WS: Starting broadcast queue processor for room {room_id}.")
    while True:
        message = await queue.get() # รอรับ message จาก queue
        event = message["event"]
        data = message["data"]

        # กรอง connections ที่ยัง active (ref() ไม่ใช่ None) และอยู่ในสถานะ OPEN (client_state.value == 1)
        active_and_open_websockets: List[WebSocket] = []
        # ทำความสะอาด room_connections ก่อนที่จะพยายามส่ง
        if room_id in room_connections:
            room_connections[room_id] = [
                ref for ref in room_connections[room_id]
                if ref() is not None and ref().client_state.value == 1 # 1 = State.OPEN
            ]
            for ws_ref in room_connections[room_id]:
                ws = ws_ref()
                if ws is not None: # ควรจะเป็น None น้อยมากหลังการกรองด้านบน
                    active_and_open_websockets.append(ws)

        if not active_and_open_websockets:
            print(f"DEBUG_WS: No active (open) connections found for room {room_id} during queue processing. Skipping message.")
            # ถ้าไม่มี connection ที่ active เลย อาจจะลบ queue และ task ออก
            if room_id in broadcast_queues:
                del broadcast_queues[room_id]
            if room_id in broadcast_tasks:
                broadcast_tasks[room_id].cancel()
                del broadcast_tasks[room_id]
            continue # ข้ามไปรอ message ถัดไป

        print(f"DEBUG_WS: Queue processor broadcasting event '{event}' to {len(active_and_open_websockets)} clients in room {room_id}.")

        for ws in active_and_open_websockets:
            try:
                # ส่ง message
                await ws.send_json({"event": event, "data": data})
                await asyncio.sleep(0) # Yield control
                print(f"DEBUG_WS: Successfully sent to a client in room {room_id} (WS state: {ws.client_state.name}).")
            except Exception as e:
                print(f"DEBUG_WS: Error sending to client in room {room_id}: {e}. Unregistering connection.")
                unregister(room_id, ws) # ให้ unregister จัดการการ remove

        # หลังจากการ broadcast ในลูป, ทำความสะอาด list อีกครั้ง (สำหรับ connection ที่อาจจะเสียไปในลูป)
        if room_id in room_connections:
            room_connections[room_id] = [
                ref for ref in room_connections[room_id]
                if ref() is not None and ref().client_state.value == 1
            ]
            if not room_connections[room_id]:
                del room_connections[room_id]


async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    await websocket.accept()
    
    # ตรวจสอบว่ามี queue สำหรับห้องนี้แล้วหรือยัง
    if room_id not in broadcast_queues:
        broadcast_queues[room_id] = asyncio.Queue()
        # เริ่มต้น background task สำหรับ broadcast queue
        broadcast_tasks[room_id] = asyncio.create_task(_process_broadcast_queue(room_id))
        print(f"DEBUG_WS: Created new broadcast queue and task for room {room_id}.")

    # ✅ ทำความสะอาด connections ที่เสียก่อนจะเพิ่มใหม่และนับ
    room_connections[room_id] = [
        ref for ref in room_connections.get(room_id, [])
        if ref() is not None and ref().client_state.value == 1 # Filter for open connections
    ]
    
    ws_ref = weakref.ref(websocket)
    if ws_ref not in room_connections[room_id]:
        room_connections[room_id].append(ws_ref)
        print(f"DEBUG_WS: Registered new connection for room {room_id}. Total active connections: {len(room_connections[room_id])}")
    else:
        print(f"DEBUG_WS: WebSocket already registered for room {room_id}. Skipping.")
    
    return websocket

def unregister(room_id: str, websocket: WebSocket):
    if room_id in room_connections:
        room_connections[room_id] = [
            ref for ref in room_connections[room_id]
            if ref() is not None and ref() is not websocket # check if object is not None and not the one to unregister
        ]
        
        print(f"DEBUG_WS: Unregistered connection for room {room_id}. Remaining active connections: {len(room_connections[room_id])}")
        
        if not room_connections[room_id]: # Clean up empty room lists
            del room_connections[room_id]
            # ถ้าไม่มี connection เหลือแล้ว ให้ยกเลิก broadcast queue และ task ด้วย
            if room_id in broadcast_queues:
                broadcast_tasks[room_id].cancel()
                del broadcast_tasks[room_id]
                del broadcast_queues[room_id]
                print(f"DEBUG_WS: Cleaned up broadcast queue and task for room {room_id} (no active connections).")
    else:
        print(f"DEBUG_WS: Attempted to unregister from non-existent room {room_id}")

# ✅ broadcast function จะใส่ message ลงใน queue แทนที่จะส่งโดยตรง
async def broadcast(room_id: str, event: str, data: dict):
    if room_id not in broadcast_queues:
        print(f"DEBUG_WS: Broadcast queue not found for room {room_id}. Cannot broadcast.")
        return # หรือ raise error ถ้าต้องการให้การ broadcast ต้องมี queue เสมอ
    
    await broadcast_queues[room_id].put({"event": event, "data": data})
    print(f"DEBUG_WS: Message for event '{event}' added to queue for room {room_id}.")
