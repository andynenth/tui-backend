# backend/engine/room.py
from engine.game import Game
from engine.player import Player
from typing import Optional

class Room:
    def __init__(self, room_id: str, host_name: str):
        self.room_id = room_id
        self.host_name = host_name
        self.players = [None, None, None, None]  # Slots P1–P4
        self.player_names = {}
        self.started = False
        self.game: Optional[Game] = None

    def assign_slot(self, slot: int, player_name: str):
        if self.players[slot] is not None:
            raise ValueError("Slot already taken")
        self.players[slot] = Player(player_name, is_bot=False)
        self.player_names[player_name] = slot

    def set_bot(self, slot: int):
        self.players[slot] = Player(f"BOT_{slot+1}", is_bot=True)

    def start_game(self):
        if self.started:
            raise ValueError("Game already started")
        if not all(self.players):
            raise ValueError("Not all slots are filled")
        self.game = Game(self.players)
        self.started = True
        self.game.start_game()

    def summary(self):
        return {
            "room_id": self.room_id,
            "host": self.host_name,
            "slots": [
                player.name if player else "OPEN"
                for player in self.players
            ],
            "started": self.started,
        }
