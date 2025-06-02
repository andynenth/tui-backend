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
            self.players[i] = Player(f"Bot {i}", is_bot=True)

    def summary(self):
        def slot_info(player: Optional[Player]):
            if player is None:
                return None
            return {
                "name": None if player.is_bot else player.name,
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

        current = self.players[slot]

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
        for i, player in enumerate(self.players):
            if player is None:
                self.players[i] = Player(player_name, is_bot=False)
                return i
            if player.is_bot:
                continue
        raise ValueError("No empty slot available")

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
