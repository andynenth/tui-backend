"""
Hybrid game repository with automatic archival.

Maintains active games in memory and archives completed games asynchronously.
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import asyncio
import logging
from collections import OrderedDict


from backend.domain.entities import Game
from backend.application.interfaces import IGameRepository
from backend.infrastructure.persistence.archive import (
    ArchiveManager, ArchivalTrigger, ArchivalPriority,
    FileSystemArchiveBackend, GameArchivalStrategy,
    DEFAULT_GAME_POLICY
)


logger = logging.getLogger(__name__)


class HybridGameRepository(IGameRepository):
    """
    Hybrid implementation of game repository.
    
    Features:
    - Active games stay 100% in memory for performance
    - Completed games are automatically archived
    - Transparent retrieval from archive when needed
    - No performance impact on active games
    """
    
    def __init__(
        self,
        max_active_games: int = 1000,
        archive_on_completion: bool = True,
        archive_after_inactive: Optional[timedelta] = timedelta(hours=1),
        enable_compression: bool = True
    ):
        """
        Initialize hybrid game repository.
        
        Args:
            max_active_games: Maximum active games in memory
            archive_on_completion: Archive games immediately on completion
            archive_after_inactive: Archive after inactivity period
            enable_compression: Enable compression for archives
        """
        # In-memory storage for active games
        self._active_games: OrderedDict[str, Game] = OrderedDict()
        self._games_by_room: Dict[str, Set[str]] = {}
        self._games_by_player: Dict[str, Set[str]] = {}
        
        # Configuration
        self.max_active_games = max_active_games
        self.archive_on_completion = archive_on_completion
        self.archive_after_inactive = archive_after_inactive
        
        # Archive manager
        self._archive_manager: Optional[ArchiveManager] = None
        self._archive_backend = FileSystemArchiveBackend(
            use_compression=enable_compression
        )
        
        # Track last activity
        self._last_activity: Dict[str, datetime] = {}
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> None:
        """Initialize repository and start background tasks."""
        # Setup archive manager
        self._archive_manager = ArchiveManager(
            entity_provider=self,
            backend=self._archive_backend,
            policies={'game': DEFAULT_GAME_POLICY},
            enable_worker=True,
            enable_monitoring=True
        )
        
        await self._archive_manager.start()
        
        # Start background cleanup
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Hybrid game repository initialized")
    
    async def shutdown(self) -> None:
        """Shutdown repository and stop background tasks."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._archive_manager:
            await self._archive_manager.stop()
        
        logger.info("Hybrid game repository shutdown")
    
    async def save(self, game: Game) -> None:
        """Save or update a game."""
        game_id = game.id
        
        # Update activity tracking
        self._last_activity[game_id] = datetime.utcnow()
        
        # Save to active storage
        self._active_games[game_id] = game
        
        # Update indexes
        if game.room_id:
            if game.room_id not in self._games_by_room:
                self._games_by_room[game.room_id] = set()
            self._games_by_room[game.room_id].add(game_id)
        
        # Update player index
        for player in game.players:
            if player.id not in self._games_by_player:
                self._games_by_player[player.id] = set()
            self._games_by_player[player.id].add(game_id)
        
        # Check if should archive
        if self.archive_on_completion and game.status == 'completed':
            await self._trigger_archival(game)
        
        # Check capacity
        if len(self._active_games) > self.max_active_games:
            await self._evict_oldest_inactive()
    
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        """Get game by ID from active storage or archive."""
        # Check active storage first
        if game_id in self._active_games:
            self._last_activity[game_id] = datetime.utcnow()
            return self._active_games[game_id]
        
        # Try to retrieve from archive
        if self._archive_manager:
            game = await self._archive_manager.retrieve_entity(game_id, 'game')
            if game:
                # Optionally restore to active storage if game is recent
                if hasattr(game, 'completed_at'):
                    age = datetime.utcnow() - game.completed_at
                    if age < timedelta(hours=24):
                        # Recent game, keep in memory for potential access
                        self._active_games[game_id] = game
                        self._last_activity[game_id] = datetime.utcnow()
                
                return game
        
        return None
    
    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """Get active game for a room."""
        game_ids = self._games_by_room.get(room_id, set())
        
        # Look for active (non-completed) game
        for game_id in game_ids:
            game = self._active_games.get(game_id)
            if game and game.status != 'completed':
                self._last_activity[game_id] = datetime.utcnow()
                return game
        
        return None
    
    async def get_games_by_player_id(self, player_id: str) -> List[Game]:
        """Get all games for a player."""
        games = []
        
        # Get from active storage
        game_ids = self._games_by_player.get(player_id, set())
        for game_id in game_ids:
            if game_id in self._active_games:
                games.append(self._active_games[game_id])
        
        # Note: Could also search archives if needed
        # This would be slower and typically not needed for active play
        
        return games
    
    async def delete(self, game_id: str) -> bool:
        """Delete a game from active storage."""
        if game_id not in self._active_games:
            return False
        
        game = self._active_games[game_id]
        
        # Remove from indexes
        if game.room_id and game.room_id in self._games_by_room:
            self._games_by_room[game.room_id].discard(game_id)
            if not self._games_by_room[game.room_id]:
                del self._games_by_room[game.room_id]
        
        for player in game.players:
            if player.id in self._games_by_player:
                self._games_by_player[player.id].discard(game_id)
                if not self._games_by_player[player.id]:
                    del self._games_by_player[player.id]
        
        # Remove from active storage
        del self._active_games[game_id]
        self._last_activity.pop(game_id, None)
        
        return True
    
    async def list_active_games(self) -> List[Game]:
        """List all active games in memory."""
        return list(self._active_games.values())
    
    # IEntityProvider implementation for ArchiveManager
    
    async def get_entity(self, entity_id: str, entity_type: str) -> Any:
        """Get entity for archival."""
        if entity_type == 'game':
            return self._active_games.get(entity_id)
        return None
    
    async def list_entities(self, entity_type: str, 
                          filter_func: Optional[callable] = None) -> List[Any]:
        """List entities for archival."""
        if entity_type == 'game':
            games = list(self._active_games.values())
            if filter_func:
                games = [g for g in games if filter_func(g)]
            return games
        return []
    
    async def delete_entity(self, entity_id: str, entity_type: str) -> bool:
        """Delete entity after archival."""
        if entity_type == 'game':
            return await self.delete(entity_id)
        return False
    
    # Private methods
    
    async def _trigger_archival(self, game: Game) -> None:
        """Trigger archival for a completed game."""
        if not self._archive_manager:
            return
        
        logger.info(f"Triggering archival for completed game {game.id}")
        
        success = await self._archive_manager.archive_entity(
            entity_id=game.id,
            entity_type='game',
            trigger=ArchivalTrigger.GAME_COMPLETED,
            priority=ArchivalPriority.NORMAL
        )
        
        if success:
            # Game will be removed from active storage after successful archival
            logger.debug(f"Game {game.id} submitted for archival")
    
    async def _evict_oldest_inactive(self) -> None:
        """Evict oldest inactive games to maintain capacity."""
        # Find completed games first
        completed_games = [
            (game_id, game) 
            for game_id, game in self._active_games.items()
            if game.status == 'completed'
        ]
        
        if completed_games:
            # Archive oldest completed game
            oldest_id, oldest_game = completed_games[0]
            await self._trigger_archival(oldest_game)
        else:
            # No completed games, check for inactive games
            current_time = datetime.utcnow()
            
            for game_id, last_activity in self._last_activity.items():
                if self.archive_after_inactive:
                    if current_time - last_activity > self.archive_after_inactive:
                        game = self._active_games.get(game_id)
                        if game:
                            logger.info(f"Archiving inactive game {game_id}")
                            await self._archive_manager.archive_entity(
                                entity_id=game_id,
                                entity_type='game',
                                trigger=ArchivalTrigger.TIME_BASED,
                                priority=ArchivalPriority.LOW
                            )
                            break
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self._running:
            try:
                # Check for games to archive
                current_time = datetime.utcnow()
                to_archive = []
                
                for game_id, game in self._active_games.items():
                    # Check completed games
                    if game.status == 'completed':
                        # Archive if old enough
                        if hasattr(game, 'completed_at'):
                            age = current_time - game.completed_at
                            if age > timedelta(minutes=5):  # Give 5 minutes for replay
                                to_archive.append((game_id, ArchivalTrigger.GAME_COMPLETED))
                    
                    # Check inactive games
                    elif self.archive_after_inactive:
                        last_activity = self._last_activity.get(game_id, current_time)
                        if current_time - last_activity > self.archive_after_inactive:
                            to_archive.append((game_id, ArchivalTrigger.TIME_BASED))
                
                # Archive games
                for game_id, trigger in to_archive:
                    await self._archive_manager.archive_entity(
                        entity_id=game_id,
                        entity_type='game',
                        trigger=trigger,
                        priority=ArchivalPriority.LOW
                    )
                
                # Sleep for cleanup interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        return {
            'active_games': len(self._active_games),
            'completed_games': sum(
                1 for g in self._active_games.values() 
                if g.status == 'completed'
            ),
            'rooms_with_games': len(self._games_by_room),
            'players_with_games': len(self._games_by_player),
            'max_capacity': self.max_active_games,
            'archive_enabled': self._archive_manager is not None
        }