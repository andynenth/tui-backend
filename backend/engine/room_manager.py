# backend/engine/room_manager.py

from typing import Dict
from engine.room import Room
import uuid

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(self, host_name: str) -> str:
        room_id = uuid.uuid4().hex[:6].upper()
        self.rooms[room_id] = Room(room_id, host_name)
        return room_id

    def get_room(self, room_id: str) -> Room:
        return self.rooms.get(room_id)

    def delete_room(self, room_id: str):
        if room_id in self.rooms:
            del self.rooms[room_id]

    def list_rooms(self):
        return [room.summary() for room in self.rooms.values() if not room.started]
