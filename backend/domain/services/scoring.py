# domain/services/scoring.py
"""
Domain service for score calculation.
Pure business logic for scoring rules.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass(frozen=True)
class RoundScore:
    """Value object representing a player's score for a round."""
    player_name: str
    declared: int
    actual: int
    base_score: int
    multiplier: int
    final_score: int
    is_perfect_round: bool
    
    @property
    def score_delta(self) -> int:
        """The change in score for this round."""
        return self.final_score


class ScoringService:
    """
    Domain service for calculating scores.
    Encapsulates all scoring rules and logic.
    """
    
    # Scoring constants
    ZERO_SUCCESS_BONUS = 3
    PERFECT_PREDICTION_BONUS = 5
    
    @classmethod
    def calculate_base_score(cls, declared: int, actual: int) -> int:
        """
        Calculate base score based on declared vs actual piles captured.
        
        Scoring rules:
        - If declared = 0 and actual = 0 → +3 bonus points
        - If declared = 0 but actual > 0 → penalty = -actual
        - If declared == actual (non-zero) → score = declared + 5 bonus
        - Otherwise → penalty = -abs(declared - actual)
        
        Args:
            declared: Number of piles player declared
            actual: Number of piles player actually captured
            
        Returns:
            Base score before multipliers
        """
        if declared == 0:
            if actual == 0:
                return cls.ZERO_SUCCESS_BONUS  # Successfully kept zero
            else:
                return -actual  # Failed to keep zero
        else:
            if actual == declared:
                return declared + cls.PERFECT_PREDICTION_BONUS  # Perfect prediction
            else:
                return -abs(declared - actual)  # Missed target
    
    @classmethod
    def calculate_round_scores(
        cls,
        player_declarations: Dict[str, int],
        pile_counts: Dict[str, int],
        redeal_multiplier: int = 1
    ) -> List[RoundScore]:
        """
        Calculate scores for all players at the end of a round.
        
        Args:
            player_declarations: Map of player name to declared piles
            pile_counts: Map of player name to actual piles captured
            redeal_multiplier: Score multiplier due to redeals
            
        Returns:
            List of RoundScore objects for each player
        """
        if redeal_multiplier < 1:
            raise ValueError("Redeal multiplier must be at least 1")
        
        scores = []
        
        for player_name, declared in player_declarations.items():
            actual = pile_counts.get(player_name, 0)
            base_score = cls.calculate_base_score(declared, actual)
            final_score = base_score * redeal_multiplier
            
            # Check for perfect round (non-zero declaration met exactly)
            is_perfect = declared > 0 and declared == actual
            
            scores.append(RoundScore(
                player_name=player_name,
                declared=declared,
                actual=actual,
                base_score=base_score,
                multiplier=redeal_multiplier,
                final_score=final_score,
                is_perfect_round=is_perfect
            ))
        
        return scores
    
    @classmethod
    def is_perfect_round(cls, declared: int, actual: int) -> bool:
        """
        Check if a player had a perfect round.
        
        A perfect round is when a player declares a non-zero value
        and captures exactly that many piles.
        
        Args:
            declared: Number of piles declared
            actual: Number of piles captured
            
        Returns:
            True if this was a perfect round
        """
        return declared > 0 and declared == actual
    
    @classmethod
    def calculate_score_penalty(cls, declared: int, actual: int) -> int:
        """
        Calculate just the penalty portion of scoring.
        Used for displaying potential penalties during gameplay.
        
        Args:
            declared: Number of piles declared
            actual: Number of piles that would be captured
            
        Returns:
            Penalty amount (always non-positive)
        """
        base_score = cls.calculate_base_score(declared, actual)
        return min(0, base_score)  # Return only penalties
    
    @classmethod
    def calculate_potential_score(
        cls,
        declared: int,
        current_piles: int,
        remaining_turns: int,
        redeal_multiplier: int = 1
    ) -> Dict[str, int]:
        """
        Calculate potential scores for strategic planning.
        
        Args:
            declared: Number of piles declared
            current_piles: Current pile count
            remaining_turns: Turns left in round
            redeal_multiplier: Current multiplier
            
        Returns:
            Dict with 'best_case', 'worst_case', and 'current' scores
        """
        # Current trajectory
        current_score = cls.calculate_base_score(declared, current_piles) * redeal_multiplier
        
        # Best case: capture exactly declared
        best_score = cls.calculate_base_score(declared, declared) * redeal_multiplier
        
        # Worst case: maximum deviation
        max_possible = current_piles + remaining_turns
        worst_score = cls.calculate_base_score(declared, max_possible) * redeal_multiplier
        
        return {
            'current': current_score,
            'best_case': best_score,
            'worst_case': worst_score
        }