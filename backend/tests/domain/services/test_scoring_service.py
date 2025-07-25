"""
Tests for the ScoringService domain service.
"""

import pytest
from domain.services.scoring_service import ScoringService, RoundScore, RoundResult
from domain.entities.player import Player


class TestScoringService:
    """Test the ScoringService domain service."""
    
    def test_calculate_base_score_zero_success(self):
        """Test scoring when declaring 0 and achieving 0."""
        score = ScoringService.calculate_base_score(declared=0, actual=0)
        assert score == 3  # Zero declaration success bonus
    
    def test_calculate_base_score_zero_failure(self):
        """Test scoring when declaring 0 but capturing piles."""
        score = ScoringService.calculate_base_score(declared=0, actual=2)
        assert score == -2  # Penalty equals actual piles
        
        score = ScoringService.calculate_base_score(declared=0, actual=5)
        assert score == -5
    
    def test_calculate_base_score_perfect_prediction(self):
        """Test scoring for perfect non-zero predictions."""
        score = ScoringService.calculate_base_score(declared=3, actual=3)
        assert score == 8  # 3 + 5 bonus
        
        score = ScoringService.calculate_base_score(declared=7, actual=7)
        assert score == 12  # 7 + 5 bonus
    
    def test_calculate_base_score_missed_target(self):
        """Test scoring when missing the target."""
        # Declared more than captured
        score = ScoringService.calculate_base_score(declared=5, actual=3)
        assert score == -2  # -abs(5-3)
        
        # Declared less than captured
        score = ScoringService.calculate_base_score(declared=2, actual=6)
        assert score == -4  # -abs(2-6)
    
    def test_round_score_value_object(self):
        """Test RoundScore value object."""
        score = RoundScore(
            player_name="Alice",
            declared_piles=3,
            actual_piles=3,
            base_score=8,
            multiplier=1.5,
            final_score=12,
            is_perfect_round=True
        )
        
        assert score.player_name == "Alice"
        assert score.is_perfect_round is True
        assert score.final_score == 12
        
        # Test immutability
        with pytest.raises(AttributeError):
            score.final_score = 15
        
        # Test to_dict
        data = score.to_dict()
        assert data["player_name"] == "Alice"
        assert data["is_perfect_round"] is True
    
    def test_calculate_round_scores(self):
        """Test calculating scores for a full round."""
        # Create players
        players = [
            Player(name="Alice"),
            Player(name="Bob"),
            Player(name="Carol"),
            Player(name="Dave")
        ]
        
        # Set declarations
        players[0].declare_piles(3, "room123")  # Alice declares 3
        players[1].declare_piles(0, "room123")  # Bob declares 0
        players[2].declare_piles(2, "room123")  # Carol declares 2
        players[3].declare_piles(3, "room123")  # Dave declares 3
        
        # Set actual captures
        piles_captured = {
            "Alice": 3,  # Perfect
            "Bob": 0,    # Perfect zero
            "Carol": 4,  # Missed (declared 2, got 4)
            "Dave": 1    # Missed (declared 3, got 1)
        }
        
        # Calculate scores
        result = ScoringService.calculate_round_scores(
            players=players,
            piles_captured=piles_captured,
            redeal_multiplier=1.0,
            round_number=1
        )
        
        assert isinstance(result, RoundResult)
        assert result.round_number == 1
        assert result.redeal_multiplier == 1.0
        assert len(result.player_scores) == 4
        
        # Check individual scores
        scores_by_name = {s.player_name: s for s in result.player_scores}
        
        # Alice: declared 3, got 3 = 3 + 5 = 8
        assert scores_by_name["Alice"].base_score == 8
        assert scores_by_name["Alice"].final_score == 8
        assert scores_by_name["Alice"].is_perfect_round is True
        
        # Bob: declared 0, got 0 = 3
        assert scores_by_name["Bob"].base_score == 3
        assert scores_by_name["Bob"].final_score == 3
        assert scores_by_name["Bob"].is_perfect_round is False
        
        # Carol: declared 2, got 4 = -2
        assert scores_by_name["Carol"].base_score == -2
        assert scores_by_name["Carol"].final_score == -2
        assert scores_by_name["Carol"].is_perfect_round is False
        
        # Dave: declared 3, got 1 = -2
        assert scores_by_name["Dave"].base_score == -2
        assert scores_by_name["Dave"].final_score == -2
        assert scores_by_name["Dave"].is_perfect_round is False
        
        # Round winner should be Alice (highest score)
        assert result.winner_name == "Alice"
    
    def test_calculate_round_scores_with_multiplier(self):
        """Test score calculation with redeal multiplier."""
        players = [
            Player(name="Alice"),
            Player(name="Bob")
        ]
        
        players[0].declare_piles(2, "room123")
        players[1].declare_piles(0, "room123")
        
        piles_captured = {
            "Alice": 2,  # Perfect = 2 + 5 = 7
            "Bob": 1     # Failed zero = -1
        }
        
        # With 1.5x multiplier
        result = ScoringService.calculate_round_scores(
            players=players,
            piles_captured=piles_captured,
            redeal_multiplier=1.5,
            round_number=2
        )
        
        scores_by_name = {s.player_name: s for s in result.player_scores}
        
        # Alice: 7 * 1.5 = 10.5 -> 10 (integer)
        assert scores_by_name["Alice"].base_score == 7
        assert scores_by_name["Alice"].final_score == 10
        
        # Bob: -1 * 1.5 = -1.5 -> -1 (integer)
        assert scores_by_name["Bob"].base_score == -1
        assert scores_by_name["Bob"].final_score == -1
    
    def test_get_score_deltas(self):
        """Test getting score deltas from round result."""
        result = RoundResult(
            round_number=1,
            player_scores=[
                RoundScore("Alice", 3, 3, 8, 1.0, 8, True),
                RoundScore("Bob", 0, 0, 3, 1.0, 3, False),
                RoundScore("Carol", 2, 1, -1, 1.0, -1, False)
            ],
            redeal_multiplier=1.0,
            winner_name="Alice"
        )
        
        deltas = result.get_score_deltas()
        assert deltas == {
            "Alice": 8,
            "Bob": 3,
            "Carol": -1
        }
    
    def test_calculate_final_standings(self):
        """Test calculating final game standings."""
        players = [
            Player(name="Alice"),
            Player(name="Bob"),
            Player(name="Carol")
        ]
        
        # Set scores and stats
        players[0].update_score(45, "room123", "Final")
        players[0].stats.perfect_rounds = 3
        players[0].stats.turns_won = 12
        
        players[1].update_score(52, "room123", "Final")
        players[1].stats.perfect_rounds = 4
        players[1].stats.turns_won = 15
        
        players[2].update_score(38, "room123", "Final")
        players[2].stats.perfect_rounds = 2
        players[2].stats.turns_won = 10
        
        standings = ScoringService.calculate_final_standings(players)
        
        # Should be sorted by score (highest first)
        assert len(standings) == 3
        assert standings[0]["name"] == "Bob"
        assert standings[0]["score"] == 52
        assert standings[0]["rank"] == 1
        
        assert standings[1]["name"] == "Alice"
        assert standings[1]["score"] == 45
        assert standings[1]["rank"] == 2
        
        assert standings[2]["name"] == "Carol"
        assert standings[2]["score"] == 38
        assert standings[2]["rank"] == 3
    
    def test_is_perfect_round(self):
        """Test perfect round detection."""
        # Perfect rounds
        assert ScoringService.is_perfect_round(3, 3) is True
        assert ScoringService.is_perfect_round(7, 7) is True
        
        # Not perfect
        assert ScoringService.is_perfect_round(0, 0) is False  # Zero doesn't count
        assert ScoringService.is_perfect_round(3, 2) is False
        assert ScoringService.is_perfect_round(2, 4) is False
    
    def test_get_penalty_reason(self):
        """Test penalty reason descriptions."""
        # Failed zero declaration
        reason = ScoringService.get_penalty_reason(0, 2)
        assert reason == "Declared 0 but captured 2 pile(s)"
        
        # Captured more than declared
        reason = ScoringService.get_penalty_reason(3, 5)
        assert reason == "Captured 2 more pile(s) than declared"
        
        # Captured less than declared
        reason = ScoringService.get_penalty_reason(5, 2)
        assert reason == "Captured 3 fewer pile(s) than declared"
        
        # No penalty
        reason = ScoringService.get_penalty_reason(3, 3)
        assert reason == "No penalty"