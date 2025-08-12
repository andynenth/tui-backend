# backend/tests/api/test_multi_round_endpoint.py
"""
Test multi-round endpoint for play history API.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.shared_instances import shared_room_manager
from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
import asyncio


client = TestClient(app)


class TestMultiRoundEndpoint:
    """Test multi-round play history endpoint."""

    async def setup_test_room_with_rounds(self, num_rounds: int = 3):
        """Create a test room with multiple completed rounds."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        # Create room and game
        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)

        # Set up game with multiple rounds
        room.game = Game(players)
        room.game.round_number = num_rounds
        room.game.current_phase = "SCORING"

        # Simulate round history storage
        room.game.round_history = {}

        for round_num in range(1, num_rounds + 1):
            # Store minimal round data
            room.game.round_history[round_num] = {
                "starter_index": (round_num - 1) % 4,
                "declarations": {
                    "Bot 1": 2,
                    "Bot 2": 3,
                    "Bot 3": 2,
                    "Bot 4": 1,
                },
                "final_captures": {
                    "Bot 1": [1, 2, 3, 2][round_num % 4],
                    "Bot 2": [3, 2, 1, 3][round_num % 4],
                    "Bot 3": [2, 3, 2, 1][round_num % 4],
                    "Bot 4": [2, 1, 2, 2][round_num % 4],
                },
                "scores": {
                    "Bot 1": round_num * 5,
                    "Bot 2": round_num * 8,
                    "Bot 3": round_num * 6,
                    "Bot 4": round_num * 7,
                },
            }

        # Set cumulative scores
        for player in players:
            player.score = sum(
                room.game.round_history[r]["scores"][player.name]
                for r in range(1, num_rounds + 1)
            )

        return room_id

    def test_get_rounds_range_basic(self):
        """Test getting a range of rounds."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(5))

        # Get rounds 2-4
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=2&to=4")

        assert response.status_code == 200
        data = response.json()

        # Should return 3 rounds (2, 3, 4)
        assert data["total_rounds"] == 3
        assert len(data["rounds"]) == 3

        # Verify round numbers
        round_numbers = [r["round_number"] for r in data["rounds"]]
        assert round_numbers == [2, 3, 4]

    def test_get_all_rounds(self):
        """Test getting all rounds when range covers entire game."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Get rounds 1-10 (more than available)
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1&to=10")

        assert response.status_code == 200
        data = response.json()

        # Should return only 3 rounds
        assert data["total_rounds"] == 3
        assert len(data["rounds"]) == 3

    def test_single_round_range(self):
        """Test getting a single round via range endpoint."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Get only round 2
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=2&to=2")

        assert response.status_code == 200
        data = response.json()

        assert data["total_rounds"] == 1
        assert len(data["rounds"]) == 1
        assert data["rounds"][0]["round_number"] == 2

    def test_invalid_range(self):
        """Test invalid range where from > to."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # from > to should return error
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=5&to=2")

        assert response.status_code == 400
        assert "'from' must be <= 'to'" in response.json()["detail"]

    def test_out_of_bounds_range(self):
        """Test range that's completely out of bounds."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Request rounds 10-15 when only 3 exist
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=10&to=15")

        assert response.status_code == 200
        data = response.json()

        # Should return empty list
        assert data["total_rounds"] == 0
        assert len(data["rounds"]) == 0

    def test_partial_range_overlap(self):
        """Test range that partially overlaps with available rounds."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(5))

        # Request rounds 4-8 when only 5 exist
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=4&to=8")

        assert response.status_code == 200
        data = response.json()

        # Should return rounds 4 and 5
        assert data["total_rounds"] == 2
        assert len(data["rounds"]) == 2
        assert [r["round_number"] for r in data["rounds"]] == [4, 5]

    def test_range_with_include_parameters(self):
        """Test range query with include_hands and include_ai_analysis."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Get rounds without hands or AI analysis
        response = client.get(
            f"/api/rooms/{room_id}/play-history/rounds?from=1&to=2"
            "&include_hands=false&include_ai_analysis=false"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify hands are excluded
        for round_data in data["rounds"]:
            assert round_data["hands_dealt"] == {}

    def test_range_with_compact_format(self):
        """Test range query with compact format."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Get rounds in compact format
        response = client.get(
            f"/api/rooms/{room_id}/play-history/rounds?from=1&to=3&format=compact"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify compact format
        for round_data in data["rounds"]:
            assert len(round_data["turn_history"]) == 0  # No turn history in compact

    def test_missing_to_parameter(self):
        """Test that 'to' parameter is required."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Missing 'to' parameter
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1")

        assert response.status_code == 422  # Validation error

    def test_negative_round_numbers(self):
        """Test that negative round numbers are rejected."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room_with_rounds(3))

        # Negative from
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=-1&to=2")
        assert response.status_code == 422

        # Negative to
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1&to=-2")
        assert response.status_code == 422

    def test_room_not_found(self):
        """Test range query for non-existent room."""
        response = client.get("/api/rooms/invalid-room/play-history/rounds?from=1&to=5")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_room_no_game(self):
        """Test range query for room without active game."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create room without game
        room_id = loop.run_until_complete(
            shared_room_manager.create_room("Test Player")
        )

        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1&to=5")

        assert response.status_code == 400
        assert "no active game" in response.json()["detail"]

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, "rooms"):
            shared_room_manager.rooms.clear()
