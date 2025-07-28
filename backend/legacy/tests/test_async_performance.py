# backend/tests/test_async_performance.py
"""
Performance tests for async implementation.
Tests concurrent game handling and bot decision making.
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import statistics

from engine.async_room_manager import AsyncRoomManager
from engine.async_room import AsyncRoom
from engine.async_game import AsyncGame
from engine.async_compat import AsyncCompatRoomManager
from engine.room_manager import RoomManager
from engine.async_bot_strategy import async_bot_strategy
from engine.piece import Piece
from engine.player import Player


class TestAsyncPerformance:
    """Test suite for async performance benchmarks."""
    
    @pytest.fixture
    async def async_room_manager(self):
        """Create AsyncRoomManager for testing."""
        manager = AsyncRoomManager()
        yield manager
        # Cleanup
        manager._rooms.clear()
    
    @pytest.fixture
    async def compat_room_manager(self):
        """Create compatibility room manager."""
        sync_manager = RoomManager()
        manager = AsyncCompatRoomManager(sync_manager)
        yield manager
        # Cleanup
        sync_manager.rooms.clear()
    
    @pytest.mark.asyncio
    async def test_concurrent_room_creation(self, async_room_manager):
        """Test creating multiple rooms concurrently."""
        num_rooms = 10
        start_time = time.time()
        
        # Create rooms concurrently
        tasks = []
        for i in range(num_rooms):
            task = async_room_manager.create_room(f"Host{i}")
            tasks.append(task)
        
        room_ids = await asyncio.gather(*tasks)
        elapsed = (time.time() - start_time) * 1000
        
        assert len(room_ids) == num_rooms
        assert len(set(room_ids)) == num_rooms  # All unique
        print(f"Created {num_rooms} rooms concurrently in {elapsed:.2f}ms")
        assert elapsed < 1000  # Should be fast
    
    @pytest.mark.asyncio
    async def test_concurrent_player_joins(self, async_room_manager):
        """Test multiple players joining rooms concurrently."""
        # Create a room
        room_id = await async_room_manager.create_room("Host")
        
        # Join 3 players concurrently
        start_time = time.time()
        tasks = []
        for i in range(3):
            task = async_room_manager.join_room(room_id, f"Player{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        elapsed = (time.time() - start_time) * 1000
        
        # All should succeed
        for result in results:
            assert result["success"] == True
        
        # Check room state
        room = async_room_manager._rooms[room_id]
        assert len(room.players) == 4  # Host + 3 players
        print(f"3 players joined concurrently in {elapsed:.2f}ms")
        assert elapsed < 500  # Should be fast
    
    @pytest.mark.asyncio
    async def test_concurrent_bot_decisions(self):
        """Test concurrent bot decision making."""
        # Create bot hands
        bot_hands = {}
        for i in range(4):
            hand = [
                MagicMock(spec=Piece, point=j+5, color="RED")
                for j in range(8)
            ]
            bot_hands[f"Bot{i}"] = hand
        
        # Test concurrent declarations
        start_time = time.time()
        declare_results = await async_bot_strategy.simulate_concurrent_decisions(
            bot_hands, 
            decision_type="declare"
        )
        declare_elapsed = (time.time() - start_time) * 1000
        
        assert len(declare_results) == 4
        for bot_name, declaration in declare_results.items():
            assert 0 <= declaration <= 8
        
        print(f"4 bot declarations completed concurrently in {declare_elapsed:.2f}ms")
        
        # Test concurrent plays
        start_time = time.time()
        play_results = await async_bot_strategy.simulate_concurrent_decisions(
            bot_hands,
            decision_type="play"
        )
        play_elapsed = (time.time() - start_time) * 1000
        
        assert len(play_results) == 4
        for bot_name, pieces in play_results.items():
            assert isinstance(pieces, list)
            assert len(pieces) > 0
        
        print(f"4 bot plays completed concurrently in {play_elapsed:.2f}ms")
        
        # Should be faster than sequential
        assert declare_elapsed < 300  # Reasonable threshold for 4 concurrent decisions
        assert play_elapsed < 300
    
    @pytest.mark.asyncio
    async def test_async_vs_sync_room_performance(self, async_room_manager, compat_room_manager):
        """Compare performance of async vs sync room operations."""
        num_operations = 20
        
        # Test async room manager
        async_start = time.time()
        async_room_ids = []
        for i in range(num_operations):
            room_id = await async_room_manager.create_room(f"AsyncHost{i}")
            async_room_ids.append(room_id)
        async_elapsed = (time.time() - async_start) * 1000
        
        # Test compat room manager (sync wrapped)
        compat_start = time.time()
        compat_room_ids = []
        for i in range(num_operations):
            room_id = await compat_room_manager.create_room(f"SyncHost{i}")
            compat_room_ids.append(room_id)
        compat_elapsed = (time.time() - compat_start) * 1000
        
        print(f"Async room creation: {async_elapsed:.2f}ms")
        print(f"Compat room creation: {compat_elapsed:.2f}ms")
        print(f"Speedup: {compat_elapsed/async_elapsed:.2f}x")
        
        # Async should be at least as fast
        assert async_elapsed <= compat_elapsed * 1.2  # Allow 20% variance
    
    @pytest.mark.asyncio
    async def test_concurrent_game_operations(self):
        """Test concurrent game operations."""
        # Create 4 games
        games = []
        for i in range(4):
            players = [
                MagicMock(spec=Player, name=f"P{j}", is_bot=False)
                for j in range(4)
            ]
            game = AsyncGame(players)
            games.append(game)
        
        # Test concurrent dealing
        start_time = time.time()
        deal_tasks = [game.deal_pieces() for game in games]
        deal_results = await asyncio.gather(*deal_tasks)
        deal_elapsed = (time.time() - start_time) * 1000
        
        for result in deal_results:
            assert result["success"] == True
        
        print(f"4 games dealt concurrently in {deal_elapsed:.2f}ms")
        
        # Test concurrent score calculations
        for game in games:
            # Setup some game state
            game.pile_counts = {p.name: 2 for p in game.players}
            for p in game.players:
                p.declared = 2
        
        start_time = time.time()
        score_tasks = [game.calculate_scores() for game in games]
        score_results = await asyncio.gather(*score_tasks)
        score_elapsed = (time.time() - start_time) * 1000
        
        for scores in score_results:
            assert len(scores) == 4
        
        print(f"4 games scored concurrently in {score_elapsed:.2f}ms")
        
        # Should handle concurrent operations efficiently
        assert deal_elapsed < 500
        assert score_elapsed < 200
    
    @pytest.mark.asyncio
    async def test_stress_concurrent_operations(self, async_room_manager):
        """Stress test with many concurrent operations."""
        num_rooms = 5
        players_per_room = 4
        
        start_time = time.time()
        
        # Create rooms
        room_tasks = []
        for i in range(num_rooms):
            task = async_room_manager.create_room(f"StressHost{i}")
            room_tasks.append(task)
        
        room_ids = await asyncio.gather(*room_tasks)
        
        # Join players to all rooms concurrently
        join_tasks = []
        for room_id in room_ids:
            for j in range(players_per_room - 1):  # -1 for host
                task = async_room_manager.join_room(room_id, f"Player{j}")
                join_tasks.append(task)
        
        join_results = await asyncio.gather(*join_tasks)
        
        # Start all games concurrently
        start_tasks = []
        for room_id in room_ids:
            task = async_room_manager.start_game(room_id)
            start_tasks.append(task)
        
        start_results = await asyncio.gather(*start_tasks)
        
        elapsed = (time.time() - start_time) * 1000
        
        # Verify all operations succeeded
        assert all(result["success"] for result in join_results)
        assert all(result["success"] for result in start_results)
        
        total_operations = num_rooms + (num_rooms * (players_per_room - 1)) + num_rooms
        print(f"Completed {total_operations} operations in {elapsed:.2f}ms")
        print(f"Average: {elapsed/total_operations:.2f}ms per operation")
        
        # Should handle stress efficiently
        assert elapsed < 5000  # 5 seconds for all operations
    
    @pytest.mark.asyncio
    async def test_game_state_consistency(self, async_room_manager):
        """Test that concurrent operations maintain game state consistency."""
        room_id = await async_room_manager.create_room("ConsistencyHost")
        
        # Join 3 players concurrently multiple times (should fail gracefully)
        tasks = []
        for i in range(9):  # Try to join 9 players (only 3 should succeed)
            task = async_room_manager.join_room(room_id, f"Player{i % 3}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failures = sum(1 for r in results if isinstance(r, dict) and not r.get("success"))
        
        # Should have exactly 3 successes (first join for each player)
        assert successes == 3
        assert failures == 6  # Duplicate join attempts
        
        # Verify room state is consistent
        room = async_room_manager._rooms[room_id]
        assert len(room.players) == 4  # Host + 3 players
        player_names = {p["name"] for p in room.players.values()}
        assert player_names == {"ConsistencyHost", "Player0", "Player1", "Player2"}
    
    def test_performance_summary(self):
        """Summary of performance expectations."""
        print("\n=== Async Performance Targets ===")
        print("- Room creation: < 50ms per room")
        print("- Player join: < 50ms per join")
        print("- Bot decision: < 50ms per decision")
        print("- Concurrent operations: Near-linear scaling")
        print("- Game operations: < 100ms for most operations")
        print("- Stress test: < 1s for 100+ operations")
        print("================================\n")