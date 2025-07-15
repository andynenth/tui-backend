"""
Pydantic request models for API endpoints.

These models define the structure and validation for request bodies
sent to the Liap Tui game API endpoints.

NOTE: Room management models have been removed as part of the WebSocket-only
migration. Room operations now use WebSocket events exclusively.
See REST_TO_WEBSOCKET_MIGRATION.md for details.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# REMOVED: Room Management Models - Use WebSocket events instead
# ============================================================================
# The following models have been removed:
# - CreateRoomRequest: Use WebSocket event 'create_room'
# - JoinRoomRequest: Use WebSocket event 'join_room'
# - AssignSlotRequest: Use WebSocket events 'add_bot' or 'remove_player'
# - StartGameRequest: Use WebSocket event 'start_game'
# - ExitRoomRequest: Use WebSocket event 'leave_room'
# ============================================================================


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