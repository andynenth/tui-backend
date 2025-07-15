"""
Pydantic models for game entities and API responses.

These models provide OpenAPI documentation and request/response validation
for the Liap Tui game API endpoints.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class GamePhase(str, Enum):
    """Game phases in the Liap Tui game flow."""
    LOBBY = "lobby"
    PREPARATION = "preparation"
    DECLARATION = "declaration"
    TURN = "turn"
    TURN_RESULTS = "turn_results"
    SCORING = "scoring"
    GAME_OVER = "game_over"


class PieceColor(str, Enum):
    """Piece colors in the game."""
    RED = "red"
    BLACK = "black"


class PieceSuit(str, Enum):
    """Piece suits in the game."""
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class Piece(BaseModel):
    """A single game piece (card)."""
    value: int = Field(..., ge=1, le=14, description="Piece value (1-14, where 1=Ace, 11=Jack, 12=Queen, 13=King, 14=Red General)")
    color: PieceColor = Field(..., description="Piece color")
    suit: PieceSuit = Field(..., description="Piece suit")
    
    class Config:
        schema_extra = {
            "example": {
                "value": 12,
                "color": "red",
                "suit": "hearts"
            }
        }


class Player(BaseModel):
    """A player in the game."""
    name: str = Field(..., min_length=1, max_length=50, description="Player name")
    id: str = Field(..., description="Unique player identifier")
    is_bot: bool = Field(False, description="Whether this player is a bot")
    slot_id: Optional[int] = Field(None, ge=1, le=4, description="Player's slot position (1-4)")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Alice",
                "id": "player_123",
                "is_bot": False,
                "slot_id": 1
            }
        }


class RoomStatus(str, Enum):
    """Room status values."""
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Room(BaseModel):
    """A game room."""
    id: str = Field(..., description="Unique room identifier")
    name: Optional[str] = Field(None, description="Room display name")
    status: RoomStatus = Field(..., description="Current room status")
    players: List[Player] = Field([], description="Players in the room")
    max_players: int = Field(4, description="Maximum number of players")
    created_at: str = Field(..., description="Room creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "room_abc123",
                "name": "Alice's Game",
                "status": "waiting",
                "players": [
                    {
                        "name": "Alice",
                        "id": "player_123",
                        "is_bot": False,
                        "slot_id": 1
                    }
                ],
                "max_players": 4,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class GameState(BaseModel):
    """Complete game state information."""
    room: Room = Field(..., description="Room information")
    phase: GamePhase = Field(..., description="Current game phase")
    round_number: int = Field(0, ge=0, description="Current round number")
    turn_number: int = Field(0, ge=0, description="Current turn number within round")
    current_player: Optional[str] = Field(None, description="Current player's name")
    current_declarer: Optional[str] = Field(None, description="Current declarer's name")
    declarations: Dict[str, int] = Field({}, description="Player declarations (player_name -> pile_count)")
    scores: Dict[str, int] = Field({}, description="Player scores (player_name -> total_score)")
    winner: Optional[str] = Field(None, description="Game winner (if game is finished)")
    
    class Config:
        schema_extra = {
            "example": {
                "room": {
                    "id": "room_abc123",
                    "name": "Alice's Game",
                    "status": "in_progress",
                    "players": [],
                    "max_players": 4,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "phase": "declaration",
                "round_number": 1,
                "turn_number": 0,
                "current_player": None,
                "current_declarer": "Alice",
                "declarations": {"Alice": 2},
                "scores": {"Alice": 0, "Bob": 0},
                "winner": None
            }
        }


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """Basic health check response."""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0"
            }
        }


class DetailedHealthCheck(BaseModel):
    """Detailed health check response."""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    components: Dict[str, HealthStatus] = Field(..., description="Component health status")
    memory_usage_mb: float = Field(..., description="Memory usage in megabytes")
    active_rooms: int = Field(..., description="Number of active game rooms")
    active_connections: int = Field(..., description="Number of active WebSocket connections")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0",
                "uptime_seconds": 3600.5,
                "components": {
                    "database": "healthy",
                    "websocket": "healthy",
                    "game_engine": "healthy"
                },
                "memory_usage_mb": 256.7,
                "active_rooms": 5,
                "active_connections": 12
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    code: Optional[int] = Field(None, description="Error code")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid player name",
                "details": "Player name must be between 1 and 50 characters",
                "code": 1001,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response format."""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None
            }
        }