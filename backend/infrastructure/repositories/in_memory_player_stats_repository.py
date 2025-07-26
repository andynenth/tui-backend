"""
In-memory implementation of PlayerStatsRepository.

This provides a simple in-memory storage for player statistics during
development and testing.
"""

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from copy import deepcopy

from application.interfaces import PlayerStatsRepository
from application.dto.common import PlayerStats

logger = logging.getLogger(__name__)


class InMemoryPlayerStatsRepository(PlayerStatsRepository):
    """
    In-memory implementation of the player stats repository.
    
    Stores player statistics in memory using dictionaries.
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._stats: Dict[str, PlayerStats] = {}
        
    async def get_by_player_id(self, player_id: str) -> Optional[PlayerStats]:
        """
        Get statistics for a specific player.
        
        Args:
            player_id: The player identifier
            
        Returns:
            Player statistics if found, None otherwise
        """
        stats = self._stats.get(player_id)
        if stats:
            logger.debug(f"Retrieved stats for player {player_id}")
        return deepcopy(stats) if stats else None
    
    async def save(self, player_id: str, stats: PlayerStats) -> None:
        """
        Save or update player statistics.
        
        Args:
            player_id: The player identifier
            stats: The statistics to save
        """
        self._stats[player_id] = deepcopy(stats)
        logger.debug(f"Saved stats for player {player_id}")
    
    async def increment_games_played(self, player_id: str) -> None:
        """
        Increment the games played counter for a player.
        
        Args:
            player_id: The player identifier
        """
        stats = await self.get_by_player_id(player_id)
        if not stats:
            stats = PlayerStats(
                games_played=0,
                games_won=0,
                total_score=0,
                highest_score=0,
                perfect_rounds=0,
                total_piles_captured=0
            )
        
        stats.games_played += 1
        await self.save(player_id, stats)
        logger.debug(f"Incremented games played for player {player_id}")
    
    async def update_win(
        self,
        player_id: str,
        final_score: int,
        piles_captured: int
    ) -> None:
        """
        Update statistics for a game win.
        
        Args:
            player_id: The player identifier
            final_score: The player's final score
            piles_captured: Total piles captured in the game
        """
        stats = await self.get_by_player_id(player_id)
        if not stats:
            stats = PlayerStats(
                games_played=1,
                games_won=0,
                total_score=0,
                highest_score=0,
                perfect_rounds=0,
                total_piles_captured=0
            )
        
        stats.games_won += 1
        stats.total_score += final_score
        stats.highest_score = max(stats.highest_score, final_score)
        stats.total_piles_captured += piles_captured
        
        await self.save(player_id, stats)
        logger.info(f"Updated win stats for player {player_id}")
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top players by wins.
        
        Args:
            limit: Maximum number of players to return
            
        Returns:
            List of (player_id, stats) tuples sorted by wins
        """
        # Sort by wins, then by win rate
        sorted_players = sorted(
            self._stats.items(),
            key=lambda x: (
                x[1].games_won,
                x[1].games_won / max(x[1].games_played, 1)
            ),
            reverse=True
        )
        
        result = []
        for pid, stats in sorted_players[:limit]:
            result.append({
                'player_id': pid,
                'games_played': stats.games_played,
                'games_won': stats.games_won,
                'total_score': stats.total_score,
                'highest_score': stats.highest_score,
                'win_rate': stats.games_won / max(stats.games_played, 1)
            })
        logger.debug(f"Retrieved leaderboard with {len(result)} players")
        return result
    
    async def get_player_rank(self, player_id: str) -> Optional[int]:
        """
        Get a player's rank in the leaderboard.
        
        Args:
            player_id: The player identifier
            
        Returns:
            The player's rank (1-based) or None if not found
        """
        leaderboard = await self.get_leaderboard(limit=len(self._stats))
        
        for rank, (pid, _) in enumerate(leaderboard, 1):
            if pid == player_id:
                return rank
        
        return None
    
    async def get_stats(self, player_id: str) -> Dict[str, Any]:
        """Get statistics for a player."""
        stats = await self.get_by_player_id(player_id)
        if stats:
            return {
                'games_played': stats.games_played,
                'games_won': stats.games_won,
                'total_score': stats.total_score,
                'highest_score': stats.highest_score,
                'win_rate': stats.games_won / max(stats.games_played, 1)
            }
        return {}
    
    async def update_stats(self, player_id: str, stats: Dict[str, Any]) -> None:
        """Update statistics for a player."""
        current = await self.get_by_player_id(player_id)
        if not current:
            current = PlayerStats(
                games_played=0,
                games_won=0,
                total_score=0,
                highest_score=0,
                perfect_rounds=0,
                total_piles_captured=0
            )
        
        # Update fields that are provided
        if 'games_played' in stats:
            current.games_played = stats['games_played']
        if 'games_won' in stats:
            current.games_won = stats['games_won']
        if 'total_score' in stats:
            current.total_score = stats['total_score']
        if 'highest_score' in stats:
            current.highest_score = stats['highest_score']
            
        await self.save(player_id, current)
    
    def snapshot(self) -> Dict[str, any]:
        """Create a snapshot of current state for rollback."""
        return {'stats': deepcopy(self._stats)}
    
    def restore(self, snapshot: Dict[str, any]) -> None:
        """Restore from a snapshot."""
        self._stats = snapshot['stats']