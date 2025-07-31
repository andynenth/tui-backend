"""
Common DTOs used across multiple use cases.

These DTOs represent common data structures that are shared
between different parts of the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


@dataclass
class BaseRequest:
    """Base class for all use case requests."""

    pass


@dataclass
class BaseResponse:
    """Base class for all use case responses."""

    success: bool = True
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PlayerStatus(str, Enum):
    """Player connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AWAY = "away"


class RoomStatus(str, Enum):
    """Room status."""

    WAITING = "waiting"
    IN_GAME = "in_game"
    FINISHED = "finished"


@dataclass
class PlayerInfo:
    """Information about a player."""

    player_id: str
    player_name: str
    is_bot: bool
    is_host: bool
    status: PlayerStatus
    seat_position: Optional[int] = None
    score: int = 0
    games_played: int = 0
    games_won: int = 0

    @classmethod
    def from_domain(cls, player) -> "PlayerInfo":
        """Create from domain Player entity."""
        return cls(
            player_id=player.id,
            player_name=player.name,
            is_bot=player.is_bot,
            is_host=False,  # Will be set by room context
            status=(
                PlayerStatus.CONNECTED
                if player.is_connected
                else PlayerStatus.DISCONNECTED
            ),
            seat_position=None,  # Will be set by room context
            score=player.score,
            games_played=player.games_played,
            games_won=player.games_won,
        )


@dataclass
class RoomInfo:
    """Information about a room."""

    room_id: str
    room_code: str
    room_name: str
    host_id: str
    status: RoomStatus
    players: List[PlayerInfo]
    max_players: int
    created_at: datetime
    game_in_progress: bool
    current_game_id: Optional[str] = None

    @property
    def player_count(self) -> int:
        """Get current number of players."""
        return len(self.players)

    @property
    def is_full(self) -> bool:
        """Check if room is full."""
        return self.player_count >= self.max_players

    @property
    def is_joinable(self) -> bool:
        """Check if room can be joined."""
        return not self.is_full and self.status == RoomStatus.WAITING


@dataclass
class GameStateInfo:
    """Information about current game state."""

    game_id: str
    room_id: str
    round_number: int
    turn_number: int
    phase: str
    current_player_id: Optional[str]
    player_scores: Dict[str, int]
    pieces_remaining: Dict[str, int]
    last_play: Optional[Dict[str, Any]] = None

    @property
    def is_active(self) -> bool:
        """Check if game is currently active."""
        return self.phase not in ["ended", "abandoned"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "game_id": self.game_id,
            "room_id": self.room_id,
            "round_number": self.round_number,
            "turn_number": self.turn_number,
            "phase": self.phase,
            "current_player_id": self.current_player_id,
            "player_scores": self.player_scores,
            "pieces_remaining": self.pieces_remaining,
            "last_play": self.last_play,
        }


@dataclass
class PieceInfo:
    """Information about a game piece."""

    value: int
    kind: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"value": self.value, "kind": self.kind}


@dataclass
class PlayInfo:
    """Information about a play."""

    player_id: str
    pieces: List[PieceInfo]
    play_type: str
    is_valid: bool

    @property
    def piece_count(self) -> int:
        """Get number of pieces played."""
        return len(self.pieces)


@dataclass
class PlayerStats:
    """Player statistics DTO."""

    player_id: str
    total_games: int = 0
    games_won: int = 0
    total_score: int = 0
    highest_score: int = 0
    average_score: float = 0.0
    win_rate: float = 0.0
    last_played: Optional[datetime] = None
