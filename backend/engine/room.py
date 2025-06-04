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

    def get_occupied_slots(self) -> int:
        """
        Counts the number of occupied slots (by both human players and bots).
        Returns:
            int: The count of non-empty slots.
        """
        return sum(1 for player in self.players if player is not None)

    def get_total_slots(self) -> int:
        """
        Returns the total number of slots available in the room.
        Returns:
            int: The total number of player slots.
        """
        return len(self.players)

    def is_full(self) -> bool:
        """
        Checks if the room is completely full (all slots are occupied).
        Returns:
            bool: True if the room is full, False otherwise.
        """
        return self.get_occupied_slots() >= self.get_total_slots()

    def summary(self):
        """
        Generates a summary of the room's current state, suitable for sending to clients.
        Includes information about occupied and total slots.
        Returns:
            dict: A dictionary containing room_id, host_name, started status,
                  slot information, occupied slots count, and total slots count.
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
                "name": player.name, # Always use player.name, regardless of whether it's a bot or human.
                "is_bot": player.is_bot
            }

        return {
            "room_id": self.room_id,
            "host_name": self.host_name,
            "started": self.started,
            "slots": {
                # Create a dictionary mapping slot names (P1, P2, etc.) to their info.
                f"P{i+1}": slot_info(p) for i, p in enumerate(self.players)
            },
            "occupied_slots": self.get_occupied_slots(),  # ✅ Added occupied slots count.
            "total_slots": self.get_total_slots()         # ✅ Added total slots count.
        }

    def assign_slot(self, slot: int, name_or_none: Optional[str]):
        """
        Assigns a player (human or bot) or clears a slot.
        If a human player is assigned to a slot, and they were previously in another slot,
        their old slot is cleared.
        Args:
            slot (int): The 0-indexed slot number (0 to 3).
            name_or_none (Optional[str]): The name of the player/bot to assign, or None to clear the slot.
        Raises:
            ValueError: If the slot number is invalid.
        """
        if slot < 0 or slot > 3:
            raise ValueError("Invalid slot number") # Validate slot index.
        
        # If a human player is being assigned, check for duplicates and move them.
        if name_or_none and not (name_or_none.startswith("BOT_") or name_or_none.startswith("Bot")):
            # Check if this player is already in another slot in the room.
            for i, player in enumerate(self.players):
                if i != slot and player and player.name == name_or_none and not player.is_bot:
                    self.players[i] = None  # Clear the old slot if the player is found elsewhere.
                    break
        
        # Assign the new player/bot or clear the slot.
        if name_or_none is None:
            self.players[slot] = None # Clear the slot.
        elif name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
            self.players[slot] = Player(name_or_none, is_bot=True) # Assign a bot.
        else:
            self.players[slot] = Player(name_or_none, is_bot=False) # Assign a human player.

    def join_room(self, player_name: str) -> int:
        """
        Allows a player to join the room.
        Automatically assigns the player to the first available empty slot.
        If no empty slots, replaces the first available bot.
        Args:
            player_name (str): The name of the player attempting to join.
        Returns:
            int: The index of the slot the player joined.
        Raises:
            ValueError: If the player is already in the room or no available slots.
        """
        # 1. Check if the player with this name is already in the room.
        for i, player in enumerate(self.players):
            if player and player.name == player_name and not player.is_bot:
                raise ValueError(f"Player '{player_name}' is already in this room.")

        # 2. Find the first truly empty slot (None).
        for i, player in enumerate(self.players):
            if player is None:
                self.players[i] = Player(player_name, is_bot=False)
                return i
        
        # 3. If no empty slots, find the first bot slot to replace.
        for i, player in enumerate(self.players):
            if player and player.is_bot:
                self.players[i] = Player(player_name, is_bot=False)
                return i
        
        # If no suitable slot was found (all slots are filled by other human players).
        raise ValueError("No available slot (all slots are filled by human players).")


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
        
        # Find and remove the specific human player.
        for i, player in enumerate(self.players):
            if player and not player.is_bot and player.name == player_name:
                self.players[i] = None # Set the player's slot to None (empty).
                return False # Player exited, but not the host.
        
        return False  # Player not found or was a bot.

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
        Checks if a player will be kicked from a slot when a new assignment is made.
        Args:
            slot (int): The 0-indexed slot number being assigned to.
            new_assignment (Optional[str]): The name of the new player/bot, or None if clearing the slot.
        Returns:
            Optional[str]: The name of the player who would be kicked, or None if no one is kicked.
        """
        current = self.players[slot] # Get the current player/bot in the slot.
        
        # If the slot is currently empty or has a bot, no one is kicked.
        if not current or current.is_bot:
            return None
        
        # If a bot is being assigned to a slot currently held by a human player, that player is kicked.
        if new_assignment and (new_assignment.startswith("Bot") or new_assignment.startswith("BOT_")):
            return current.name
        
        # If a different human player is being assigned to a slot currently held by another human player,
        # the current player is kicked.
        if new_assignment and new_assignment != current.name:
            return current.name
        
        return None # No player is kicked in other scenarios.
