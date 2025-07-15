"""
Pydantic request models for API endpoints.

These models define the structure and validation for request bodies
sent to the Liap Tui game API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    """Request to create a new game room."""
    player_name: str = Field(..., min_length=1, max_length=50, description="Name of the player creating the room")
    room_name: Optional[str] = Field(None, max_length=100, description="Optional display name for the room")
    
    class Config:
        schema_extra = {
            "example": {
                "player_name": "Alice",
                "room_name": "Alice's Game"
            }
        }


class JoinRoomRequest(BaseModel):
    """Request to join an existing game room."""
    room_id: str = Field(..., min_length=1, max_length=50, description="ID of the room to join")
    player_name: str = Field(..., min_length=1, max_length=50, description="Name of the player joining")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "player_name": "Bob"
            }
        }


class AssignSlotRequest(BaseModel):
    """Request to assign a player or bot to a slot."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    slot_id: int = Field(..., ge=1, le=4, description="Slot position (1-4)")
    player_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Player name (for human players)")
    is_bot: bool = Field(False, description="Whether to assign a bot to this slot")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "slot_id": 2,
                "player_name": "Charlie",
                "is_bot": False
            }
        }


class StartGameRequest(BaseModel):
    """Request to start a game in a room."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123"
            }
        }


class ExitRoomRequest(BaseModel):
    """Request to exit/delete a room."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123"
            }
        }


class DeclareRequest(BaseModel):
    """Request to make a pile count declaration."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    player_name: str = Field(..., min_length=1, max_length=50, description="Player making the declaration")
    value: int = Field(..., ge=0, le=8, description="Declared pile count (0-8)")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "player_name": "Alice",
                "value": 2
            }
        }


class PlayTurnRequest(BaseModel):
    """Request to play pieces during a turn."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    player_name: str = Field(..., min_length=1, max_length=50, description="Player playing the turn")
    piece_indices: List[int] = Field(..., min_items=1, max_items=6, description="Indices of pieces to play (1-6 pieces)")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "player_name": "Alice",
                "piece_indices": [0, 1, 2]
            }
        }


class RedealRequest(BaseModel):
    """Request to initiate a redeal for weak hands."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    player_name: str = Field(..., min_length=1, max_length=50, description="Player requesting redeal")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "player_name": "Alice"
            }
        }


class RedealDecisionRequest(BaseModel):
    """Request to respond to a redeal offer."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    player_name: str = Field(..., min_length=1, max_length=50, description="Player making the decision")
    choice: str = Field(..., pattern="^(accept|decline)$", description="Redeal decision: 'accept' or 'decline'")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "player_name": "Bob",
                "choice": "accept"
            }
        }


class ScoreRoundRequest(BaseModel):
    """Request to score the current round."""
    room_id: str = Field(..., min_length=1, max_length=50, description="Room ID")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123"
            }
        }


class TriggerRecoveryRequest(BaseModel):
    """Request to trigger a recovery procedure."""
    room_id: Optional[str] = Field(None, description="Room ID (if recovery is room-specific)")
    force: bool = Field(False, description="Force recovery even if system appears healthy")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room_abc123",
                "force": False
            }
        }