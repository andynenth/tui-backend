# backend/engine/room.py

from engine.game import Game # Import the Game class, representing the core game logic.
from engine.player import Player # Import the Player class, representing a player in the game.
from typing import Optional # Import Optional for type hinting variables that can be None.

class Room:
    """
    The Room class manages the state of a single game room, including players,
    game status, and provides methods for managing room participants.
    """
    def __init__(self, room_id: str, host_name: str):
        """
        Initializes a new game room.
        Args:
            room_id (str): The unique identifier for the room.
            host_name (str): The name of the player who created and hosts the room.
        """
        self.room_id = room_id # Unique ID of the room.
        self.host_name = host_name # Name of the room's host.
        # Initialize player slots. There are 4 slots (P1-P4), initially all None.
        self.players = [None, None, None, None]
        self.started = False # Boolean flag indicating if the game in this room has started.
        self.game: Optional[Game] = None # The Game instance associated with this room, initially None.

        # Assign the host to the first slot (P1).
        self.players[0] = Player(host_name, is_bot=False)

        # Assign bots to the remaining slots (P2-P4) by default.
        for i in range(1, 4):
            self.players[i] = Player(f"Bot {i+1}", is_bot=True)

    def summary(self):
        """
        Generates a summary of the room's current state, suitable for sending to clients.
        Returns:
            dict: A dictionary containing room_id, host_name, started status, and slot information.
        """
        def slot_info(player: Optional[Player]):
            """
            Helper function to get simplified information for a player slot.
            Args:
                player (Optional[Player]): The Player object or None if the slot is empty.
            Returns:
                dict or None: A dictionary with player name and bot status, or None if the slot is empty.
            """
            if player is None:
                return None # Return None if the slot is empty.
            return {
                # ✅ Always use player.name, regardless of whether it's a bot or human.
                "name": player.name,
                "is_bot": player.is_bot
            }

        return {
            "room_id": self.room_id,
            "host_name": self.host_name,
            "started": self.started,
            "slots": {
                # Create a dictionary mapping slot names (P1, P2, etc.) to their info.
                f"P{i+1}": slot_info(p) for i, p in enumerate(self.players)
            }
        }

    def assign_slot(self, slot: int, name_or_none: Optional[str]):
        """
        Assigns a player or clears a slot.
        Prevents duplicate players.
        """
        if slot < 0 or slot > 3:
            raise ValueError("Invalid slot number")
        
        # ถ้าจะ assign ผู้เล่น ต้องเช็คว่าไม่ซ้ำ
        if name_or_none and not (name_or_none.startswith("BOT_") or name_or_none.startswith("Bot")):
            # เช็คว่าผู้เล่นนี้อยู่ในห้องแล้วหรือไม่
            for i, player in enumerate(self.players):
                if i != slot and player and player.name == name_or_none and not player.is_bot:
                    # ถ้าอยู่แล้ว ให้ย้ายมาที่ slot ใหม่
                    self.players[i] = None  # Clear old slot
                    break
        
        # Assign ตามปกติ
        if name_or_none is None:
            self.players[slot] = None
        elif name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
            self.players[slot] = Player(name_or_none, is_bot=True)
        else:
            self.players[slot] = Player(name_or_none, is_bot=False)

    def join_room(self, player_name: str) -> int:
        """
        Allows a player to join the room.
        Automatically assigns to the first available slot.
        """
        # 1. ตรวจสอบว่าผู้เล่นอยู่ในห้องแล้วหรือไม่
        for i, player in enumerate(self.players):
            if player and player.name == player_name and not player.is_bot:
                raise ValueError(f"Player '{player_name}' is already in this room.")

        # 2. หาช่องว่างแรกสุด (ไม่ใช่หา bot slot)
        for i, player in enumerate(self.players):
            if player is None:
                self.players[i] = Player(player_name, is_bot=False)
                return i
        
        # 3. ถ้าไม่มีช่องว่าง ให้แทนที่ bot slot แรกที่เจอ
        for i, player in enumerate(self.players):
            if player and player.is_bot:
                self.players[i] = Player(player_name, is_bot=False)
                return i
        
        raise ValueError("No available slot (all slots are filled by human players).")


    def exit_room(self, player_name: str) -> bool:
        """
        Handles a player exiting the room.
        Returns True if the exiting player was the host.
        """
        if player_name == self.host_name:
            return True  # Host is leaving
        
        # Find and remove the player
        for i, player in enumerate(self.players):
            if player and not player.is_bot and player.name == player_name:
                self.players[i] = None
                return False
        
        return False  # Player not found

    def start_game(self):
        """
        Starts the game within the room.
        Initializes the Game instance and sets the room's started status.
        Raises:
            ValueError: If the game has already started or not all slots are filled.
        """
        if self.started:
            raise ValueError("Game already started") # Prevent starting a game that's already in progress.
        # Check if all slots are filled (either by a player or a bot).
        if any(p is None or (not p.is_bot and not p.name) for p in self.players):
            raise ValueError("All slots must be filled before starting")
        self.game = Game(self.players) # Create a new Game instance with the current players.
        self.started = True # Set the room's status to started.
        self.game.start_game() # Call the game's start_game method.

    def get_kicked_player(self, slot: int, new_assignment: Optional[str]) -> Optional[str]:
        """
        Check if a player will be kicked when assigning to a slot.
        Returns the name of the kicked player or None.
        """
        current = self.players[slot]
        
        # ถ้า slot ว่าง หรือมี bot อยู่ = ไม่มีใครถูกเตะ
        if not current or current.is_bot:
            return None
        
        # ถ้ากำลังจะใส่ bot หรือใส่คนอื่น = คนเดิมถูกเตะ
        if new_assignment and (new_assignment.startswith("Bot") or new_assignment.startswith("BOT_")):
            return current.name
        
        # ถ้าใส่คนอื่นที่ไม่ใช่ bot
        if new_assignment and new_assignment != current.name:
            return current.name
        
        return None