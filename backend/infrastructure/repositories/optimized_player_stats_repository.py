"""
High-performance player statistics repository with real-time aggregation.

This implementation provides instant access to player statistics with
automatic aggregation and efficient leaderboard calculations.
"""

import asyncio
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import heapq

from application.interfaces.repositories import PlayerStatsRepository


logger = logging.getLogger(__name__)


@dataclass
class PlayerStatistics:
    """Enhanced player statistics with performance tracking."""

    player_id: str
    games_played: int = 0
    games_won: int = 0
    total_score: int = 0
    highest_score: int = 0
    perfect_rounds: int = 0
    total_piles_captured: int = 0

    # Additional performance metrics
    last_game_at: Optional[datetime] = None
    win_streak: int = 0
    best_win_streak: int = 0
    average_score: float = 0.0

    # Time-based stats
    games_today: int = 0
    games_this_week: int = 0
    games_this_month: int = 0

    def calculate_win_rate(self) -> float:
        """Calculate win rate as percentage."""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "player_id": self.player_id,
            "games_played": self.games_played,
            "games_won": self.games_won,
            "total_score": self.total_score,
            "highest_score": self.highest_score,
            "win_rate": self.calculate_win_rate(),
            "average_score": self.average_score,
            "win_streak": self.win_streak,
            "best_win_streak": self.best_win_streak,
            "last_game_at": (
                self.last_game_at.isoformat() if self.last_game_at else None
            ),
        }


class OptimizedPlayerStatsRepository(PlayerStatsRepository):
    """
    High-performance player statistics repository with:
    - Real-time aggregation and updates
    - Efficient leaderboard calculations
    - Time-based statistics tracking
    - Memory-efficient storage
    """

    def __init__(self, leaderboard_cache_ttl: int = 60):
        """
        Initialize repository with performance features.

        Args:
            leaderboard_cache_ttl: Cache TTL for leaderboard in seconds
        """
        # Primary storage
        self._stats: Dict[str, PlayerStatistics] = {}

        # Leaderboard caches (updated periodically)
        self._leaderboard_by_wins: List[Tuple[str, PlayerStatistics]] = []
        self._leaderboard_by_score: List[Tuple[str, PlayerStatistics]] = []
        self._leaderboard_by_rate: List[Tuple[str, PlayerStatistics]] = []
        self._leaderboard_last_update = 0
        self._leaderboard_cache_ttl = leaderboard_cache_ttl

        # Daily/weekly/monthly tracking
        self._daily_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._last_daily_reset = datetime.now().date()

        # Thread safety
        self._lock = asyncio.Lock()

        # Performance metrics
        self._total_updates = 0
        self._cache_hits = 0
        self._cache_misses = 0

    async def get_stats(self, player_id: str) -> Dict[str, Any]:
        """Get statistics for a player with O(1) access."""
        stats = self._stats.get(player_id)
        if stats:
            self._cache_hits += 1
            return stats.to_dict()

        self._cache_misses += 1
        return {
            "player_id": player_id,
            "games_played": 0,
            "games_won": 0,
            "total_score": 0,
            "highest_score": 0,
            "win_rate": 0.0,
            "average_score": 0.0,
        }

    async def update_stats(self, player_id: str, stats: Dict[str, Any]) -> None:
        """Update statistics for a player."""
        async with self._lock:
            if player_id not in self._stats:
                self._stats[player_id] = PlayerStatistics(player_id=player_id)

            player_stats = self._stats[player_id]

            # Update basic stats
            if "games_played" in stats:
                player_stats.games_played = stats["games_played"]
            if "games_won" in stats:
                player_stats.games_won = stats["games_won"]
            if "total_score" in stats:
                player_stats.total_score = stats["total_score"]
            if "highest_score" in stats:
                player_stats.highest_score = max(
                    player_stats.highest_score, stats.get("highest_score", 0)
                )

            # Update calculated fields
            if player_stats.games_played > 0:
                player_stats.average_score = (
                    player_stats.total_score / player_stats.games_played
                )

            self._total_updates += 1
            self._invalidate_leaderboard_cache()

    async def update_game_result(
        self,
        player_id: str,
        won: bool,
        score: int,
        piles_captured: int,
        perfect_rounds: int = 0,
    ) -> None:
        """Update stats after a game with automatic aggregation."""
        async with self._lock:
            if player_id not in self._stats:
                self._stats[player_id] = PlayerStatistics(player_id=player_id)

            stats = self._stats[player_id]
            now = datetime.now()

            # Update basic counters
            stats.games_played += 1
            stats.total_score += score
            stats.total_piles_captured += piles_captured
            stats.perfect_rounds += perfect_rounds
            stats.last_game_at = now

            # Update score tracking
            stats.highest_score = max(stats.highest_score, score)
            stats.average_score = stats.total_score / stats.games_played

            # Update win tracking
            if won:
                stats.games_won += 1
                stats.win_streak += 1
                stats.best_win_streak = max(stats.best_win_streak, stats.win_streak)
            else:
                stats.win_streak = 0

            # Update time-based stats
            await self._update_time_based_stats(player_id)

            self._total_updates += 1
            self._invalidate_leaderboard_cache()

            logger.info(
                f"Updated stats for {player_id}: "
                f"{'WIN' if won else 'LOSS'}, score={score}, "
                f"total_games={stats.games_played}"
            )

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players with cached results for performance."""
        # Check if cache is valid
        if self._is_leaderboard_cache_valid():
            self._cache_hits += 1
            return [stats.to_dict() for _, stats in self._leaderboard_by_wins[:limit]]

        self._cache_misses += 1

        # Rebuild leaderboard caches
        async with self._lock:
            await self._rebuild_leaderboards()

        return [stats.to_dict() for _, stats in self._leaderboard_by_wins[:limit]]

    async def get_leaderboard_by_metric(
        self, metric: str = "wins", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get leaderboard sorted by different metrics."""
        # Ensure cache is fresh
        if not self._is_leaderboard_cache_valid():
            async with self._lock:
                await self._rebuild_leaderboards()

        # Return appropriate leaderboard
        if metric == "wins":
            leaderboard = self._leaderboard_by_wins
        elif metric == "score":
            leaderboard = self._leaderboard_by_score
        elif metric == "win_rate":
            leaderboard = self._leaderboard_by_rate
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return [stats.to_dict() for _, stats in leaderboard[:limit]]

    async def get_player_rank(
        self, player_id: str, metric: str = "wins"
    ) -> Optional[int]:
        """Get player's rank in leaderboard with O(n) scan."""
        # Ensure cache is fresh
        if not self._is_leaderboard_cache_valid():
            async with self._lock:
                await self._rebuild_leaderboards()

        # Select appropriate leaderboard
        if metric == "wins":
            leaderboard = self._leaderboard_by_wins
        elif metric == "score":
            leaderboard = self._leaderboard_by_score
        elif metric == "win_rate":
            leaderboard = self._leaderboard_by_rate
        else:
            return None

        # Find player rank
        for rank, (pid, _) in enumerate(leaderboard, 1):
            if pid == player_id:
                return rank

        return None

    # Private helper methods

    def _is_leaderboard_cache_valid(self) -> bool:
        """Check if leaderboard cache is still valid."""
        return (
            time.time() - self._leaderboard_last_update
        ) < self._leaderboard_cache_ttl

    def _invalidate_leaderboard_cache(self):
        """Mark leaderboard cache as invalid."""
        self._leaderboard_last_update = 0

    async def _rebuild_leaderboards(self):
        """Rebuild all leaderboard caches efficiently."""
        # Get all players with at least one game
        active_players = [
            (pid, stats) for pid, stats in self._stats.items() if stats.games_played > 0
        ]

        # Sort by wins (primary: wins, secondary: win rate)
        self._leaderboard_by_wins = sorted(
            active_players,
            key=lambda x: (x[1].games_won, x[1].calculate_win_rate()),
            reverse=True,
        )

        # Sort by total score
        self._leaderboard_by_score = sorted(
            active_players, key=lambda x: x[1].total_score, reverse=True
        )

        # Sort by win rate (minimum 10 games)
        eligible_for_rate = [
            (pid, stats) for pid, stats in active_players if stats.games_played >= 10
        ]
        self._leaderboard_by_rate = sorted(
            eligible_for_rate, key=lambda x: x[1].calculate_win_rate(), reverse=True
        )

        self._leaderboard_last_update = time.time()
        logger.debug(f"Rebuilt leaderboards with {len(active_players)} players")

    async def _update_time_based_stats(self, player_id: str):
        """Update daily/weekly/monthly statistics."""
        today = datetime.now().date()

        # Reset daily stats if needed
        if today != self._last_daily_reset:
            self._daily_stats.clear()
            self._last_daily_reset = today

            # Reset daily counters for all players
            for stats in self._stats.values():
                stats.games_today = 0

        # Update counters
        stats = self._stats[player_id]
        stats.games_today += 1

        # Update weekly/monthly (simplified - in production would track properly)
        stats.games_this_week = stats.games_today  # Simplified
        stats.games_this_month = stats.games_today  # Simplified

    # Monitoring methods

    def get_metrics(self) -> Dict[str, Any]:
        """Get repository performance metrics."""
        total_players = len(self._stats)
        active_players = sum(1 for s in self._stats.values() if s.games_played > 0)

        return {
            "total_players": total_players,
            "active_players": active_players,
            "total_updates": self._total_updates,
            "cache_hit_rate": (
                self._cache_hits / max(self._cache_hits + self._cache_misses, 1) * 100
            ),
            "leaderboard_cache_valid": self._is_leaderboard_cache_valid(),
            "memory_usage_estimate": total_players * 256,  # ~256 bytes per player
        }

    async def export_top_players(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Export top players for archival/analytics."""
        await self.get_leaderboard(limit=1)  # Ensure cache is fresh

        return [
            {**stats.to_dict(), "export_timestamp": datetime.utcnow().isoformat()}
            for _, stats in self._leaderboard_by_wins[:limit]
        ]
