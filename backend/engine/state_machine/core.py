# backend/engine/state_machine/core.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


class GamePhase(str, Enum):
    """Game phases in order"""
    PREPARATION = "preparation"        # Deal cards, check weak hands, redeals
    DECLARATION = "declaration"        # Players declare target piles
    TURN = "turn"                     # Players play pieces in turns
    TURN_RESULTS = "turn_results"     # Show turn winner & pieces won
    SCORING = "scoring"               # Calculate scores, check for winner
    SCORING_DISPLAY = "scoring_display"  # Show score breakdown to players
    GAME_END = "game_end"             # Show final results when game complete


class ActionType(str, Enum):
    """All possible game actions"""
    # Preparation phase actions
    REDEAL_REQUEST = "redeal_request"    # Accept redeal (weak player)
    REDEAL_RESPONSE = "redeal_response"  # Decline redeal (weak player)
    
    # Declaration phase actions
    DECLARE = "declare"                  # Declare target piles
    
    # Turn phase actions
    PLAY_PIECES = "play_pieces"         # Play 1-6 pieces
    
    # General actions (any phase)
    PLAYER_DISCONNECT = "player_disconnect"
    PLAYER_RECONNECT = "player_reconnect"
    TIMEOUT = "timeout"                 # Action timeout
    
    # Game end actions
    NAVIGATE_TO_LOBBY = "navigate_to_lobby"  # Back to lobby from game end
    
    # System actions
    PHASE_TRANSITION = "phase_transition"
    GAME_STATE_UPDATE = "game_state_update"
    
    VIEW_SCORES = "view_scores"           
    CONTINUE_ROUND = "continue_round"     


@dataclass
class GameAction:
    """Represents a game action from a player or system"""
    player_name: str
    action_type: ActionType
    payload: Dict[str, Any]
    timestamp: datetime = None
    sequence_id: int = 0
    is_bot: bool = False
    
    def __post_init__(self):
        # Ensure we have a timestamp
        if self.timestamp is None:
            self.timestamp = datetime.now()