# backend/engine/room.py

from engine.game import Game
from engine.player import Player
from typing import Optional

class Room:
    def __init__(self, room_id: str, host_name: str):
        self.room_id = room_id
        self.host_name = host_name
        self.players = [None, None, None, None]  # Slots P1–P4
        self.started = False
        self.game: Optional[Game] = None

        # Assign host to P1
        self.players[0] = Player(host_name, is_bot=False)

        # Assign bots to P2–P4
        for i in range(1, 4):
            self.players[i] = Player(f"Bot {i+1}", is_bot=True)

    def summary(self):
        def slot_info(player: Optional[Player]):
            if player is None:
                return None
            return {
                # ✅ ต้องเป็น player.name เสมอ ไม่ว่าจะเป็นบอทหรือไม่
                "name": player.name,
                "is_bot": player.is_bot
            }

        return {
            "room_id": self.room_id,
            "host_name": self.host_name,
            "started": self.started,
            "slots": {
                f"P{i+1}": slot_info(p) for i, p in enumerate(self.players)
            }
        }

    def assign_slot(self, slot: int, name_or_none: Optional[str]):
        if slot < 0 or slot > 3:
            raise ValueError("Invalid slot number")

        if name_or_none is None:
            # Remove player or bot → make slot empty
            self.players[slot] = None
        elif name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
            # Replace with bot
            self.players[slot] = Player(name_or_none, is_bot=True)
        else:
            # Replace with human player
            self.players[slot] = Player(name_or_none, is_bot=False)

    def join_room(self, player_name: str) -> int:
        # 1. ตรวจสอบว่าผู้เล่นชื่อนี้อยู่ในห้องแล้วหรือไม่ (ป้องกันการ Join ซ้ำ)
        for i, player in enumerate(self.players):
            if player and player.name == player_name and not player.is_bot:
                raise ValueError(f"Player '{player_name}' is already in this room.")

        # 2. หา slot ที่ว่างจริงๆ (None) หรือ slot ที่เป็น Bot
        found_slot_index = -1
        # ลองหาสล็อตว่างก่อน
        for i, player in enumerate(self.players):
            if player is None: # ช่องว่างจริงๆ
                found_slot_index = i
                break
        
        # ถ้าไม่มีช่องว่างจริง ให้หาช่องที่เป็น Bot แทน
        if found_slot_index == -1:
            for i, player in enumerate(self.players):
                if player and player.is_bot: # ช่องที่เป็น Bot
                    found_slot_index = i
                    break # เลือก Bot ตัวแรกที่เจอ

        if found_slot_index != -1:
            self.players[found_slot_index] = Player(player_name, is_bot=False)
            return found_slot_index
        
        # ถ้าหาไม่เจอเลย (ห้องเต็มไปด้วยผู้เล่นคนอื่น)
        raise ValueError("No available slot (all slots are filled by human players or cannot be replaced).")


    def exit_room(self, player_name: str) -> bool:
        if player_name == self.host_name:
            return True  # host → remove entire room
        for i, player in enumerate(self.players):
            if player and not player.is_bot and player.name == player_name:
                self.players[i] = None
                return False
        return False

    def start_game(self):
        if self.started:
            raise ValueError("Game already started")
        if any(p is None or (not p.is_bot and not p.name) for p in self.players):
            raise ValueError("All slots must be filled before starting")
        self.game = Game(self.players)
        self.started = True
        self.game.start_game()
