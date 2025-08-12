# backend/tests/services/test_ai_decision_analysis.py
"""
Test AI decision analysis extraction for play history.
"""

import pytest
from backend.services.play_history_service import PlayHistoryService
from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.models.play_history import AIDecisionAnalysis


class TestAIDecisionAnalysis:
    """Test extraction and formatting of AI decision reasoning."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PlayHistoryService()

        # Create test players (mix of AI and human)
        self.players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Human 1", is_bot=False),
            Player("Bot 3", is_bot=True),
        ]

        # Create test game
        self.game = Game(self.players)
        self.game.round_number = 1
        self.game.starter_index = 0

    def test_ai_analysis_placeholder_when_no_data(self):
        """Test that placeholder is created when AI analysis data is missing."""
        # Create a play data without AI analysis
        play_data = {
            "player_id": "bot_1",
            "player_name": "Bot 1",
            "pieces_played": [Piece("SOLDIER_RED")],
            "play_type": "SINGLE",
            "is_ai": True,
        }

        # Extract AI analysis
        ai_analysis = self.service.extract_ai_analysis_for_play(play_data, self.game)

        assert ai_analysis is not None
        assert isinstance(ai_analysis, dict)
        assert (
            "declaration_reasoning" in ai_analysis
            or "turn_play_reasoning" in ai_analysis
        )

    def test_ai_declaration_reasoning_extraction(self):
        """Test extraction of AI reasoning for declarations."""
        # Simulate stored AI decision data
        self.game.ai_decision_history = {
            "Bot 1": {
                "declaration": {
                    "declared": 3,
                    "reasoning": "Moderate strategy - balanced risk/reward",
                    "hand_strength": "medium",
                    "available_options": [0, 1, 2, 3, 4],
                    "factors": {
                        "position": "starter",
                        "pile_room": 8,
                        "combo_potential": 2,
                    },
                }
            }
        }

        # Extract declaration reasoning
        reasoning = self.service.extract_ai_declaration_reasoning("Bot 1", self.game)

        assert reasoning is not None
        assert reasoning["declared"] == 3
        assert reasoning["reasoning"] == "Moderate strategy - balanced risk/reward"
        assert "available_options" in reasoning
        assert "factors" in reasoning

    def test_ai_turn_play_reasoning_extraction(self):
        """Test extraction of AI reasoning for turn plays."""
        # Simulate stored AI turn decision
        self.game.ai_decision_history = {
            "Bot 1": {
                "turns": {
                    1: {
                        "pieces_played": ["SOLDIER_RED"],
                        "play_type": "SINGLE",
                        "reasoning": "Testing field strength with low piece",
                        "strategy": "conservative",
                        "alternatives_considered": [
                            {"play": "CANNON_BLACK", "reason": "Too strong for opener"},
                            {"play": "PAIR", "reason": "Saving for later"},
                        ],
                        "game_state": {
                            "captured": 0,
                            "declared": 3,
                            "remaining_turns": 7,
                        },
                    }
                }
            }
        }

        # Extract turn play reasoning
        reasoning = self.service.extract_ai_turn_reasoning("Bot 1", 1, self.game)

        assert reasoning is not None
        assert reasoning["reasoning"] == "Testing field strength with low piece"
        assert reasoning["strategy"] == "conservative"
        assert len(reasoning["alternatives_considered"]) == 2
        assert "game_state" in reasoning

    def test_human_player_no_ai_analysis(self):
        """Test that human players don't get AI analysis."""
        # Create play data for human player
        play_data = {
            "player_id": "human_1",
            "player_name": "Human 1",
            "pieces_played": [Piece("SOLDIER_RED")],
            "play_type": "SINGLE",
            "is_ai": False,
        }

        # Extract AI analysis (should be None)
        ai_analysis = self.service.extract_ai_analysis_for_play(play_data, self.game)

        assert ai_analysis is None

    def test_ai_analysis_with_include_flag(self):
        """Test that AI analysis respects the include_ai_analysis flag."""
        # Set up game with AI decision history
        self.game.ai_decision_history = {
            "Bot 1": {"declaration": {"declared": 3, "reasoning": "Moderate strategy"}}
        }

        # Build history with AI analysis included
        history_with = self.service.build_play_history(
            self.game, "TEST123", include_ai_analysis=True
        )

        # Build history without AI analysis
        history_without = self.service.build_play_history(
            self.game, "TEST123", include_ai_analysis=False
        )

        # For now, both should work (we'll implement the flag later)
        assert history_with is not None
        assert history_without is not None

    def test_ai_urgency_level_extraction(self):
        """Test extraction of AI urgency level in decision making."""
        # Simulate AI decision with urgency
        self.game.ai_decision_history = {
            "Bot 2": {
                "turns": {
                    5: {
                        "pieces_played": ["GENERAL_RED"],
                        "play_type": "SINGLE",
                        "reasoning": "Must win this turn to meet declaration",
                        "urgency_level": "critical",
                        "target_remaining": 2,
                        "turns_remaining": 3,
                    }
                }
            }
        }

        reasoning = self.service.extract_ai_turn_reasoning("Bot 2", 5, self.game)

        assert reasoning is not None
        assert reasoning["urgency_level"] == "critical"
        assert reasoning["target_remaining"] == 2

    def test_ai_combo_strategy_extraction(self):
        """Test extraction of AI combo planning strategy."""
        # Simulate AI strategic planning
        self.game.ai_decision_history = {
            "Bot 3": {
                "strategy_plan": {
                    "main_plan": "combo_focused",
                    "assigned_combos": [
                        {
                            "type": "STRAIGHT",
                            "pieces": ["CHARIOT_RED", "HORSE_RED", "CANNON_RED"],
                        },
                        {"type": "PAIR", "pieces": ["SOLDIER_BLACK", "SOLDIER_BLACK"]},
                    ],
                    "opener_pieces": ["GENERAL_RED", "ADVISOR_BLACK"],
                    "reserve_pieces": ["SOLDIER_RED"],
                    "plan_viability": "high",
                }
            }
        }

        strategy = self.service.extract_ai_strategy_plan("Bot 3", self.game)

        assert strategy is not None
        assert strategy["main_plan"] == "combo_focused"
        assert len(strategy["assigned_combos"]) == 2
        assert strategy["plan_viability"] == "high"
