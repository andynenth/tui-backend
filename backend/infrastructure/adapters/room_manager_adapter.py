"""
Room manager adapter that provides legacy-compatible interface using shared instances.
This allows gradual migration from shared_instances to clean architecture.

This is a temporary compatibility layer for Phase 7 migration.
Once all legacy code is removed, this adapter will also be removed.
"""

from typing import Optional, List, Dict, Any
import logging

# Import the legacy shared instance
from shared_instances import shared_room_manager

logger = logging.getLogger(__name__)


async def get_room(room_id: str) -> Optional[Any]:
    """
    Legacy-compatible get_room function using shared room manager.
    
    Args:
        room_id: The ID of the room to retrieve
        
    Returns:
        Room object if found, None otherwise
    """
    try:
        room = await shared_room_manager.get_room(room_id)
        if room:
            logger.debug(f"[ROOM_ADAPTER] Retrieved room {room_id}")
        else:
            logger.debug(f"[ROOM_ADAPTER] Room {room_id} not found")
        return room
    except Exception as e:
        logger.error(f"[ROOM_ADAPTER] Error getting room {room_id}: {e}")
        return None


async def delete_room(room_id: str) -> bool:
    """
    Legacy-compatible delete_room function using shared room manager.
    
    Args:
        room_id: The ID of the room to delete
        
    Returns:
        True if room was deleted, False otherwise
    """
    try:
        await shared_room_manager.delete_room(room_id)
        logger.info(f"[ROOM_ADAPTER] Deleted room {room_id}")
        return True
    except Exception as e:
        logger.error(f"[ROOM_ADAPTER] Error deleting room {room_id}: {e}")
        return False


async def list_rooms() -> List[Dict[str, Any]]:
    """
    Legacy-compatible list_rooms function using shared room manager.
    
    Returns:
        List of room summaries for available (non-started) rooms
    """
    try:
        rooms = await shared_room_manager.list_rooms()
        logger.debug(f"[ROOM_ADAPTER] Listed {len(rooms)} available rooms")
        return rooms
    except Exception as e:
        logger.error(f"[ROOM_ADAPTER] Error listing rooms: {e}")
        return []


def get_rooms_dict() -> Dict[str, Any]:
    """
    Get the raw rooms dictionary for cleanup task access.
    This is a synchronous function as it accesses the internal dictionary.
    
    Returns:
        Dictionary of all rooms (both started and non-started)
    """
    try:
        # Access the internal rooms dictionary
        rooms_dict = shared_room_manager.rooms
        logger.debug(f"[ROOM_ADAPTER] Accessed rooms dict with {len(rooms_dict)} rooms")
        return rooms_dict
    except Exception as e:
        logger.error(f"[ROOM_ADAPTER] Error accessing rooms dict: {e}")
        return {}


# Re-export the room manager instance for direct access if needed
# This is for compatibility with code that needs the full object
room_manager = shared_room_manager