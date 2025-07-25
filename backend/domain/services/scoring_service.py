"""
ScoringService domain service - handles score calculations.

This is a pure domain service with no infrastructure dependencies.
Encapsulates all scoring rules and calculations.
"""

from typing import Dict, List
from dataclasses import dataclass

from domain.entities.player import Player


@dataclass(frozen=True)
class RoundScore:
    """Value object representing a player's score for a round."""
    player_name: str
    declared_piles: int
    actual_piles: int
    base_score: int
    multiplier: float
    final_score: int
    is_perfect_round: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "player_name": self.player_name,
            "declared_piles": self.declared_piles,
            "actual_piles": self.actual_piles,
            "base_score": self.base_score,
            "multiplier": self.multiplier,
            "final_score": self.final_score,
            "is_perfect_round": self.is_perfect_round
        }


@dataclass(frozen=True)
class RoundResult:
    """Value object representing the complete scoring result for a round."""
    round_number: int
    player_scores: List[RoundScore]
    redeal_multiplier: float
    winner_name: str  # Player with highest score this round
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "round_number": self.round_number,
            "player_scores": [score.to_dict() for score in self.player_scores],
            "redeal_multiplier": self.redeal_multiplier,
            "winner_name": self.winner_name
        }
    
    def get_score_deltas(self) -> Dict[str, int]:
        """Get score changes for each player."""
        return {score.player_name: score.final_score for score in self.player_scores}


class ScoringService:
    """
    Domain service for score calculations.
    
    Scoring rules:
    - If declared = 0 and actual = 0 → +3 bonus points
    - If declared = 0 but actual > 0 → penalty = -actual
    - If declared == actual (non-zero) → score = declared + 5 bonus
    - Otherwise → penalty = -abs(declared - actual)
    - If round was triggered by redeal → score × multiplier
    """
    
    # Score constants
    ZERO_DECLARATION_SUCCESS_BONUS = 3
    PERFECT_DECLARATION_BONUS = 5
    
    @staticmethod
    def calculate_base_score(declared: int, actual: int) -> int:
        """
        Calculate base score for a single player.
        
        Args:
            declared: Number of piles player declared they would capture
            actual: Number of piles player actually captured
            
        Returns:
            Base score before multipliers
        """
        if declared == 0:
            if actual == 0:
                # Successfully declared and achieved zero
                return ScoringService.ZERO_DECLARATION_SUCCESS_BONUS
            else:
                # Failed zero declaration - penalty equals actual piles taken
                return -actual
        else:
            if actual == declared:
                # Perfect non-zero prediction
                return declared + ScoringService.PERFECT_DECLARATION_BONUS
            else:
                # Missed target - penalty is difference
                return -abs(declared - actual)
    
    @staticmethod
    def calculate_round_scores(
        players: List[Player],
        piles_captured: Dict[str, int],
        redeal_multiplier: float,
        round_number: int
    ) -> RoundResult:
        """
        Calculate scores for all players at end of round.
        
        Args:
            players: List of players in the game
            piles_captured: Map of player name to piles captured
            redeal_multiplier: Score multiplier from redeals (1.0, 1.5, 2.0, etc.)
            round_number: Current round number
            
        Returns:
            RoundResult with all scoring information
        """
        player_scores = []
        highest_score = float('-inf')
        round_winner = None
        
        for player in players:
            declared = player.declared_piles
            actual = piles_captured.get(player.name, 0)
            
            # Calculate base score
            base_score = ScoringService.calculate_base_score(declared, actual)
            
            # Apply multiplier
            final_score = int(base_score * redeal_multiplier)
            
            # Check for perfect round
            is_perfect = declared > 0 and declared == actual
            
            # Create score record
            score = RoundScore(
                player_name=player.name,
                declared_piles=declared,
                actual_piles=actual,
                base_score=base_score,
                multiplier=redeal_multiplier,
                final_score=final_score,
                is_perfect_round=is_perfect
            )
            
            player_scores.append(score)
            
            # Track round winner (highest score this round)
            if final_score > highest_score:
                highest_score = final_score
                round_winner = player.name
        
        return RoundResult(
            round_number=round_number,
            player_scores=player_scores,
            redeal_multiplier=redeal_multiplier,
            winner_name=round_winner
        )
    
    @staticmethod
    def calculate_final_standings(players: List[Player]) -> List[Dict[str, any]]:
        """
        Calculate final game standings.
        
        Args:
            players: List of all players
            
        Returns:
            List of player standings sorted by score (highest first)
        """
        standings = []
        
        for player in players:
            standings.append({
                "name": player.name,
                "score": player.score,
                "perfect_rounds": player.stats.perfect_rounds,
                "turns_won": player.stats.turns_won,
                "is_bot": player.is_bot
            })
        
        # Sort by score (descending)
        standings.sort(key=lambda x: x["score"], reverse=True)
        
        # Add rank
        for i, standing in enumerate(standings):
            standing["rank"] = i + 1
        
        return standings
    
    @staticmethod
    def is_perfect_round(declared: int, actual: int) -> bool:
        """Check if a declaration was perfectly met."""
        return declared > 0 and declared == actual
    
    @staticmethod
    def get_penalty_reason(declared: int, actual: int) -> str:
        """
        Get human-readable reason for score penalty.
        
        Args:
            declared: Declared piles
            actual: Actual piles captured
            
        Returns:
            Description of why player received penalty
        """
        if declared == 0 and actual > 0:
            return f"Declared 0 but captured {actual} pile(s)"
        elif declared != actual:
            diff = abs(declared - actual)
            if actual > declared:
                return f"Captured {diff} more pile(s) than declared"
            else:
                return f"Captured {diff} fewer pile(s) than declared"
        else:
            return "No penalty"