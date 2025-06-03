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
        Assigns a player (human or bot) or clears a slot.
        Args:
            slot (int): The 0-indexed slot number (0 to 3).
            name_or_none (Optional[str]): The name of the player/bot to assign, or None to clear the slot.
        Raises:
            ValueError: If the slot number is invalid.
        """
        if slot < 0 or slot > 3:
            raise ValueError("Invalid slot number") # Validate slot index.

        if name_or_none is None:
            # If name_or_none is None, clear the slot.
            self.players[slot] = None
        elif name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
            # If the name starts with "BOT_" or "Bot", assign a bot.
            self.players[slot] = Player(name_or_none, is_bot=True)
        else:
            # Otherwise, assign a human player.
            self.players[slot] = Player(name_or_none, is_bot=False)

    def join_room(self, player_name: str) -> int:
        """
        Allows a player to join the room.
        A player can join an empty slot or replace a bot.
        Args:
            player_name (str): The name of the player attempting to join.
        Returns:
            int: The index of the slot the player joined.
        Raises:
            ValueError: If the player is already in the room or no available slots.
        """
        # 1. Check if the player with this name is already in the room (prevent duplicate joins).
        for i, player in enumerate(self.players):
            if player and player.name == player_name and not player.is_bot:
                raise ValueError(f"Player '{player_name}' is already in this room.")

        # 2. Find an available slot: prioritize truly empty slots (None), then bot slots.
        found_slot_index = -1
        # First, try to find a truly empty slot.
        for i, player in enumerate(self.players):
            if player is None: # Found an empty slot.
                found_slot_index = i
                break
        
        # If no empty slot was found, try to find a bot slot to replace.
        if found_slot_index == -1:
            for i, player in enumerate(self.players):
                if player and player.is_bot: # Found a bot slot.
                    found_slot_index = i
                    break # Select the first bot found.

        if found_slot_index != -1:
            # Assign the human player to the found slot.
            self.players[found_slot_index] = Player(player_name, is_bot=False)
            return found_slot_index
        
        # If no suitable slot was found (all slots are filled by other human players).
        raise ValueError("No available slot (all slots are filled by human players or cannot be replaced).")


    def exit_room(self, player_name: str) -> bool:
        """
        Handles a player exiting the room.
        If the host exits, the room should be considered for deletion.
        Args:
            player_name (str): The name of the player exiting.
        Returns:
            bool: True if the exiting player was the host, False otherwise.
        """
        if player_name == self.host_name:
            return True  # If the host exits, signal to remove the entire room.
        for i, player in enumerate(self.players):
            if player and not player.is_bot and player.name == player_name:
                self.players[i] = None # Set the player's slot to None (empty).
                return False # Player exited, but not the host.
        return False # Player not found or was a bot.

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
