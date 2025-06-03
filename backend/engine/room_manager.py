# backend/engine/room_manager.py

from typing import Dict # Import Dict for type hinting dictionaries.
from engine.room import Room # Import the Room class, which represents a single game room.
import uuid # Import the uuid module for generating unique identifiers.

class RoomManager:
    """
    The RoomManager class is responsible for managing all active game rooms.
    It provides functionalities to create, retrieve, delete, and list rooms.
    """
    def __init__(self):
        """
        Initializes the RoomManager.
        Attributes:
            rooms (Dict[str, Room]): A dictionary to store Room objects,
                                     where keys are room IDs (strings) and values are Room instances.
        """
        self.rooms: Dict[str, Room] = {}

    def create_room(self, host_name: str) -> str:
        """
        Creates a new game room.
        Generates a unique 6-character uppercase hexadecimal room ID.
        Args:
            host_name (str): The name of the player who will be the host of the new room.
        Returns:
            str: The ID of the newly created room.
        """
        # Generate a unique 16-character hexadecimal string, then take the first 6 characters and convert to uppercase.
        room_id = uuid.uuid4().hex[:6].upper()
        # Create a new Room instance and store it in the rooms dictionary.
        self.rooms[room_id] = Room(room_id, host_name)
        return room_id

    def get_room(self, room_id: str) -> Room:
        """
        Retrieves a Room object by its ID.
        Args:
            room_id (str): The ID of the room to retrieve.
        Returns:
            Room: The Room object if found, otherwise None.
        """
        return self.rooms.get(room_id) # Use .get() to safely retrieve, returning None if key not found.

    def delete_room(self, room_id: str):
        """
        Deletes a room from the manager.
        Args:
            room_id (str): The ID of the room to delete.
        """
        if room_id in self.rooms:
            del self.rooms[room_id] # Remove the room from the dictionary if it exists.

    def list_rooms(self):
        """
        Lists all available rooms that have not yet started a game.
        Returns:
            list: A list of summaries for rooms that are not yet started.
                  Each summary is typically a dictionary containing room details.
        """
        # Iterate through all room values and filter for rooms where 'started' attribute is False.
        # Then, return the summary of each filtered room.
        return [room.summary() for room in self.rooms.values() if not room.started]
