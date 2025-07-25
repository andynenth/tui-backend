"""
DTOs for game flow use cases.

These DTOs define the request and response structures for
game operations like starting games, making plays, and declarations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base import Request, Response
from .common import GameStateInfo, PieceInfo, PlayInfo


# StartGame Use Case DTOs

@dataclass
class StartGameRequest(Request):
    """Request to start a new game."""
    
    room_id: str
    requesting_player_id: str
    shuffle_seats: bool = True
    use_previous_starter: bool = False


@dataclass
class StartGameResponse(Response):
    """Response from starting a game."""
    
    game_id: str
    room_id: str
    initial_state: GameStateInfo
    player_hands: Dict[str, List[PieceInfo]]
    starting_player_id: str
    weak_hands_detected: List[str] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        """Include game start data in response."""
        return {
            "game_id": self.game_id,
            "room_id": self.room_id,
            "initial_state": self.initial_state.__dict__,
            "player_hands": {
                player_id: [p.to_dict() for p in pieces]
                for player_id, pieces in self.player_hands.items()
            },
            "starting_player_id": self.starting_player_id,
            "weak_hands_detected": self.weak_hands_detected
        }


# Declare Use Case DTOs

@dataclass
class DeclareRequest(Request):
    """Request to declare pile count."""
    
    game_id: str
    player_id: str
    pile_count: int


@dataclass
class DeclareResponse(Response):
    """Response from making a declaration."""
    
    player_id: str
    declared_piles: int
    all_declared: bool
    next_player_id: Optional[str] = None
    total_declared: Optional[int] = None
    
    def _get_data(self) -> Dict[str, Any]:
        """Include declaration data in response."""
        data = {
            "player_id": self.player_id,
            "declared_piles": self.declared_piles,
            "all_declared": self.all_declared
        }
        
        if self.next_player_id:
            data["next_player_id"] = self.next_player_id
        
        if self.total_declared is not None:
            data["total_declared"] = self.total_declared
        
        return data


# Play Use Case DTOs

@dataclass
class PlayRequest(Request):
    """Request to play pieces."""
    
    game_id: str
    player_id: str
    pieces: List[PieceInfo]


@dataclass
class PlayResponse(Response):
    """Response from playing pieces."""
    
    play_info: PlayInfo
    turn_winner_id: Optional[str] = None
    turn_complete: bool = False
    next_player_id: Optional[str] = None
    round_complete: bool = False
    game_complete: bool = False
    scores: Optional[Dict[str, int]] = None
    
    def _get_data(self) -> Dict[str, Any]:
        """Include play result data in response."""
        data = {
            "play": self.play_info.__dict__,
            "turn_complete": self.turn_complete,
            "round_complete": self.round_complete,
            "game_complete": self.game_complete
        }
        
        if self.turn_winner_id:
            data["turn_winner_id"] = self.turn_winner_id
        
        if self.next_player_id:
            data["next_player_id"] = self.next_player_id
        
        if self.scores:
            data["scores"] = self.scores
        
        return data


# Redeal Request DTOs

@dataclass
class RequestRedealRequest(Request):
    """Request to initiate a redeal due to weak hand."""
    
    game_id: str
    player_id: str
    hand_strength_score: Optional[int] = None


@dataclass
class RequestRedealResponse(Response):
    """Response from requesting a redeal."""
    
    redeal_id: str
    requesting_player_id: str
    votes_required: int
    timeout_seconds: int = 30
    auto_accept_players: List[str] = field(default_factory=list)
    
    def _get_data(self) -> Dict[str, Any]:
        """Include redeal request data in response."""
        return {
            "redeal_id": self.redeal_id,
            "requesting_player_id": self.requesting_player_id,
            "votes_required": self.votes_required,
            "timeout_seconds": self.timeout_seconds,
            "auto_accept_players": self.auto_accept_players
        }


# Accept/Decline Redeal DTOs

@dataclass
class AcceptRedealRequest(Request):
    """Request to accept a redeal."""
    
    game_id: str
    player_id: str
    redeal_id: str


@dataclass
class AcceptRedealResponse(Response):
    """Response from accepting a redeal."""
    
    redeal_id: str
    player_id: str
    votes_collected: int
    votes_required: int
    redeal_approved: bool
    new_hands_dealt: bool = False
    
    def _get_data(self) -> Dict[str, Any]:
        """Include acceptance data in response."""
        return {
            "redeal_id": self.redeal_id,
            "player_id": self.player_id,
            "votes_collected": self.votes_collected,
            "votes_required": self.votes_required,
            "redeal_approved": self.redeal_approved,
            "new_hands_dealt": self.new_hands_dealt
        }


@dataclass
class DeclineRedealRequest(Request):
    """Request to decline a redeal."""
    
    game_id: str
    player_id: str
    redeal_id: str


@dataclass
class DeclineRedealResponse(Response):
    """Response from declining a redeal."""
    
    redeal_id: str
    player_id: str
    redeal_cancelled: bool
    declining_player_becomes_starter: bool = False
    new_starting_player_id: Optional[str] = None
    
    def _get_data(self) -> Dict[str, Any]:
        """Include decline data in response."""
        data = {
            "redeal_id": self.redeal_id,
            "player_id": self.player_id,
            "redeal_cancelled": self.redeal_cancelled,
            "declining_player_becomes_starter": self.declining_player_becomes_starter
        }
        
        if self.new_starting_player_id:
            data["new_starting_player_id"] = self.new_starting_player_id
        
        return data


# Other Game DTOs

@dataclass
class HandleRedealDecisionRequest(Request):
    """Request to handle redeal timeout or completion."""
    
    game_id: str
    redeal_id: str
    force_decision: bool = False


@dataclass
class HandleRedealDecisionResponse(Response):
    """Response from handling redeal decision."""
    
    redeal_id: str
    decision: str  # "approved", "declined", "timeout"
    new_hands_dealt: bool
    starting_player_id: str
    missing_votes: List[str] = field(default_factory=list)


@dataclass
class MarkPlayerReadyRequest(Request):
    """Request to mark player ready for next phase."""
    
    game_id: str
    player_id: str
    ready_for_phase: str


@dataclass
class MarkPlayerReadyResponse(Response):
    """Response from marking player ready."""
    
    player_id: str
    ready_count: int
    total_players: int
    all_ready: bool
    next_phase: Optional[str] = None


@dataclass
class LeaveGameRequest(Request):
    """Request to leave an active game."""
    
    game_id: str
    player_id: str
    reason: Optional[str] = None


@dataclass
class LeaveGameResponse(Response):
    """Response from leaving a game."""
    
    player_id: str
    converted_to_bot: bool
    game_continues: bool
    replacement_bot_id: Optional[str] = None