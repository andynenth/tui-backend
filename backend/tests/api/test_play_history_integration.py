# backend/tests/api/test_play_history_integration.py
"""
Integration tests for play history API with actual game data.
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


class TestPlayHistoryIntegration:
    """Integration tests with actual game data."""
    
    async def setup_test_room(self):
        """Create a test room with a game."""
        # Create players
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        
        # Create room
        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)
        
        # Add players
        for player in players:
            room.slots[players.index(player)] = {
                "name": player.name,
                "is_bot": player.is_bot,
                "is_ready": True
            }
        
        # Create game
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "SCORING"
        room.game.starter_index = 0
        
        # Set up some test data
        for i, player in enumerate(players):
            # Give each player a hand
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
            
            # Set declarations and captures
            player.declared = [4, 2, 2, 0][i]
            player.captured_piles = [2, 3, 2, 1][i]
            player.score = [10, 15, 8, 12][i]
        
        # Set up game declarations (for extraction)
        room.game.declarations = {
            "Bot 1": 4,
            "Bot 2": 2,
            "Bot 3": 2,
            "Bot 4": 0,
        }
        
        # Set round scores
        room.game.round_scores = {
            "Bot 1": -4,
            "Bot 2": 2,
            "Bot 3": 0,
            "Bot 4": 2,
        }
        
        return room_id
    
    def test_play_history_with_game_data(self):
        """Test play history endpoint with actual game data."""
        # Setup room in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Get play history
        response = client.get(f"/api/rooms/{room_id}/play-history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["room_id"] == room_id
        assert data["total_rounds"] == 1
        assert len(data["players"]) == 4
        assert len(data["rounds"]) == 1
        
        # Verify player info
        assert "Bot 1" in data["players"]
        assert data["players"]["Bot 1"]["player_type"] == "ai"
        assert data["players"]["Bot 1"]["ai_version"] == "v2"
        
        # Verify round data
        round_data = data["rounds"][0]
        assert round_data["round_number"] == 1
        
        # Verify initial state
        assert round_data["initial_state"]["starter"]["player_name"] == "Bot 1"
        assert round_data["initial_state"]["starter"]["reason"] == "has_general_red"
        assert round_data["initial_state"]["player_order"] == ["Bot 1", "Bot 2", "Bot 3", "Bot 4"]
        
        # Verify hands are sorted correctly
        bot1_hand = round_data["hands_dealt"]["Bot 1"]
        assert bot1_hand[0]["kind"] == "GENERAL_RED"  # RED first, highest value
        assert bot1_hand[0]["point"] == 14
        
        # Verify declaration phase
        assert round_data["declaration_phase"]["total_declared"] == 8
        assert len(round_data["declaration_phase"]["declarations"]) == 4
        assert round_data["declaration_phase"]["pile_room_calculation"]["Bot 1"] == 8
        assert round_data["declaration_phase"]["pile_room_calculation"]["Bot 4"] == 0
        
        # Verify round summary
        assert round_data["round_summary"]["total_turns"] == 8
        assert round_data["round_summary"]["final_captures"]["Bot 1"]["declared"] == 4
        assert round_data["round_summary"]["final_captures"]["Bot 1"]["captured"] == 2
        assert round_data["round_summary"]["scoring"]["Bot 1"]["points"] == -4
        assert round_data["round_summary"]["cumulative_scores"]["Bot 1"] == 10
    
    def test_query_parameters(self):
        """Test query parameter filtering."""
        # Setup room
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(self.setup_test_room())
        
        # Test include_hands=false
        response = client.get(f"/api/rooms/{room_id}/play-history?include_hands=false")
        assert response.status_code == 200
        data = response.json()
        assert data["rounds"][0]["hands_dealt"] == {}
        
        # Test specific rounds (should be empty as we only have round 1)
        response = client.get(f"/api/rooms/{room_id}/play-history?rounds=2,3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["rounds"]) == 0
        
        # Test specific round that exists
        response = client.get(f"/api/rooms/{room_id}/play-history?rounds=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["rounds"]) == 1
        assert data["rounds"][0]["round_number"] == 1
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clear any test rooms
        if hasattr(shared_room_manager, 'rooms'):
            shared_room_manager.rooms.clear()