# WebSocket Message Contracts Definition
"""
Defines the exact contracts for all WebSocket messages between frontend and backend.
These contracts serve as the source of truth for compatibility testing.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class MessageDirection(Enum):
    """Direction of WebSocket messages"""

    CLIENT_TO_SERVER = "client_to_server"
    SERVER_TO_CLIENT = "server_to_client"
    SERVER_BROADCAST = "server_broadcast"


@dataclass
class WebSocketContract:
    """Base contract for WebSocket messages"""

    name: str
    direction: MessageDirection
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    broadcast_schemas: Optional[List[Dict[str, Any]]] = None
    error_cases: Optional[List[Dict[str, Any]]] = None
    state_preconditions: Optional[Dict[str, Any]] = None
    state_postconditions: Optional[Dict[str, Any]] = None
    timing_requirements: Optional[Dict[str, Any]] = None


# Connection Management Contracts
PING_CONTRACT = WebSocketContract(
    name="ping",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Heartbeat to keep connection alive",
    request_schema={"action": "ping", "data": {"timestamp": "number (optional)"}},
    response_schema={
        "event": "pong",
        "data": {
            "timestamp": "number (echo from request)",
            "server_time": "number (server timestamp)",
            "room_id": "string (if in room)",
        },
    },
    timing_requirements={"max_response_time_ms": 100},
)

CLIENT_READY_CONTRACT = WebSocketContract(
    name="client_ready",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Signal client is ready to receive events",
    request_schema={
        "action": "client_ready",
        "data": {"player_name": "string (optional)"},
    },
    response_schema={
        "event": "room_state_update",
        "data": {"slots": "array of player objects", "host_name": "string"},
    },
    broadcast_schemas=[
        {
            "event": "room_list_update",
            "data": {
                "rooms": "array of room summaries",
                "timestamp": "number",
                "initial": True,
            },
        }
    ],
)

# Room Management Contracts
CREATE_ROOM_CONTRACT = WebSocketContract(
    name="create_room",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Create a new game room",
    request_schema={
        "action": "create_room",
        "data": {"player_name": "string (1-20 alphanumeric + spaces)"},
    },
    response_schema={
        "event": "room_created",
        "data": {
            "room_id": "string (6 uppercase alphanumeric)",
            "host_name": "string (echo of player_name)",
            "success": True,
        },
    },
    broadcast_schemas=[
        {
            "event": "room_list_update",
            "data": {
                "rooms": "array of room summaries",
                "timestamp": "number",
                "reason": "new_room_created",
            },
        }
    ],
    error_cases=[
        {
            "condition": "Invalid player name",
            "response": {
                "event": "error",
                "data": {
                    "message": "Failed to create room: Invalid player name",
                    "type": "room_creation_error",
                },
            },
        }
    ],
    state_preconditions={"player_not_in_room": True, "connection_to_lobby": True},
    state_postconditions={
        "room_created": True,
        "player_is_host": True,
        "player_in_slot": "P1",
    },
)

JOIN_ROOM_CONTRACT = WebSocketContract(
    name="join_room",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Join an existing room",
    request_schema={
        "action": "join_room",
        "data": {"room_id": "string (6 chars)", "player_name": "string (1-20 chars)"},
    },
    response_schema={
        "event": "room_joined",
        "data": {
            "room_id": "string",
            "player_name": "string",
            "assigned_slot": "number (0-3)",
            "success": True,
        },
    },
    broadcast_schemas=[
        {
            "event": "room_update",
            "data": {
                "players": "array of player objects",
                "host_name": "string",
                "room_id": "string",
                "started": "boolean",
            },
        }
    ],
    error_cases=[
        {
            "condition": "Room not found",
            "response": {
                "event": "error",
                "data": {"message": "Room not found", "type": "join_room_error"},
            },
        },
        {
            "condition": "Room is full",
            "response": {
                "event": "error",
                "data": {"message": "Room is full", "type": "join_room_error"},
            },
        },
        {
            "condition": "Game already started",
            "response": {
                "event": "error",
                "data": {
                    "message": "Room has already started",
                    "type": "join_room_error",
                },
            },
        },
    ],
)

START_GAME_CONTRACT = WebSocketContract(
    name="start_game",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Start the game (host only)",
    request_schema={"action": "start_game", "data": {}},
    broadcast_schemas=[
        {"event": "game_started", "data": {"room_id": "string", "success": True}},
        {
            "event": "phase_change",
            "data": {
                "phase": "PREPARATION",
                "allowed_actions": "array of action strings",
                "phase_data": "object with phase-specific data",
                "players": "object with player hands",
                "round": 1,
            },
        },
    ],
    error_cases=[
        {
            "condition": "Not enough players",
            "response": {
                "event": "error",
                "data": {"message": "Failed to start game", "type": "start_game_error"},
            },
        }
    ],
    state_preconditions={
        "is_host": True,
        "room_has_4_players": True,
        "game_not_started": True,
    },
    state_postconditions={
        "game_started": True,
        "phase": "PREPARATION",
        "cards_dealt": True,
    },
)

# Game Action Contracts
DECLARE_CONTRACT = WebSocketContract(
    name="declare",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Make pile count declaration",
    request_schema={
        "action": "declare",
        "data": {"player_name": "string", "value": "number (0-8)"},
    },
    broadcast_schemas=[
        {
            "event": "declare",
            "data": {
                "player": "string",
                "value": "number",
                "players_declared": "number",
                "total_players": 4,
            },
        }
    ],
    error_cases=[
        {
            "condition": "Wrong phase",
            "response": {
                "event": "error",
                "data": {
                    "message": "Cannot declare in current phase",
                    "type": "invalid_action",
                },
            },
        },
        {
            "condition": "Already declared",
            "response": {
                "event": "error",
                "data": {
                    "message": "You have already declared",
                    "type": "invalid_action",
                },
            },
        },
    ],
    state_preconditions={"phase": "DECLARATION", "player_has_not_declared": True},
    timing_requirements={"max_response_time_ms": 200},
)

PLAY_CONTRACT = WebSocketContract(
    name="play",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Play pieces during turn",
    request_schema={
        "action": "play",
        "data": {
            "player_name": "string",
            "indices": "array of numbers (piece indices)",
        },
    },
    broadcast_schemas=[
        {
            "event": "turn_played",
            "data": {
                "player": "string",
                "pieces": "array of piece strings",
                "pieces_remaining": "number",
            },
        }
    ],
    response_schema={
        "event": "play_rejected",
        "data": {
            "message": "string (error message)",
            "details": "string (additional details)",
        },
    },
    error_cases=[
        {
            "condition": "Not your turn",
            "response": {
                "event": "play_rejected",
                "data": {
                    "message": "Not your turn",
                    "details": "It's currently Player X's turn",
                },
            },
        },
        {
            "condition": "Invalid piece count",
            "response": {
                "event": "play_rejected",
                "data": {
                    "message": "Invalid piece count",
                    "details": "Expected X pieces, got Y",
                },
            },
        },
    ],
    state_preconditions={
        "phase": "TURN",
        "is_current_player": True,
        "has_pieces_in_hand": True,
    },
    state_postconditions={
        "pieces_removed_from_hand": True,
        "turn_history_updated": True,
    },
)

# Phase Change Event Contract (Server to Client)
PHASE_CHANGE_CONTRACT = WebSocketContract(
    name="phase_change",
    direction=MessageDirection.SERVER_TO_CLIENT,
    description="Game phase changed notification",
    response_schema={
        "event": "phase_change",
        "data": {
            "phase": "string (PREPARATION|DECLARATION|TURN|SCORING)",
            "allowed_actions": "array of action strings",
            "phase_data": {
                "current_player": "string (for TURN phase)",
                "required_piece_count": "number (for TURN phase)",
                "weak_hands": "array (for PREPARATION phase)",
                "scores": "object (for SCORING phase)",
            },
            "players": "object with player data",
            "round": "number",
        },
    },
)

# Additional Contract Definitions

ACK_CONTRACT = WebSocketContract(
    name="ack",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Message acknowledgment for reliability",
    request_schema={
        "action": "ack",
        "data": {"sequence": "number", "client_id": "string (optional)"},
    },
)

SYNC_REQUEST_CONTRACT = WebSocketContract(
    name="sync_request",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Request synchronization after disconnect",
    request_schema={
        "action": "sync_request",
        "data": {"client_id": "string (optional)"},
    },
)

REQUEST_ROOM_LIST_CONTRACT = WebSocketContract(
    name="request_room_list",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Request list of available rooms",
    request_schema={
        "action": "request_room_list",
        "data": {"player_name": "string (optional)"},
    },
    response_schema={
        "event": "room_list_update",
        "data": {
            "rooms": "array of room objects",
            "timestamp": "number",
            "requested_by": "string",
        },
    },
)

GET_ROOMS_CONTRACT = WebSocketContract(
    name="get_rooms",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Get available rooms (alternative to request_room_list)",
    request_schema={"action": "get_rooms", "data": {}},
    response_schema={
        "event": "room_list",
        "data": {"rooms": "array of room objects", "timestamp": "number"},
    },
)

GET_ROOM_STATE_CONTRACT = WebSocketContract(
    name="get_room_state",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Request current room state",
    request_schema={"action": "get_room_state", "data": {}},
    response_schema={
        "event": "room_update",
        "data": {
            "players": "array of player objects",
            "host_name": "string",
            "room_id": "string",
            "started": "boolean",
        },
    },
    error_cases=[
        {
            "condition": "Room not found",
            "response": {
                "event": "room_closed",
                "data": {"message": "Room not found."},
            },
        }
    ],
)

ADD_BOT_CONTRACT = WebSocketContract(
    name="add_bot",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Add bot to empty slot (host only)",
    request_schema={"action": "add_bot", "data": {"slot_id": "string (1-4)"}},
    broadcast_schemas=[
        {
            "event": "room_update",
            "data": {
                "players": "array with bot added",
                "host_name": "string",
                "room_id": "string",
                "started": False,
            },
        }
    ],
    error_cases=[
        {
            "condition": "Not host",
            "response": {
                "event": "error",
                "data": {
                    "message": "Only the host can add bots",
                    "type": "permission_denied",
                },
            },
        }
    ],
    state_preconditions={"is_host": True, "slot_empty": True},
)

REMOVE_PLAYER_CONTRACT = WebSocketContract(
    name="remove_player",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Remove player from slot (host only)",
    request_schema={"action": "remove_player", "data": {"slot_id": "string (1-4)"}},
    broadcast_schemas=[
        {
            "event": "room_update",
            "data": {
                "players": "array with player removed",
                "host_name": "string",
                "room_id": "string",
                "started": False,
            },
        }
    ],
    error_cases=[
        {
            "condition": "Not host",
            "response": {
                "event": "error",
                "data": {
                    "message": "Only the host can remove players",
                    "type": "permission_denied",
                },
            },
        }
    ],
)

LEAVE_ROOM_CONTRACT = WebSocketContract(
    name="leave_room",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Leave current room",
    request_schema={"action": "leave_room", "data": {"player_name": "string"}},
    response_schema={
        "event": "player_left",
        "data": {"player_name": "string", "success": True, "room_closed": "boolean"},
    },
    broadcast_schemas=[
        {
            "event": "room_update",
            "data": {
                "players": "array",
                "host_name": "string",
                "room_id": "string",
                "started": "boolean",
            },
        }
    ],
)

LEAVE_GAME_CONTRACT = WebSocketContract(
    name="leave_game",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Leave active game",
    request_schema={"action": "leave_game", "data": {"player_name": "string"}},
    response_schema={"event": "leave_game_success", "data": {"player_name": "string"}},
)

REQUEST_REDEAL_CONTRACT = WebSocketContract(
    name="request_redeal",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Request redeal (weak hand)",
    request_schema={"action": "request_redeal", "data": {"player_name": "string"}},
    response_schema={"event": "redeal_success", "data": {"player_name": "string"}},
    state_preconditions={"phase": "PREPARATION", "has_weak_hand": True},
)

ACCEPT_REDEAL_CONTRACT = WebSocketContract(
    name="accept_redeal",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Accept redeal offer",
    request_schema={"action": "accept_redeal", "data": {"player_name": "string"}},
    response_schema={
        "event": "redeal_response_success",
        "data": {"player_name": "string", "choice": "accept"},
    },
)

DECLINE_REDEAL_CONTRACT = WebSocketContract(
    name="decline_redeal",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Decline redeal offer",
    request_schema={"action": "decline_redeal", "data": {"player_name": "string"}},
    response_schema={
        "event": "redeal_response_success",
        "data": {"player_name": "string", "choice": "decline"},
    },
)

PLAY_PIECES_CONTRACT = WebSocketContract(
    name="play_pieces",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Play pieces (legacy handler)",
    request_schema={
        "action": "play_pieces",
        "data": {"player_name": "string", "indices": "array of numbers"},
    },
    response_schema={
        "event": "play_success",
        "data": {"player_name": "string", "indices": "array"},
    },
)

PLAYER_READY_CONTRACT = WebSocketContract(
    name="player_ready",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Signal ready for next phase",
    request_schema={"action": "player_ready", "data": {"player_name": "string"}},
    response_schema={"event": "ready_success", "data": {"player_name": "string"}},
)

REDEAL_DECISION_CONTRACT = WebSocketContract(
    name="redeal_decision",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Response to redeal offer",
    request_schema={
        "action": "redeal_decision",
        "data": {"player_name": "string", "choice": "string (accept|decline)"},
    },
)

# Contract Registry
WEBSOCKET_CONTRACTS = {
    # Connection Management
    "ping": PING_CONTRACT,
    "client_ready": CLIENT_READY_CONTRACT,
    "ack": ACK_CONTRACT,
    "sync_request": SYNC_REQUEST_CONTRACT,
    # Lobby Operations
    "request_room_list": REQUEST_ROOM_LIST_CONTRACT,
    "get_rooms": GET_ROOMS_CONTRACT,
    "create_room": CREATE_ROOM_CONTRACT,
    "join_room": JOIN_ROOM_CONTRACT,
    # Room Management
    "get_room_state": GET_ROOM_STATE_CONTRACT,
    "add_bot": ADD_BOT_CONTRACT,
    "remove_player": REMOVE_PLAYER_CONTRACT,
    "leave_room": LEAVE_ROOM_CONTRACT,
    "leave_game": LEAVE_GAME_CONTRACT,
    "start_game": START_GAME_CONTRACT,
    # Game Actions
    "redeal_decision": REDEAL_DECISION_CONTRACT,
    "request_redeal": REQUEST_REDEAL_CONTRACT,
    "accept_redeal": ACCEPT_REDEAL_CONTRACT,
    "decline_redeal": DECLINE_REDEAL_CONTRACT,
    "declare": DECLARE_CONTRACT,
    "play": PLAY_CONTRACT,
    "play_pieces": PLAY_PIECES_CONTRACT,
    "player_ready": PLAYER_READY_CONTRACT,
    # Server Events
    "phase_change": PHASE_CHANGE_CONTRACT,
}


def get_contract(message_name: str) -> Optional[WebSocketContract]:
    """Get contract for a specific message"""
    return WEBSOCKET_CONTRACTS.get(message_name)


def get_all_contracts() -> Dict[str, WebSocketContract]:
    """Get all defined contracts"""
    return WEBSOCKET_CONTRACTS.copy()


def validate_message_against_contract(
    message: Dict[str, Any], contract: WebSocketContract
) -> tuple[bool, Optional[str]]:
    """
    Validate a message against its contract

    Returns:
        (is_valid, error_message)
    """
    # Basic implementation - to be expanded
    if contract.direction == MessageDirection.CLIENT_TO_SERVER:
        if not contract.request_schema:
            return True, None

        # Check action field
        if message.get("action") != contract.name:
            return (
                False,
                f"Expected action '{contract.name}', got '{message.get('action')}'",
            )

    elif contract.direction == MessageDirection.SERVER_TO_CLIENT:
        if not contract.response_schema:
            return True, None

        # Check event field
        expected_event = contract.response_schema.get("event")
        if message.get("event") != expected_event:
            return (
                False,
                f"Expected event '{expected_event}', got '{message.get('event')}'",
            )

    return True, None
