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
            Lists all available rooms with complete information.
            This method iterates through all rooms and includes only those that have not started.
            For each available room, it provides a detailed summary including slot occupancy.
            Returns:
                list: A list of dictionaries, where each dictionary is a summary of an available room.
            """
            available_rooms = [] # Initialize an empty list to store summaries of available rooms.
            
            # Iterate through all room objects currently managed.
            for room in self.rooms.values():
                # Only include rooms that have not yet started a game.
                if not room.started:
                    summary = room.summary() # Get the detailed summary of the room.
                    # ✅ Ensure that 'occupied_slots' and 'total_slots' data are present in the summary.
                    # These fields are expected to be added by the Room.summary() method.
                    available_rooms.append(summary) # Add the room's summary to the list.
            
            return available_rooms # Return the list of available room summaries.
