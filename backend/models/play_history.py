# backend/models/play_history.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class PlayerInfo(BaseModel):
    """Information about a player."""

    player_id: str
    player_name: str
    player_type: str = Field(..., description="'ai' or 'human'")
    ai_version: Optional[str] = Field(None, description="AI version if player is AI")


class StarterInfo(BaseModel):
    """Information about the round starter."""

    player_id: str
    player_name: str
    reason: str = Field(
        ..., description="Reason for being starter (e.g., 'highest_card')"
    )
    highest_card: Optional[str] = Field(None, description="Card that made them starter")


class InitialState(BaseModel):
    """Initial state of a round."""

    starter: StarterInfo
    player_order: List[str] = Field(..., description="Order of play for the round")


class PieceInfo(BaseModel):
    """Information about a piece."""

    kind: str
    point: int


class HandInfo(BaseModel):
    """Hand information with sorted pieces."""

    pieces: List[PieceInfo]


class DeclarationData(BaseModel):
    """Individual player's declaration."""

    player_id: str
    declared: int
    position: int = Field(..., description="Position in declaration order (0-3)")
    strategy_notes: Optional[str] = Field(None, description="AI strategy notes")


class DeclarationInfo(BaseModel):
    """Declaration phase information."""

    declarations: List[DeclarationData]
    total_declared: int
    pile_room_calculation: Dict[str, int] = Field(
        ..., description="Pile room per player"
    )


class AIDecisionAnalysis(BaseModel):
    """AI decision reasoning (only for AI players)."""

    declaration_reasoning: Optional[Dict[str, Any]] = None
    turn_play_reasoning: Optional[Dict[str, Any]] = None


class PlayData(BaseModel):
    """Individual player's play in a turn."""

    player_id: str
    player_name: str
    pieces_played: List[PieceInfo]
    play_type: str = Field(..., description="Type of play (SINGLE, PAIR, etc.)")
    hand_before: List[PieceInfo]
    hand_after: List[PieceInfo]
    captured_count: int
    declared_count: int
    ai_decision_analysis: Optional[AIDecisionAnalysis] = None


class TurnWinner(BaseModel):
    """Turn winner information."""

    player_id: str
    player_name: str
    winning_play: List[PieceInfo]
    pieces_captured: int


class GameStateAfterTurn(BaseModel):
    """Game state after a turn."""

    captured: int
    declared: int
    hand_size: int


class TurnInfo(BaseModel):
    """Complete information for a single turn."""

    turn_number: int
    plays: List[PlayData]
    winner: Optional[TurnWinner] = None
    next_starter: str
    game_state_after: Dict[str, GameStateAfterTurn]


class CaptureInfo(BaseModel):
    """Capture information for scoring."""

    captured: int
    declared: int
    difference: int


class ScoringInfo(BaseModel):
    """Scoring details for a player."""

    points: int
    multiplier: int
    reason: str


class RoundSummary(BaseModel):
    """Summary of a round."""

    total_turns: int
    final_captures: Dict[str, CaptureInfo]
    scoring: Dict[str, ScoringInfo]
    cumulative_scores: Dict[str, int]


class RoundHistory(BaseModel):
    """Complete history for a single round."""

    round_number: int
    initial_state: InitialState
    hands_dealt: Dict[str, List[PieceInfo]]
    declaration_phase: DeclarationInfo
    turn_history: List[TurnInfo]
    round_summary: RoundSummary


class PlayHistoryResponse(BaseModel):
    """Complete play history response."""

    room_id: str
    total_rounds: int
    players: Dict[str, PlayerInfo]
    rounds: List[RoundHistory]
