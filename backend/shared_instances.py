# backend/shared_instances.py
from engine.room_manager import RoomManager

# สร้าง RoomManager instance เพียงครั้งเดียว และจะถูกแชร์ทั่วทั้งแอปพลิเคชัน
# นี่คือ RoomManager ที่จะเก็บข้อมูลห้องทั้งหมด
shared_room_manager = RoomManager()