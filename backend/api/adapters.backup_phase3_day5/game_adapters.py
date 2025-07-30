"""
Game action WebSocket adapters using minimal intervention pattern.
Handles all game-related actions with clean architecture boundaries.
"""

from typing import Dict, Any, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

# Actions that need game adapter handling
GAME_ADAPTER_ACTIONS = {
    "start_game",
    "declare",
    "play",
    "play_pieces",  # play_pieces is legacy alias
    "request_redeal",
    "accept_redeal",
    "decline_redeal",
    "redeal_decision",
    "player_ready",
    "leave_game",
}


async def handle_game_messages(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Minimal intervention handler for game-related messages.
    Only intercepts messages that need clean architecture adaptation.
    """
    action = message.get("action")

    # Fast path - pass through non-game messages
    if action not in GAME_ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)

    # Handle game actions with minimal overhead
    if action == "start_game":
        return await _handle_start_game(websocket, message, room_state, broadcast_func)
    elif action == "declare":
        return await _handle_declare(websocket, message, room_state, broadcast_func)
    elif action in ["play", "play_pieces"]:  # Handle both variants
        return await _handle_play(websocket, message, room_state, broadcast_func)
    elif action == "request_redeal":
        return await _handle_request_redeal(
            websocket, message, room_state, broadcast_func
        )
    elif action == "accept_redeal":
        return await _handle_accept_redeal(
            websocket, message, room_state, broadcast_func
        )
    elif action == "decline_redeal":
        return await _handle_decline_redeal(
            websocket, message, room_state, broadcast_func
        )
    elif action == "redeal_decision":
        return await _handle_redeal_decision(
            websocket, message, room_state, broadcast_func
        )
    elif action == "player_ready":
        return await _handle_player_ready(
            websocket, message, room_state, broadcast_func
        )
    elif action == "leave_game":
        return await _handle_leave_game(websocket, message, room_state, broadcast_func)

    # Fallback (shouldn't reach here)
    return await legacy_handler(websocket, message)


async def _handle_start_game(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle start_game request from room host.
    Validates conditions and initiates game.
    """
    data = message.get("data", {})
    requester = data.get("player_name")

    if not requester:
        return {
            "event": "error",
            "data": {
                "message": "Player name required to start game",
                "type": "validation_error",
            },
        }

    # In full implementation would:
    # 1. Verify requester is host
    # 2. Check all players ready
    # 3. Initialize game state
    # 4. Deal cards
    # 5. Broadcast game started

    return {
        "event": "game_started",
        "data": {
            "success": True,
            "initial_phase": "PREPARATION",
            "round_number": 1,
            "starter_player": requester,
        },
    }


async def _handle_declare(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle pile count declaration during DECLARATION phase.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    pile_count = data.get("pile_count")

    if not player_name or pile_count is None:
        return {
            "event": "error",
            "data": {
                "message": "Player name and pile count required",
                "type": "validation_error",
            },
        }

    # Validate pile count
    if not isinstance(pile_count, int) or pile_count < 0 or pile_count > 8:
        return {
            "event": "error",
            "data": {
                "message": "Pile count must be between 0 and 8",
                "type": "validation_error",
            },
        }

    return {
        "event": "declaration_made",
        "data": {"player_name": player_name, "pile_count": pile_count, "success": True},
    }


async def _handle_play(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle play action during TURN phase.
    Supports both 'play' and 'play_pieces' actions.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    pieces = data.get("pieces", [])

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    if not pieces or not isinstance(pieces, list):
        return {
            "event": "error",
            "data": {"message": "Pieces list required", "type": "validation_error"},
        }

    # Basic validation
    if len(pieces) < 1 or len(pieces) > 6:
        return {
            "event": "error",
            "data": {
                "message": "Must play between 1 and 6 pieces",
                "type": "validation_error",
            },
        }

    # In full implementation would validate:
    # 1. It's player's turn
    # 2. Player has these pieces
    # 3. Pieces follow game rules
    # 4. Update game state

    return {
        "event": "play_made",
        "data": {
            "player_name": player_name,
            "pieces_played": pieces,
            "pieces_count": len(pieces),
            "success": True,
            "next_player": "NextPlayer",  # Would be determined by game logic
            "winner": None,  # Or player name if they won this turn
        },
    }


async def _handle_request_redeal(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle weak hand redeal request during PREPARATION phase.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    # In full implementation would:
    # 1. Verify in PREPARATION phase
    # 2. Check player has weak hand (no piece > 9)
    # 3. Broadcast redeal request to others

    return {
        "event": "redeal_requested",
        "data": {
            "requesting_player": player_name,
            "reason": "weak_hand",
            "waiting_for_players": ["Player2", "Player3", "Player4"],
        },
    }


async def _handle_accept_redeal(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle acceptance of redeal request.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    return {
        "event": "redeal_vote_cast",
        "data": {
            "player_name": player_name,
            "vote": "accept",
            "votes_remaining": 2,  # Would track actual votes
        },
    }


async def _handle_decline_redeal(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle declining of redeal request.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    return {
        "event": "redeal_declined",
        "data": {
            "declining_player": player_name,
            "redeal_cancelled": True,
            "next_phase": "DECLARATION",
        },
    }


async def _handle_redeal_decision(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle combined redeal decision (accept/decline in one message).
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    decision = data.get("decision")

    if not player_name or decision not in ["accept", "decline"]:
        return {
            "event": "error",
            "data": {
                "message": "Player name and valid decision required",
                "type": "validation_error",
            },
        }

    if decision == "accept":
        return await _handle_accept_redeal(
            websocket, message, room_state, broadcast_func
        )
    else:
        return await _handle_decline_redeal(
            websocket, message, room_state, broadcast_func
        )


async def _handle_player_ready(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle player ready status toggle.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    ready_status = data.get("ready", True)

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    return {
        "event": "player_ready_status",
        "data": {
            "player_name": player_name,
            "ready": ready_status,
            "all_ready": False,  # Would check if all players ready
        },
    }


async def _handle_leave_game(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle player leaving during active game.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")

    if not player_name:
        return {
            "event": "error",
            "data": {"message": "Player name required", "type": "validation_error"},
        }

    return {
        "event": "player_left_game",
        "data": {
            "player_name": player_name,
            "game_continues": True,  # Or False if not enough players
            "replacement": "Bot_MED",  # If replaced with bot
        },
    }


class GameAdapterIntegration:
    """
    Integration point for game adapters.
    Maintains compatibility with existing system while enabling clean architecture.
    """

    def __init__(self, legacy_handler: Callable):
        self.legacy_handler = legacy_handler
        self._enabled = True

    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """Main entry point for game message handling"""
        if not self._enabled:
            return await self.legacy_handler(websocket, message)

        return await handle_game_messages(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )

    def enable(self):
        """Enable game adapters"""
        self._enabled = True
        logger.info("Game adapters enabled")

    def disable(self):
        """Disable game adapters (fallback to legacy)"""
        self._enabled = False
        logger.info("Game adapters disabled - using legacy handlers")
