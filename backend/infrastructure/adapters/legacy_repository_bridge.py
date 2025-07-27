"""
Legacy Repository Bridge

This bridge synchronizes data between clean architecture repositories
and legacy managers during the transition period. This allows both
architectures to see the same data.

This is a TEMPORARY component that will be removed in Phase 7.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from infrastructure.dependencies import get_unit_of_work
from shared_instances import shared_room_manager
from domain.entities.room import Room as CleanRoom
from engine.game import Game as LegacyGame

logger = logging.getLogger(__name__)


class LegacyRepositoryBridge:
    """
    Bridge between clean architecture repositories and legacy managers.
    
    This component ensures data visibility across both architectures
    during the transition period.
    """
    
    def __init__(self):
        """Initialize the bridge."""
        self._sync_enabled = True
        self._sync_tasks = set()
    
    async def sync_room_to_legacy(self, room_id: str) -> None:
        """
        Sync a room from clean architecture to legacy manager.
        
        Args:
            room_id: The room ID to sync
        """
        if not self._sync_enabled:
            return
            
        try:
            # Get room from clean architecture
            uow = get_unit_of_work()
            async with uow:
                clean_room = await uow.rooms.get_by_id(room_id)
                
                if not clean_room:
                    logger.debug(f"Room {room_id} not found in clean architecture")
                    return
                
                # Convert to legacy format and add to legacy manager
                legacy_room = self._convert_to_legacy_room(clean_room)
                
                # Add to legacy manager if not exists
                if room_id not in shared_room_manager.rooms:
                    shared_room_manager.rooms[room_id] = legacy_room
                    logger.info(f"Synced room {room_id} to legacy manager")
                else:
                    # Update existing room
                    shared_room_manager.rooms[room_id] = legacy_room
                    logger.debug(f"Updated room {room_id} in legacy manager")
                    
        except Exception as e:
            logger.error(f"Error syncing room {room_id} to legacy: {e}")
    
    async def sync_room_from_legacy(self, room_id: str) -> None:
        """
        Sync a room from legacy manager to clean architecture.
        
        Args:
            room_id: The room ID to sync
        """
        if not self._sync_enabled:
            return
            
        try:
            # Get room from legacy manager
            legacy_room = await shared_room_manager.get_room(room_id)
            
            if not legacy_room:
                logger.debug(f"Room {room_id} not found in legacy manager")
                return
            
            # Convert to clean architecture format
            clean_room = self._convert_from_legacy_room(legacy_room)
            
            # Save to clean architecture
            uow = get_unit_of_work()
            async with uow:
                await uow.rooms.save(clean_room)
                await uow.commit()
                
            logger.info(f"Synced room {room_id} from legacy to clean architecture")
            
        except Exception as e:
            logger.error(f"Error syncing room {room_id} from legacy: {e}")
    
    def _convert_to_legacy_room(self, clean_room: CleanRoom) -> Any:
        """
        Convert clean architecture room to legacy format.
        
        Args:
            clean_room: Clean architecture room entity
            
        Returns:
            Legacy AsyncRoom object
        """
        from engine.async_room import AsyncRoom
        from engine.player import Player as LegacyPlayer
        
        # Create legacy room
        legacy_room = AsyncRoom(clean_room.room_id, clean_room.host_player_name)
        
        # Clear default players and add actual players
        legacy_room.players = [None, None, None, None]
        
        # Add players in their seat positions
        for player in clean_room.players:
            seat_pos = player.seat_position
            if seat_pos is not None and 0 <= seat_pos < 4:
                legacy_player = LegacyPlayer(
                    name=player.name,
                    is_bot=player.is_bot,
                    position=seat_pos
                )
                # Set connected status
                if hasattr(legacy_player, 'is_connected'):
                    legacy_player.is_connected = not player.is_bot
                    
                legacy_room.players[seat_pos] = legacy_player
        
        # Set room state
        legacy_room.started = clean_room.game_started
        
        # If game exists, create minimal game object
        if clean_room.current_game_id and clean_room.game_started:
            legacy_room.game = self._create_minimal_legacy_game(clean_room)
        
        return legacy_room
    
    def _convert_from_legacy_room(self, legacy_room: Any) -> CleanRoom:
        """
        Convert legacy room to clean architecture format.
        
        Args:
            legacy_room: Legacy room object
            
        Returns:
            Clean architecture room entity
        """
        # This would need proper implementation based on legacy room structure
        # For now, return a basic conversion
        raise NotImplementedError("Legacy to clean conversion not yet implemented")
    
    def _create_minimal_legacy_game(self, clean_room: CleanRoom) -> Optional[Any]:
        """
        Create a minimal legacy game object for compatibility.
        
        Args:
            clean_room: Clean architecture room
            
        Returns:
            Minimal legacy game object
        """
        # Create minimal game for legacy compatibility
        # This prevents "room.game is None" errors
        try:
            from engine.async_game import AsyncGame
            from engine.player import Player as LegacyPlayer
            
            # Convert players
            legacy_players = []
            for player in clean_room.players:
                if player.seat_position is not None:
                    legacy_player = LegacyPlayer(
                        name=player.name,
                        is_bot=player.is_bot,
                        position=player.seat_position
                    )
                    legacy_players.append(legacy_player)
            
            # Create minimal game (AsyncGame requires at least 4 players)
            while len(legacy_players) < 4:
                # Add bot players to fill slots
                bot_pos = len(legacy_players)
                bot_player = LegacyPlayer(
                    name=f"Bot {bot_pos + 1}",
                    is_bot=True,
                    position=bot_pos
                )
                legacy_players.append(bot_player)
            
            # Create game
            game = AsyncGame(legacy_players)
            game.game_id = clean_room.current_game_id
            
            return game
            
        except Exception as e:
            logger.error(f"Error creating minimal legacy game: {e}")
            return None
    
    async def start_background_sync(self) -> None:
        """Start background synchronization tasks."""
        # Could implement periodic sync or event-based sync here
        pass
    
    async def stop_background_sync(self) -> None:
        """Stop background synchronization tasks."""
        self._sync_enabled = False
        
        # Cancel any running sync tasks
        for task in self._sync_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._sync_tasks:
            await asyncio.gather(*self._sync_tasks, return_exceptions=True)
    
    @asynccontextmanager
    async def sync_context(self, room_id: str):
        """
        Context manager that ensures room is synced.
        
        Usage:
            async with bridge.sync_context(room_id):
                # Both architectures can see the room
                ...
        """
        # Sync to legacy before operation
        await self.sync_room_to_legacy(room_id)
        
        try:
            yield
        finally:
            # Could sync back if needed
            pass


# Global bridge instance
legacy_bridge = LegacyRepositoryBridge()


async def ensure_room_visible_to_legacy(room_id: str) -> None:
    """
    Convenience function to ensure a room is visible to legacy code.
    
    This should be called after creating a room in clean architecture
    to prevent "Room not found" warnings.
    """
    await legacy_bridge.sync_room_to_legacy(room_id)


async def sync_all_rooms() -> None:
    """
    Sync all rooms between architectures.
    
    This could be called at startup or periodically.
    """
    # Get all rooms from clean architecture
    uow = get_unit_of_work()
    async with uow:
        clean_rooms = await uow.rooms.list_active()
        
        for room in clean_rooms:
            await legacy_bridge.sync_room_to_legacy(room.room_id)
    
    logger.info(f"Synced {len(clean_rooms)} rooms to legacy manager")