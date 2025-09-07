#!/usr/bin/env python3
"""
Integration test for EventBuffer with actual game flow
"""

import asyncio
import os
import sys
import sqlite3
from pathlib import Path
import pytest

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.services.event_store import EventStore
from engine.game import Game
from engine.player import Player


class TestBufferIntegration:
    """Integration tests for EventBuffer with game flow"""

    @pytest.fixture
    async def setup_game(self):
        """Setup a test game with event store"""
        # Enable buffer for testing
        os.environ["EVENT_BUFFER_ENABLED"] = "true"
        os.environ["EVENT_BUFFER_SIZE"] = "10"  # Smaller for testing
        os.environ["EVENT_BUFFER_FLUSH_INTERVAL"] = "1.0"  # Faster for testing

        # Create test database
        test_db = "/tmp/test_integration.db"
        if os.path.exists(test_db):
            os.remove(test_db)

        # Create event store
        event_store = EventStore(db_path=test_db)

        # Create game with players
        players = [Player(f"Player{i}", is_bot=(i > 0)) for i in range(4)]
        game = Game(players)

        yield game, event_store, test_db

        # Cleanup
        await event_store.shutdown()
        if os.path.exists(test_db):
            os.remove(test_db)

    @pytest.mark.asyncio
    async def test_game_round_with_buffer(self, setup_game):
        """Test that a full game round works with buffered events"""
        game, event_store, test_db = setup_game
        room_id = "TEST_ROOM"

        # Simulate game events
        events_to_store = []

        # 1. Game start
        await event_store.store_event_buffered(
            room_id, "game_started", {"players": [p.name for p in game.players]}
        )
        events_to_store.append("game_started")

        # 2. Round start
        await event_store.store_event_buffered(
            room_id, "round_started", {"round": 1, "starter": game.players[0].name}
        )
        events_to_store.append("round_started")

        # 3. Hands dealt
        await event_store.store_event_buffered(room_id, "hands_dealt", {"round": 1})
        events_to_store.append("hands_dealt")

        # 4. Declarations (4 players)
        for i, player in enumerate(game.players):
            await event_store.store_event_buffered(
                room_id,
                "player_declared",
                {"player": player.name, "value": i},
                player_id=player.name,
            )
            events_to_store.append("player_declared")

        # 5. Multiple turns (simulate 4 turns)
        for turn in range(4):
            # Turn start
            await event_store.store_event_buffered(
                room_id, "turn_started", {"turn": turn + 1}
            )
            events_to_store.append("turn_started")

            # Players play
            for player in game.players:
                await event_store.store_event_buffered(
                    room_id,
                    "pieces_played",
                    {"player": player.name, "count": 1},
                    player_id=player.name,
                )
                events_to_store.append("pieces_played")

            # Turn complete
            await event_store.store_event_buffered(
                room_id,
                "turn_complete",
                {"turn": turn + 1, "winner": game.players[0].name},
            )
            events_to_store.append("turn_complete")

        # 6. Round complete (critical event - triggers flush)
        await event_store.store_event_buffered(
            room_id,
            "round_complete",
            {"round": 1, "scores": {p.name: 10 for p in game.players}},
        )
        events_to_store.append("round_complete")

        # Wait a bit for any async operations
        await asyncio.sleep(0.1)

        # Verify buffer metrics
        metrics = event_store.get_buffer_metrics()
        assert metrics["total_buffered"] == len(events_to_store)
        assert metrics["total_flushes"] >= 1  # At least one flush from round_complete

        # Force final flush to ensure all events are written
        await event_store.shutdown()

        # Verify all events were stored
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("SELECT COUNT(*) FROM game_events")
        total_events = cursor.fetchone()[0]

        # Check event types
        cursor = conn.execute(
            "SELECT event_type, COUNT(*) FROM game_events GROUP BY event_type"
        )
        event_counts = dict(cursor.fetchall())
        conn.close()

        # Assertions
        assert total_events == len(events_to_store)
        assert event_counts["game_started"] == 1
        assert event_counts["round_started"] == 1
        assert event_counts["hands_dealt"] == 1
        assert event_counts["player_declared"] == 4
        assert event_counts["turn_started"] == 4
        assert event_counts["pieces_played"] == 16  # 4 players × 4 turns
        assert event_counts["turn_complete"] == 4
        assert event_counts["round_complete"] == 1

    @pytest.mark.asyncio
    async def test_critical_events_bypass_buffer(self, setup_game):
        """Test that critical events bypass the buffer"""
        game, event_store, test_db = setup_game
        room_id = "TEST_CRITICAL"

        # Add some regular events to buffer
        for i in range(5):
            await event_store.store_event_buffered(
                room_id, "phase_change", {"phase": f"test_{i}"}
            )

        # Check buffer has events
        metrics = event_store.get_buffer_metrics()
        assert metrics["buffer_size"] > 0

        # Store critical event
        await event_store.store_event_buffered(
            room_id, "game_over", {"winner": "Player1", "scores": {}}
        )

        # Critical event should be written immediately
        conn = sqlite3.connect(test_db)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM game_events WHERE event_type = 'game_over'"
        )
        game_over_count = cursor.fetchone()[0]
        conn.close()

        assert game_over_count == 1

    @pytest.mark.asyncio
    async def test_buffer_preserves_event_order(self, setup_game):
        """Test that events maintain correct order through buffer"""
        game, event_store, test_db = setup_game
        room_id = "TEST_ORDER"

        # Store events with sequence numbers
        expected_order = []
        for i in range(20):
            event_type = f"event_{i % 3}"  # Vary event types
            await event_store.store_event_buffered(
                room_id, event_type, {"sequence": i, "data": f"test_{i}"}
            )
            expected_order.append((event_type, i))

        # Force flush
        await event_store.shutdown()

        # Verify order is preserved
        conn = sqlite3.connect(test_db)
        cursor = conn.execute(
            """
            SELECT event_type, json_extract(payload, '$.sequence') as seq
            FROM game_events
            WHERE room_id = ?
            ORDER BY sequence ASC
            """,
            (room_id,),
        )

        actual_order = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()

        assert actual_order == expected_order

    @pytest.mark.asyncio
    async def test_buffer_handles_concurrent_games(self, setup_game):
        """Test buffer handles multiple concurrent games correctly"""
        game, event_store, test_db = setup_game

        # Simulate 3 concurrent games
        room_ids = ["ROOM_A", "ROOM_B", "ROOM_C"]

        async def simulate_game_events(room_id, game_num):
            """Simulate events for one game"""
            for i in range(10):
                await event_store.store_event_buffered(
                    room_id, "phase_change", {"game": game_num, "event": i}
                )
                # Small delay to simulate real game timing
                await asyncio.sleep(0.01)

        # Run games concurrently
        tasks = [simulate_game_events(room_id, i) for i, room_id in enumerate(room_ids)]
        await asyncio.gather(*tasks)

        # Force flush
        await event_store.shutdown()

        # Verify each game has correct events
        conn = sqlite3.connect(test_db)
        for i, room_id in enumerate(room_ids):
            cursor = conn.execute(
                "SELECT COUNT(*) FROM game_events WHERE room_id = ?", (room_id,)
            )
            count = cursor.fetchone()[0]
            assert count == 10, f"Room {room_id} should have 10 events, got {count}"

        # Verify total events
        cursor = conn.execute("SELECT COUNT(*) FROM game_events")
        total = cursor.fetchone()[0]
        conn.close()

        assert total == 30, f"Should have 30 total events, got {total}"


if __name__ == "__main__":
    # Run specific test
    import sys

    if len(sys.argv) > 1:
        pytest.main([__file__, "-v", "-k", sys.argv[1]])
    else:
        pytest.main([__file__, "-v"])
