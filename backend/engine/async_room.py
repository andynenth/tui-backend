# backend/engine/async_room.py
"""
Async implementation of Room for Phase 2 migration.
This will eventually replace the sync Room class.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

from .player import Player
from .game import Game
from .state_machine.core import GamePhase
from .state_machine.game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class AsyncRoom:
    """
    Async version of Room class.
    Manages the state of a single game room with async operations.
    """
    
    def __init__(self, room_id: str, host_name: str):
        """
        Initialize an async game room.
        
        Args:
            room_id: Unique identifier for the room
            host_name: Name of the player who created and hosts the room
        """
        self.room_id = room_id
        self.host_name = host_name
        self.players: List[Optional[Player]] = [None, None, None, None]
        self.started = False
        self.game: Optional[Game] = None
        self.game_state_machine: Optional[GameStateMachine] = None
        
        # Async locks for thread safety
        self._join_lock = asyncio.Lock()
        self._assign_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._start_lock = asyncio.Lock()
        
        # Operation tracking
        self._pending_operations = set()
        self._last_operation_id = 0
        
        # Stats
        self._created_at = datetime.now()
        self._last_activity = datetime.now()
        self._total_joins = 0
        self._total_exits = 0
        
        # Initialize with host
        self.players[0] = Player(
            host_name, 
            is_bot=False, 
            available_colors=self._get_available_colors()
        )
        
        # Fill remaining slots with bots
        for i in range(1, 4):
            self.players[i] = Player(f"Bot {i+1}", is_bot=True)
        
        logger.info(f"AsyncRoom {room_id} created with host {host_name}")
    
    async def join_room(self, player_name: str) -> int:
        """
        Allow a player to join the room asynchronously.
        
        Args:
            player_name: Name of the player attempting to join
            
        Returns:
            int: The slot index the player joined
            
        Raises:
            ValueError: If no slot available
            
        Future: Will persist join to database
        """
        async with self._join_lock:
            self._last_activity = datetime.now()
            
            # Check if game already started
            if self.started:
                raise ValueError("Cannot join: game already started")
            
            # Find first empty slot
            for i, player in enumerate(self.players):
                if player is None:
                    self.players[i] = Player(
                        player_name,
                        is_bot=False,
                        available_colors=self._get_available_colors()
                    )
                    self._total_joins += 1
                    
                    logger.info(f"Player {player_name} joined room {self.room_id} in slot {i}")
                    
                    # Future: await self._persist_player_join(player_name, i)
                    
                    return i
            
            # No empty slots, try to replace a bot
            for i, player in enumerate(self.players):
                if player and player.is_bot:
                    old_bot = player.name
                    self.players[i] = Player(
                        player_name,
                        is_bot=False,
                        available_colors=self._get_available_colors()
                    )
                    self._total_joins += 1
                    
                    logger.info(
                        f"Player {player_name} joined room {self.room_id} in slot {i}, "
                        f"replacing {old_bot}"
                    )
                    
                    # Future: await self._persist_player_join(player_name, i)
                    
                    return i
            
            raise ValueError("No available slot (all slots are filled by human players).")
    
    async def exit_room(self, player_name: str) -> bool:
        """
        Handle a player exiting the room asynchronously.
        
        Args:
            player_name: Name of the player exiting
            
        Returns:
            bool: True if the exiting player was the host
            
        Future: Will persist exit to database
        """
        async with self._state_lock:
            self._last_activity = datetime.now()
            
            logger.info(f"Player {player_name} exiting room {self.room_id}")
            
            # Check if host is exiting
            if player_name == self.host_name:
                logger.info(f"Host {player_name} exiting - room will be deleted")
                # Future: await self._persist_host_exit()
                return True
            
            # Find and remove the player
            for i, player in enumerate(self.players):
                if player and not player.is_bot and player.name == player_name:
                    self.players[i] = None
                    self._total_exits += 1
                    
                    logger.info(f"Player {player_name} removed from slot {i}")
                    
                    # Future: await self._persist_player_exit(player_name, i)
                    
                    return False
            
            logger.warning(f"Player {player_name} not found in room {self.room_id}")
            return False
    
    async def assign_slot(self, slot: int, name_or_none: Optional[str]) -> None:
        """
        Assign a player or bot to a specific slot asynchronously.
        
        Args:
            slot: The slot index (0-3)
            name_or_none: Player/bot name or None to clear slot
            
        Raises:
            ValueError: If slot number is invalid
            
        Future: Will persist slot assignment to database
        """
        if slot < 0 or slot > 3:
            raise ValueError(f"Invalid slot number: {slot}")
        
        async with self._assign_lock:
            self._last_activity = datetime.now()
            
            # Handle clearing slot
            if name_or_none is None:
                old_player = self.players[slot]
                self.players[slot] = None
                logger.info(f"Cleared slot {slot} in room {self.room_id}")
                
                # Future: await self._persist_slot_clear(slot)
                return
            
            # Handle human player assignment
            if not (name_or_none.startswith("BOT_") or name_or_none.startswith("Bot")):
                # Check for existing player in another slot
                for i, player in enumerate(self.players):
                    if (i != slot and player and 
                        player.name == name_or_none and not player.is_bot):
                        self.players[i] = None
                        logger.info(
                            f"Moved player {name_or_none} from slot {i} to {slot}"
                        )
                        break
            
            # Assign the player/bot
            if name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
                self.players[slot] = Player(name_or_none, is_bot=True)
            else:
                self.players[slot] = Player(
                    name_or_none,
                    is_bot=False,
                    available_colors=self._get_available_colors()
                )
            
            logger.info(f"Assigned {name_or_none} to slot {slot} in room {self.room_id}")
            
            # Future: await self._persist_slot_assignment(slot, name_or_none)
    
    async def start_game(self, broadcast_callback: Callable) -> Dict[str, Any]:
        """
        Start the game within the room asynchronously.
        
        Args:
            broadcast_callback: Async callback for broadcasting game events
            
        Returns:
            Dict containing operation result
            
        Raises:
            ValueError: If game already started or slots empty
            
        Future: Will persist game start to database
        """
        operation_id = self._generate_operation_id()
        
        try:
            self._pending_operations.add(operation_id)
            
            async with self._start_lock:
                if self.started:
                    raise ValueError("Game already started")
                
                # Validate all slots filled
                empty_slots = [i for i, p in enumerate(self.players) if p is None]
                if empty_slots:
                    raise ValueError(
                        f"Cannot start game: slots {empty_slots} are empty. "
                        f"All slots must be filled."
                    )
                
                # Create game instance
                self.game = Game(self.players)
                self.game.start_time = time.time()
                
                # Initialize state machine
                self.game_state_machine = GameStateMachine(
                    self.game, broadcast_callback
                )
                self.game_state_machine.room_id = self.room_id
                
                # Register with bot manager
                from backend.engine.bot_manager import BotManager
                bot_manager = BotManager()
                bot_manager.register_game(
                    self.room_id, self.game, self.game_state_machine
                )
                
                # Start the game
                await self.game_state_machine.start(GamePhase.PREPARATION)
                
                self.started = True
                self._last_activity = datetime.now()
                
                logger.info(f"Game started in room {self.room_id}")
                
                # Future: await self._persist_game_start()
                
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "game_created": True,
                    "state_machine_initialized": True,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
        except Exception as e:
            logger.error(f"Failed to start game in room {self.room_id}: {e}")
            raise
        finally:
            self._pending_operations.discard(operation_id)
    
    async def summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the room's current state asynchronously.
        
        Returns:
            Dict containing room summary
        """
        async with self._state_lock:
            def slot_info(player: Optional[Player], slot_index: int):
                if player is None:
                    return None
                return {
                    "name": player.name,
                    "is_bot": player.is_bot,
                    "is_host": player.name == self.host_name,
                    "avatar_color": getattr(player, "avatar_color", None)
                }
            
            return {
                "room_id": self.room_id,
                "host_name": self.host_name,
                "started": self.started,
                "slots": {
                    f"P{i+1}": slot_info(p, i)
                    for i, p in enumerate(self.players)
                },
                "players": [
                    slot_info(p, i) for i, p in enumerate(self.players)
                ],
                "occupied_slots": self.get_occupied_slots(),
                "total_slots": self.get_total_slots(),
                "created_at": self._created_at.isoformat(),
                "last_activity": self._last_activity.isoformat()
            }
    
    async def migrate_host(self) -> Optional[str]:
        """
        Migrate host privileges to the next suitable player asynchronously.
        
        Returns:
            Optional[str]: Name of new host, or None if no suitable host
            
        Future: Will persist host migration to database
        """
        async with self._state_lock:
            # Try to find a human player who isn't current host
            for player in self.players:
                if player and not player.is_bot and player.name != self.host_name:
                    old_host = self.host_name
                    self.host_name = player.name
                    
                    logger.info(
                        f"Host migrated from {old_host} to {self.host_name} "
                        f"in room {self.room_id}"
                    )
                    
                    # Future: await self._persist_host_migration(old_host, self.host_name)
                    
                    return self.host_name
            
            # If no human players, select first bot
            for player in self.players:
                if player and player.is_bot:
                    old_host = self.host_name
                    self.host_name = player.name
                    
                    logger.info(
                        f"Host migrated from {old_host} to bot {self.host_name} "
                        f"in room {self.room_id}"
                    )
                    
                    # Future: await self._persist_host_migration(old_host, self.host_name)
                    
                    return self.host_name
            
            logger.warning(f"No suitable host found for migration in room {self.room_id}")
            return None
    
    async def is_empty(self) -> bool:
        """Check if room has no human players."""
        return all(p is None or p.is_bot for p in self.players)
    
    async def cleanup(self) -> None:
        """Clean up room resources."""
        logger.info(f"Cleaning up room {self.room_id}")
        
        # Cancel any pending operations
        self._pending_operations.clear()
        
        # Future: Persist final room state
        # await self._persist_room_cleanup()
    
    # Helper methods (sync, don't need async)
    def get_occupied_slots(self) -> int:
        """Count occupied slots."""
        return sum(1 for player in self.players if player is not None)
    
    def get_total_slots(self) -> int:
        """Get total number of slots."""
        return len(self.players)
    
    def is_full(self) -> bool:
        """Check if room is full."""
        return self.get_occupied_slots() >= self.get_total_slots()
    
    def is_host(self, player_name: str) -> bool:
        """Check if player is the host."""
        return self.host_name == player_name
    
    def _get_available_colors(self) -> List[str]:
        """Get list of available avatar colors."""
        all_colors = ["blue", "purple", "orange", "red", "green", "teal", "pink", "yellow"]
        used_colors = []
        
        for player in self.players:
            if player and not player.is_bot and hasattr(player, 'avatar_color'):
                used_colors.append(player.avatar_color)
        
        return [color for color in all_colors if color not in used_colors]
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID."""
        self._last_operation_id += 1
        return f"{self.room_id}_{self._last_operation_id}"
    
    # Compatibility methods for migration
    def join_room_sync(self, player_name: str) -> int:
        """Sync wrapper for join_room."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.join_room(player_name))
        finally:
            loop.close()
    
    def exit_room_sync(self, player_name: str) -> bool:
        """Sync wrapper for exit_room."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.exit_room(player_name))
        finally:
            loop.close()
    
    def start_game_sync(self, broadcast_callback: Callable) -> Dict[str, Any]:
        """Sync wrapper for start_game."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_game(broadcast_callback))
        finally:
            loop.close()