# backend/tests/api/test_compact_format.py
"""
Test compact format option for play history API.
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


class TestCompactFormat:
    """Test compact format response option."""
    
    async def setup_test_room(self):
        """Create a test room with game data."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        
        # Create room and game
        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)
        
        # Set up game
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "SCORING"
        room.game.starter_index = 0
        
        # Set up basic data
        for i, player in enumerate(players):
            player.hand = [
                Piece("GENERAL_RED") if i == 0 else Piece("ADVISOR_BLACK"),
                Piece("HORSE_RED"),
                Piece("CANNON_BLACK"),
                Piece("SOLDIER_RED"),
                Piece("SOLDIER_BLACK"),
                Piece("SOLDIER_BLACK"),
                Piece("SOLDIER_BLACK"),
                Piece("SOLDIER_BLACK"),
            ]
            player.declared = [2, 3, 2, 1][i]
            player.captured_piles = [1, 3, 2, 2][i]
            player.score = [5, 10, 8, 12][i]
        
        room.game.declarations = {
            "Bot 1": 2,
            "Bot 2": 3,
            "Bot 3": 2,
            "Bot 4": 1,
        }
        
        return room_id
    
    def test_full_format_default(self):
        """Test that full format is returned by default."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Get play history without format parameter
        response = client.get(f"/api/rooms/{room_id}/play-history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Full format should include all details
        assert "players" in data
        assert "rounds" in data
        
        round_data = data["rounds"][0]
        assert "initial_state" in round_data
        assert "hands_dealt" in round_data
        assert "declaration_phase" in round_data
        assert "turn_history" in round_data
        assert "round_summary" in round_data
        
        # Hands should be included by default
        assert len(round_data["hands_dealt"]) > 0
    
    def test_compact_format_basic(self):
        """Test compact format returns minimal data."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Get play history with compact format
        # Note: To get truly compact output, we need to explicitly set include_hands=false
        # because include_hands defaults to true
        response = client.get(f"/api/rooms/{room_id}/play-history?format=compact&include_hands=false")
        
        assert response.status_code == 200
        data = response.json()
        
        # Compact format should have basic structure
        assert "room_id" in data
        assert "total_rounds" in data
        assert "rounds" in data
        
        # Check compact round data
        round_data = data["rounds"][0]
        assert "round_number" in round_data
        assert "round_summary" in round_data  # Always include summary
        
        # These verbose fields should be excluded or minimized
        assert "hands_dealt" not in round_data or round_data["hands_dealt"] == {}
        assert "turn_history" not in round_data or len(round_data["turn_history"]) == 0
    
    def test_compact_format_default_includes_hands(self):
        """Test that compact format includes hands by default due to include_hands=true default."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Get play history with compact format (no include_hands specified)
        response = client.get(f"/api/rooms/{room_id}/play-history?format=compact")
        
        assert response.status_code == 200
        data = response.json()
        
        round_data = data["rounds"][0]
        # Because include_hands defaults to true, compact format will still have hands
        assert "hands_dealt" in round_data
        assert len(round_data["hands_dealt"]) > 0
        
        # But turn history should still be excluded
        assert "turn_history" in round_data
        assert len(round_data["turn_history"]) == 0
    
    def test_compact_format_with_includes(self):
        """Test compact format can be combined with include parameters."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Compact format but include hands
        response = client.get(
            f"/api/rooms/{room_id}/play-history?format=compact&include_hands=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        round_data = data["rounds"][0]
        # Even in compact format, if include_hands=true, hands should be there
        assert "hands_dealt" in round_data
        assert len(round_data["hands_dealt"]) > 0
    
    def test_compact_summary_format(self):
        """Test compact format provides essential scoring info."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        response = client.get(f"/api/rooms/{room_id}/play-history?format=compact")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still have player info
        assert len(data["players"]) == 4
        
        # Round summary should be complete
        summary = data["rounds"][0]["round_summary"]
        assert "final_captures" in summary
        assert "scoring" in summary
        assert "cumulative_scores" in summary
        
        # Verify essential data is preserved
        assert summary["final_captures"]["Bot 1"]["captured"] == 1
        assert summary["final_captures"]["Bot 1"]["declared"] == 2
        assert summary["cumulative_scores"]["Bot 1"] == 5
    
    def test_invalid_format_parameter(self):
        """Test invalid format parameter is handled gracefully."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Invalid format should be ignored and return full format
        response = client.get(f"/api/rooms/{room_id}/play-history?format=invalid")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return full format when invalid format is specified
        round_data = data["rounds"][0]
        assert "initial_state" in round_data
        assert "hands_dealt" in round_data
        assert "declaration_phase" in round_data
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, 'rooms'):
            shared_room_manager.rooms.clear()