"""
Tests for optimized in-memory repositories.

These tests verify performance characteristics and correct behavior
of the high-performance repository implementations.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from domain.entities.room import Room
from domain.entities.game import Game
from domain.entities.player import Player
from domain.value_objects import RoomId, PlayerId, RoomStatus, PlayerRole

from infrastructure.repositories.optimized_room_repository import (
    OptimizedRoomRepository,
)
from infrastructure.repositories.optimized_game_repository import (
    OptimizedGameRepository,
)
from infrastructure.repositories.optimized_player_stats_repository import (
    OptimizedPlayerStatsRepository,
)


class TestOptimizedRoomRepository:
    """Test suite for OptimizedRoomRepository."""

    @pytest.fixture
    def repo(self):
        """Create a repository instance."""
        return OptimizedRoomRepository(max_rooms=100)

    @pytest.fixture
    def sample_room(self):
        """Create a sample room."""
        room = Room(room_id="ROOM01", host_name="host")
        room.join_code = "ABC123"
        room.status = RoomStatus.WAITING
        return room

    @pytest.mark.asyncio
    async def test_save_and_retrieve_room(self, repo, sample_room):
        """Test basic save and retrieve operations."""
        # Save room
        await repo.save(sample_room)

        # Retrieve by ID
        retrieved = await repo.get_by_id("ROOM01")
        assert retrieved is not None
        assert retrieved.room_id == "ROOM01"
        assert retrieved.host_name == "host"

        # Retrieve by code
        retrieved_by_code = await repo.get_by_code("ABC123")
        assert retrieved_by_code is not None
        assert retrieved_by_code.room_id == "ROOM01"

    @pytest.mark.asyncio
    async def test_performance_o1_lookup(self, repo):
        """Test O(1) lookup performance."""
        # Add many rooms
        for i in range(100):
            room = Room(room_id=f"ROOM{i:02d}", host_name=f"host{i}")
            room.join_code = f"CODE{i:02d}"
            await repo.save(room)

        # Measure lookup time
        start = time.perf_counter()
        for _ in range(1000):
            await repo.get_by_id("ROOM50")
        end = time.perf_counter()

        avg_lookup_time = (end - start) / 1000
        # Should be very fast (< 0.1ms per lookup)
        assert avg_lookup_time < 0.0001

    @pytest.mark.asyncio
    async def test_lru_ordering(self, repo):
        """Test LRU ordering for cache efficiency."""
        # Add rooms
        for i in range(5):
            room = Room(room_id=f"ROOM{i}", host_name=f"host{i}")
            await repo.save(room)

        # Access in specific order
        await repo.get_by_id("ROOM2")
        await repo.get_by_id("ROOM4")
        await repo.get_by_id("ROOM1")

        # List active should return in reverse access order
        active = await repo.list_active(limit=3)
        assert [r.room_id for r in active] == ["ROOM1", "ROOM4", "ROOM2"]

    @pytest.mark.asyncio
    async def test_memory_pressure_eviction(self, repo):
        """Test eviction under memory pressure."""
        repo._max_rooms = 10

        # Fill to capacity
        for i in range(10):
            room = Room(room_id=f"ROOM{i:02d}", host_name=f"host{i}")
            room.status = RoomStatus.WAITING
            await repo.save(room)

        # Add completed room
        completed = Room(room_id="COMP01", host_name="host")
        completed.status = RoomStatus.COMPLETED
        await repo.save(completed)

        # Should evict completed room first
        assert await repo.get_by_id("COMP01") is None
        assert len(repo._rooms) == 10

    @pytest.mark.asyncio
    async def test_player_index(self, repo):
        """Test player index for fast lookups."""
        # Create rooms with players
        for i in range(3):
            room = Room(room_id=f"ROOM{i}", host_name=f"host{i}")
            room.players = [
                Player(PlayerId(f"player{i}"), f"Player {i}", PlayerRole.HUMAN)
            ]
            await repo.save(room)

        # Find by player
        room = await repo.find_by_player("player1")
        assert room is not None
        assert room.room_id == "ROOM1"

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, repo, sample_room):
        """Test performance metrics."""
        await repo.save(sample_room)

        # Access multiple times
        for _ in range(10):
            await repo.get_by_id("ROOM01")

        metrics = repo.get_metrics()
        assert metrics["total_rooms"] == 1
        assert metrics["total_accesses"] == 10
        assert metrics["active_rooms"] == 1

    @pytest.mark.asyncio
    async def test_thread_safety(self, repo):
        """Test concurrent access safety."""

        async def add_rooms(start, count):
            for i in range(count):
                room = Room(room_id=f"R{start}{i:02d}", host_name=f"host{start}{i}")
                await repo.save(room)

        # Concurrent adds
        await asyncio.gather(add_rooms("A", 50), add_rooms("B", 50), add_rooms("C", 50))

        assert len(repo._rooms) == 100  # Max capacity

    @pytest.mark.asyncio
    async def test_completed_room_archival(self, repo):
        """Test completed rooms are collected for archival."""
        # Add active room
        active = Room(room_id="ACTIVE", host_name="host")
        active.status = RoomStatus.IN_GAME
        await repo.save(active)

        # Add completed room
        completed = Room(room_id="COMP", host_name="host")
        completed.status = RoomStatus.COMPLETED
        await repo.save(completed)

        # Get completed rooms
        archived = repo.get_completed_rooms()
        assert len(archived) == 1
        assert archived[0].room_id == "COMP"

        # Should be cleared after retrieval
        assert len(repo.get_completed_rooms()) == 0


class TestOptimizedGameRepository:
    """Test suite for OptimizedGameRepository."""

    @pytest.fixture
    def repo(self):
        """Create a repository instance."""
        return OptimizedGameRepository(max_active_games=100)

    @pytest.fixture
    def sample_game(self):
        """Create a sample game."""
        game = Mock(spec=Game)
        game.room_id = "ROOM01"
        game.is_over = False
        game.turn_number = 5
        game.to_dict = Mock(return_value={"id": "game1", "data": "test"})
        return game

    @pytest.mark.asyncio
    async def test_save_and_retrieve_game(self, repo, sample_game):
        """Test basic save and retrieve."""
        await repo.save(sample_game)

        # Retrieve by room ID
        retrieved = await repo.get_by_room_id("ROOM01")
        assert retrieved is not None
        assert retrieved.room_id == "ROOM01"

        # Also works with room_id as game_id
        retrieved2 = await repo.get_by_id("ROOM01")
        assert retrieved2 is not None

    @pytest.mark.asyncio
    async def test_game_completion_handling(self, repo):
        """Test completed games are moved to archive queue."""
        # Active game
        active_game = Mock(spec=Game)
        active_game.room_id = "ROOM01"
        active_game.is_over = False
        await repo.save(active_game)

        # Complete the game
        active_game.is_over = True
        await repo.save(active_game)

        # Should be moved to archive queue
        assert "ROOM01" not in repo._active_games
        assert repo._archive_queue.qsize() == 1

        # Get archive batch
        batch = await repo.get_next_archive_batch(1)
        assert len(batch) == 1
        assert batch[0]["room_id"] == "ROOM01"

    @pytest.mark.asyncio
    async def test_performance_metrics(self, repo, sample_game):
        """Test game metrics tracking."""
        # Start a game
        await repo.save(sample_game)

        # Wait a bit
        await asyncio.sleep(0.1)

        # Complete it
        sample_game.is_over = True
        await repo.save(sample_game)

        metrics = repo.get_metrics()
        assert metrics["active_games"] == 0
        assert metrics["completed_games_buffer"] == 1
        assert metrics["total_games_archived"] == 0  # Not yet processed
        assert metrics["archive_queue_size"] == 1

    @pytest.mark.asyncio
    async def test_archive_queue_overflow(self, repo):
        """Test archive queue overflow handling."""
        repo._archive_queue = asyncio.Queue(maxsize=2)

        # Fill archive queue
        for i in range(3):
            game = Mock(spec=Game)
            game.room_id = f"ROOM{i}"
            game.is_over = True
            game.to_dict = Mock(return_value={})
            await repo.save(game)

        # Queue should be full, last game dropped
        assert repo._archive_queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_memory_warning(self, repo, caplog):
        """Test memory pressure warning."""
        repo._max_active_games = 2

        # Add games up to limit
        for i in range(3):
            game = Mock(spec=Game)
            game.room_id = f"ROOM{i}"
            game.is_over = False
            await repo.save(game)

        # Should log warning
        assert "At capacity" in caplog.text


class TestOptimizedPlayerStatsRepository:
    """Test suite for OptimizedPlayerStatsRepository."""

    @pytest.fixture
    def repo(self):
        """Create a repository instance."""
        return OptimizedPlayerStatsRepository(leaderboard_cache_ttl=1)

    @pytest.mark.asyncio
    async def test_update_game_result(self, repo):
        """Test updating stats after a game."""
        # Win game
        await repo.update_game_result(
            player_id="player1", won=True, score=100, piles_captured=5, perfect_rounds=2
        )

        stats = await repo.get_stats("player1")
        assert stats["games_played"] == 1
        assert stats["games_won"] == 1
        assert stats["total_score"] == 100
        assert stats["highest_score"] == 100
        assert stats["win_rate"] == 100.0
        assert stats["win_streak"] == 1

        # Lose game
        await repo.update_game_result(
            player_id="player1", won=False, score=50, piles_captured=2
        )

        stats = await repo.get_stats("player1")
        assert stats["games_played"] == 2
        assert stats["games_won"] == 1
        assert stats["total_score"] == 150
        assert stats["win_rate"] == 50.0
        assert stats["win_streak"] == 0
        assert stats["average_score"] == 75.0

    @pytest.mark.asyncio
    async def test_leaderboard_caching(self, repo):
        """Test leaderboard caching for performance."""
        # Add players
        for i in range(10):
            await repo.update_game_result(
                player_id=f"player{i}",
                won=i % 2 == 0,
                score=100 - i * 5,
                piles_captured=5,
            )

        # First call builds cache
        start = time.perf_counter()
        leaderboard1 = await repo.get_leaderboard(5)
        first_call_time = time.perf_counter() - start

        # Second call uses cache (should be much faster)
        start = time.perf_counter()
        leaderboard2 = await repo.get_leaderboard(5)
        second_call_time = time.perf_counter() - start

        assert second_call_time < first_call_time / 10
        assert leaderboard1 == leaderboard2

    @pytest.mark.asyncio
    async def test_multiple_leaderboards(self, repo):
        """Test different leaderboard metrics."""
        # Player 1: High wins, low score
        for _ in range(5):
            await repo.update_game_result(
                "player1", won=True, score=10, piles_captured=1
            )

        # Player 2: Low wins, high score
        await repo.update_game_result("player2", won=True, score=500, piles_captured=10)
        await repo.update_game_result("player2", won=False, score=400, piles_captured=8)

        # By wins
        by_wins = await repo.get_leaderboard_by_metric("wins", 10)
        assert by_wins[0]["player_id"] == "player1"

        # By score
        by_score = await repo.get_leaderboard_by_metric("score", 10)
        assert by_score[0]["player_id"] == "player2"

    @pytest.mark.asyncio
    async def test_player_rank(self, repo):
        """Test player ranking."""
        # Add players with different scores
        players = [
            ("player1", 5, 5),  # 5 wins
            ("player2", 3, 5),  # 3 wins
            ("player3", 1, 5),  # 1 win
        ]

        for pid, wins, total in players:
            for i in range(total):
                await repo.update_game_result(
                    pid, won=(i < wins), score=100, piles_captured=5
                )

        # Check ranks
        assert await repo.get_player_rank("player1") == 1
        assert await repo.get_player_rank("player2") == 2
        assert await repo.get_player_rank("player3") == 3
        assert await repo.get_player_rank("unknown") is None

    @pytest.mark.asyncio
    async def test_export_top_players(self, repo):
        """Test exporting top players for archival."""
        # Add some players
        for i in range(5):
            await repo.update_game_result(
                f"player{i}", won=True, score=100 * (5 - i), piles_captured=5
            )

        exported = await repo.export_top_players(3)
        assert len(exported) == 3
        assert all("export_timestamp" in p for p in exported)
        assert exported[0]["player_id"] == "player0"  # Most wins

    @pytest.mark.asyncio
    async def test_repository_metrics(self, repo):
        """Test repository performance metrics."""
        # Some operations
        await repo.get_stats("player1")  # Miss
        await repo.update_game_result("player1", True, 100, 5)
        await repo.get_stats("player1")  # Hit
        await repo.get_leaderboard()  # Miss
        await repo.get_leaderboard()  # Hit

        metrics = repo.get_metrics()
        assert metrics["total_players"] == 1
        assert metrics["active_players"] == 1
        assert metrics["total_updates"] == 1
        assert metrics["cache_hit_rate"] > 0
