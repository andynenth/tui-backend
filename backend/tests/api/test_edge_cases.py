# backend/tests/api/test_edge_cases.py
"""
Test edge cases for play history API.
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


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    async def create_empty_game_room(self):
        """Create a room with a game but no rounds played."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)

        # Set up game with no rounds completed
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "PREPARATION"  # Just started

        return room_id

    async def create_in_progress_game_room(self):
        """Create a room with a game in progress (mid-round)."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)

        # Set up game in the middle of a round
        room.game = Game(players)
        room.game.round_number = 2
        room.game.current_phase = "TURN"  # Mid-round

        # Add some completed round data
        room.game.round_history = {
            1: {
                "starter_index": 0,
                "declarations": {
                    "Bot 1": 2,
                    "Bot 2": 3,
                    "Bot 3": 2,
                    "Bot 4": 1,
                },
                "final_captures": {
                    "Bot 1": 1,
                    "Bot 2": 3,
                    "Bot 3": 2,
                    "Bot 4": 2,
                },
                "scores": {
                    "Bot 1": 5,
                    "Bot 2": 10,
                    "Bot 3": 8,
                    "Bot 4": 12,
                },
            }
        }

        # Set current round data
        for player in players:
            player.declared = 2
            player.captured_piles = 1  # In progress
            player.score = 10  # From round 1

        return room_id

    async def create_abandoned_game_room(self):
        """Create a room with an abandoned game (missing data)."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)

        # Set up game with incomplete/missing data
        room.game = Game(players)
        room.game.round_number = 3
        room.game.current_phase = None  # Abandoned/unknown state

        # Missing some player data
        players[0].hand = None  # Missing hand
        players[1].declared = None  # Missing declaration

        return room_id

    def test_game_with_no_rounds(self):
        """Test handling of game with no completed rounds."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.create_empty_game_room())

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 200
        data = response.json()

        # Should return structure but with no rounds
        assert data["room_id"] == room_id
        assert data["total_rounds"] == 0
        assert len(data["rounds"]) == 0
        assert len(data["players"]) == 4

    def test_in_progress_round(self):
        """Test handling of in-progress round (not in SCORING phase)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.create_in_progress_game_room())

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 200
        data = response.json()

        # Should only return completed rounds
        assert data["total_rounds"] == 1
        assert len(data["rounds"]) == 1
        assert data["rounds"][0]["round_number"] == 1

        # Should not include round 2 (in progress)
        round_numbers = [r["round_number"] for r in data["rounds"]]
        assert 2 not in round_numbers

    def test_abandoned_game_with_missing_data(self):
        """Test handling of abandoned game with missing player data."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.create_abandoned_game_room())

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 200
        data = response.json()

        # Should handle missing data gracefully
        assert data["room_id"] == room_id
        assert "players" in data

        # Players should still be listed even with missing data
        assert len(data["players"]) == 4

    def test_room_with_null_game(self):
        """Test room that exists but has null game."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create room but don't start game
        room_id = loop.run_until_complete(
            shared_room_manager.create_room("Test Player")
        )
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = None  # Explicitly null

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 400
        assert "no active game" in response.json()["detail"]

    def test_game_with_corrupt_state(self):
        """Test game with corrupt/invalid state."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))

        # Create game with invalid state
        room.game = Game(players)
        room.game.round_number = -1  # Invalid round number
        room.game.current_phase = "INVALID_PHASE"  # Invalid phase

        response = client.get(f"/api/rooms/{room_id}/play-history")

        # Should handle gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["total_rounds"] == 0  # No valid rounds

    def test_empty_player_list(self):
        """Test game with empty player list."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        room_id = loop.run_until_complete(shared_room_manager.create_room("Test"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))

        # Create game with no players
        room.game = Game([])  # Empty player list
        room.game.round_number = 1

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 200
        data = response.json()
        assert len(data["players"]) == 0
        assert data["total_rounds"] == 0

    def test_missing_player_attributes(self):
        """Test players missing required attributes."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create players with missing attributes
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        # Remove some attributes
        delattr(players[0], "is_bot")  # Missing is_bot
        players[1].name = None  # Null name

        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)

        response = client.get(f"/api/rooms/{room_id}/play-history")

        # Should handle gracefully
        assert response.status_code == 200
        data = response.json()
        assert "players" in data

    def test_extremely_long_game(self):
        """Test game with many rounds (performance edge case)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        players = [Player(f"Bot {i+1}", is_bot=True) for i in range(4)]

        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)
        room.game.round_number = 50  # Very long game
        room.game.current_phase = "SCORING"

        # Create minimal round history for 50 rounds
        room.game.round_history = {}
        for round_num in range(1, 51):
            room.game.round_history[round_num] = {
                "starter_index": round_num % 4,
                "declarations": {f"Bot {i+1}": 2 for i in range(4)},
                "final_captures": {f"Bot {i+1}": 2 for i in range(4)},
                "scores": {f"Bot {i+1}": 5 for i in range(4)},
            }

        # Request only recent rounds
        response = client.get(f"/api/rooms/{room_id}/play-history?rounds=48,49,50")

        assert response.status_code == 200
        data = response.json()
        assert len(data["rounds"]) == 3
        assert data["rounds"][0]["round_number"] == 48

    def test_special_characters_in_player_names(self):
        """Test handling of special characters in player names."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Players with special characters
        players = [
            Player("Bot/1", is_bot=True),
            Player("Bot@2", is_bot=True),
            Player("Bot#3", is_bot=True),
            Player("Bot$4", is_bot=True),
        ]

        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot/1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "SCORING"

        response = client.get(f"/api/rooms/{room_id}/play-history")

        assert response.status_code == 200
        data = response.json()

        # Check player IDs are properly sanitized
        for player_name, player_info in data["players"].items():
            assert "/" not in player_info["player_id"]
            assert "@" not in player_info["player_id"]
            assert "#" not in player_info["player_id"]
            assert "$" not in player_info["player_id"]

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, "rooms"):
            shared_room_manager.rooms.clear()
