# backend/tests/services/test_round_data_extraction.py
"""
TDD: Tests for extracting round data from game state.
"""

import pytest
from backend.services.play_history_service import PlayHistoryService
from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece


class TestRoundDataExtraction:
    """Test extraction of round data from game state."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PlayHistoryService()
        
        # Create a simple game with known state
        self.players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        self.game = Game(self.players)
    
    def test_extract_initial_state_first_round(self):
        """Test extracting initial state for first round (GENERAL_RED starter)."""
        # Give Bot 2 the GENERAL_RED piece
        self.players[1].hand = [
            Piece("GENERAL_RED"),
            Piece("ADVISOR_BLACK"),
            Piece("HORSE_RED"),
            Piece("CANNON_BLACK"),
            Piece("SOLDIER_RED"),
            Piece("SOLDIER_BLACK"),
            Piece("SOLDIER_BLACK"),
            Piece("SOLDIER_BLACK"),
        ]
        
        # Set game state
        self.game.round_number = 1
        self.game.starter_index = 1  # Bot 2 starts
        
        initial_state = self.service.extract_initial_state(self.game, 1)
        
        assert initial_state.starter.player_id == "bot_2"
        assert initial_state.starter.player_name == "Bot 2"
        assert initial_state.starter.reason == "has_general_red"
        assert initial_state.starter.highest_card == "GENERAL_RED(14)"
        assert initial_state.player_order == ["Bot 2", "Bot 3", "Bot 4", "Bot 1"]
    
    def test_extract_initial_state_later_round(self):
        """Test extracting initial state for later rounds (winner starts)."""
        # Set game state for round 3
        self.game.round_number = 3
        self.game.starter_index = 2  # Bot 3 starts
        self.game.rounds = [
            {"winner": None},  # Round 1 data
            {"winner": "Bot 3"},  # Round 2 - Bot 3 won
        ]
        
        initial_state = self.service.extract_initial_state(self.game, 3)
        
        assert initial_state.starter.player_id == "bot_3"
        assert initial_state.starter.player_name == "Bot 3"
        assert initial_state.starter.reason == "won_previous_round"
        assert initial_state.starter.highest_card is None
        assert initial_state.player_order == ["Bot 3", "Bot 4", "Bot 1", "Bot 2"]
    
    def test_extract_hands_dealt(self):
        """Test extracting and sorting initial hands."""
        # Set up known hands for all players
        self.players[0].hand = [
            Piece("SOLDIER_BLACK"),    # 1
            Piece("GENERAL_RED"),      # 14
            Piece("ADVISOR_BLACK"),    # 11
            Piece("HORSE_RED"),        # 6
            Piece("CANNON_BLACK"),     # 3
            Piece("ELEPHANT_RED"),     # 10
            Piece("CHARIOT_BLACK"),    # 7
            Piece("SOLDIER_RED"),      # 2
        ]
        
        # Store initial hands in game (assuming this is how they're stored)
        self.game.initial_hands = {
            "Bot 1": self.players[0].hand.copy()
        }
        
        hands_dealt = self.service.extract_hands_dealt(self.game, 1)
        
        # Check Bot 1's hand is sorted correctly
        bot1_hand = hands_dealt["Bot 1"]
        assert len(bot1_hand) == 8
        
        # Should be sorted: RED first (14,10,6,2), then BLACK (11,7,3,1)
        expected_order = [
            ("GENERAL_RED", 14),
            ("ELEPHANT_RED", 10),
            ("HORSE_RED", 6),
            ("SOLDIER_RED", 2),
            ("ADVISOR_BLACK", 11),
            ("CHARIOT_BLACK", 7),
            ("CANNON_BLACK", 3),
            ("SOLDIER_BLACK", 1),
        ]
        
        for i, piece_info in enumerate(bot1_hand):
            assert piece_info.kind == expected_order[i][0]
            assert piece_info.point == expected_order[i][1]
    
    def test_extract_declaration_phase(self):
        """Test extracting declaration phase data."""
        # Set up declaration data in game
        self.game.declarations = {
            "Bot 1": 4,
            "Bot 2": 2,
            "Bot 3": 2,
            "Bot 4": 0,
        }
        
        # Bot 1 has GENERAL_RED
        self.players[0].hand = [Piece("GENERAL_RED")]
        self.game.starter_index = 0
        
        declaration_info = self.service.extract_declaration_phase(self.game, 1)
        
        assert len(declaration_info.declarations) == 4
        assert declaration_info.total_declared == 8
        
        # Check first declaration (starter)
        first_decl = declaration_info.declarations[0]
        assert first_decl.player_id == "bot_1"
        assert first_decl.declared == 4
        assert first_decl.position == 0
        assert "starter" in first_decl.strategy_notes.lower()
        
        # Check pile room calculations
        assert declaration_info.pile_room_calculation["Bot 1"] == 8  # Starter
        assert declaration_info.pile_room_calculation["Bot 2"] == 4  # 8-4
        assert declaration_info.pile_room_calculation["Bot 3"] == 2  # 8-4-2
        assert declaration_info.pile_room_calculation["Bot 4"] == 0  # 8-4-2-2
    
    def test_pile_room_with_general_red(self):
        """Test pile room calculation with GENERAL_RED special rule."""
        # Set up declarations
        self.game.declarations = {
            "Bot 1": 5,  # Starter
            "Bot 2": 2,
            "Bot 3": 1,
            "Bot 4": 0,
        }
        
        # Bot 3 has GENERAL_RED (not starter)
        self.players[2].hand = [Piece("GENERAL_RED")]
        self.game.starter_index = 0
        
        declaration_info = self.service.extract_declaration_phase(self.game, 1)
        
        # With GENERAL_RED, Bot 3 only counts starter's declaration
        assert declaration_info.pile_room_calculation["Bot 3"] == 3  # 8-5 (ignores Bot 2)
    
    def test_extract_round_summary(self):
        """Test extracting round summary with scoring."""
        # Set up round end state
        for i, player in enumerate(self.players):
            player.declared = [4, 2, 2, 0][i]
            player.captured_piles = [2, 3, 2, 1][i]
        
        # Set up scoring data (usually calculated by game)
        self.game.round_scores = {
            "Bot 1": -4,  # Declared 4, got 2 (-2 diff * 2 multiplier)
            "Bot 2": 2,   # Declared 2, got 3 (+1 diff * 2 multiplier)
            "Bot 3": 0,   # Declared 2, got 2 (exact match)
            "Bot 4": 2,   # Declared 0, got 1 (+1 diff * 2 multiplier)
        }
        
        # Set cumulative scores
        for i, player in enumerate(self.players):
            player.score = [6, 17, 8, 12][i]
        
        round_summary = self.service.extract_round_summary(self.game, 1)
        
        assert round_summary.total_turns == 8  # Default 8 turns per round
        
        # Check final captures
        assert round_summary.final_captures["Bot 1"].captured == 2
        assert round_summary.final_captures["Bot 1"].declared == 4
        assert round_summary.final_captures["Bot 1"].difference == -2
        
        # Check scoring
        assert round_summary.scoring["Bot 1"].points == -4
        assert round_summary.scoring["Bot 1"].multiplier == 2
        assert round_summary.scoring["Bot 1"].reason == "missed_by_2"
        
        assert round_summary.scoring["Bot 3"].points == 0
        assert round_summary.scoring["Bot 3"].multiplier == 0
        assert round_summary.scoring["Bot 3"].reason == "exact_match"
        
        # Check cumulative scores
        assert round_summary.cumulative_scores["Bot 1"] == 6
        assert round_summary.cumulative_scores["Bot 2"] == 17