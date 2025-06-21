# backend/engine/state_machine/core.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

class GamePhase(Enum):
    PREPARATION = "preparation"
    DECLARATION = "declaration" 
    TURN = "turn"
    SCORING = "scoring"

class ActionType(Enum):
    REDEAL_REQUEST = "redeal_request"
    REDEAL_RESPONSE = "redeal_response"
    DECLARE = "declare"
    PLAY_PIECES = "play_pieces"
    PLAYER_DISCONNECT = "player_disconnect"
    PLAYER_RECONNECT = "player_reconnect"
    TIMEOUT = "timeout"

@dataclass
class GameAction:
    player_name: str
    action_type: ActionType
    payload: Dict[str, Any]
    timestamp: datetime
    sequence_id: int
    is_bot: bool = False