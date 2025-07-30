"""
WebSocket Route Registry
Maps WebSocket events to their handlers
"""

from typing import Dict, Set

# Define all WebSocket event routes
WEBSOCKET_ROUTES: Dict[str, str] = {
    # Connection events
    "ping": "connection_adapters.ping",
    "client_ready": "connection_adapters.client_ready",
    "ack": "connection_adapters.ack",
    "sync_request": "connection_adapters.sync_request",
    # Room management events
    "create_room": "room_adapters.create_room",
    "join_room": "room_adapters.join_room",
    "leave_room": "room_adapters.leave_room",
    "get_room_state": "room_adapters.get_room_state",
    "add_bot": "room_adapters.add_bot",
    "remove_player": "room_adapters.remove_player",
    # Lobby events
    "request_room_list": "lobby_adapters.request_room_list",
    "get_rooms": "lobby_adapters.get_rooms",
    # Game events
    "start_game": "game_adapters.start_game",
    "declare": "game_adapters.declare",
    "play": "game_adapters.play",
    "play_pieces": "game_adapters.play_pieces",
    "request_redeal": "game_adapters.request_redeal",
    "accept_redeal": "game_adapters.accept_redeal",
    "decline_redeal": "game_adapters.decline_redeal",
    "redeal_decision": "game_adapters.redeal_decision",
    "player_ready": "game_adapters.player_ready",
    "leave_game": "game_adapters.leave_game",
}

# Event categories for easier classification
CONNECTION_EVENTS: Set[str] = {"ping", "client_ready", "ack", "sync_request"}

ROOM_EVENTS: Set[str] = {
    "create_room",
    "join_room",
    "leave_room",
    "get_room_state",
    "add_bot",
    "remove_player",
}

LOBBY_EVENTS: Set[str] = {"request_room_list", "get_rooms"}

GAME_EVENTS: Set[str] = {
    "start_game",
    "declare",
    "play",
    "play_pieces",
    "request_redeal",
    "accept_redeal",
    "decline_redeal",
    "redeal_decision",
    "player_ready",
    "leave_game",
}

# All supported events
ALL_EVENTS: Set[str] = CONNECTION_EVENTS | ROOM_EVENTS | LOBBY_EVENTS | GAME_EVENTS


def get_handler_for_event(event: str) -> str:
    """
    Get the handler path for a given event.

    Args:
        event: The event name

    Returns:
        Handler path or empty string if not found
    """
    return WEBSOCKET_ROUTES.get(event, "")


def is_supported_event(event: str) -> bool:
    """
    Check if an event is supported.

    Args:
        event: The event name

    Returns:
        True if supported, False otherwise
    """
    return event in ALL_EVENTS


def get_event_category(event: str) -> str:
    """
    Get the category of an event.

    Args:
        event: The event name

    Returns:
        Category name or "unknown"
    """
    if event in CONNECTION_EVENTS:
        return "connection"
    elif event in ROOM_EVENTS:
        return "room"
    elif event in LOBBY_EVENTS:
        return "lobby"
    elif event in GAME_EVENTS:
        return "game"
    else:
        return "unknown"
