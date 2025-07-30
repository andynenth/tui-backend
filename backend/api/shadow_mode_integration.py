"""
Shadow Mode Integration with WebSocket Handlers
Integrates shadow mode with existing WebSocket infrastructure.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
import logging

from api.shadow_mode import (
    configure_shadow_mode,
    handle_with_shadow,
    ShadowModeConfig,
    ShadowModeState,
)


logger = logging.getLogger(__name__)


class ShadowModeWebSocketAdapter:
    """Adapts existing WebSocket handlers for shadow mode"""

    def __init__(self, current_handler: Callable):
        self.current_handler = current_handler
        self.shadow_handler: Optional[Callable] = None
        self.enabled = False

    def set_shadow_handler(self, shadow_handler: Callable):
        """Set the shadow (refactored) handler"""
        self.shadow_handler = shadow_handler

    def enable_shadow_mode(
        self,
        config: Optional[ShadowModeConfig] = None,
        state: ShadowModeState = ShadowModeState.MONITORING,
    ):
        """Enable shadow mode with configuration"""
        if not self.shadow_handler:
            raise ValueError("Shadow handler must be set before enabling shadow mode")

        configure_shadow_mode(
            current_handler=self.current_handler,
            shadow_handler=self.shadow_handler,
            config=config,
        )

        self.enabled = True
        logger.info(f"Shadow mode enabled with state: {state.value}")

    def disable_shadow_mode(self):
        """Disable shadow mode"""
        if self.enabled:
            config = ShadowModeConfig()
            config.state = ShadowModeState.DISABLED
            configure_shadow_mode(self.current_handler, None, config)
            self.enabled = False
            logger.info("Shadow mode disabled")

    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ):
        """Handle message with optional shadow mode"""
        if self.enabled:
            return await handle_with_shadow(websocket, message, room_state)
        else:
            # Run current handler directly
            return await self.current_handler(websocket, message, room_state, None)


def create_shadow_mode_wrapper(current_ws_handler):
    """
    Create a shadow mode wrapper for existing WebSocket handler.

    This is designed to wrap the existing ws.py message handler.
    """

    async def shadow_aware_handler(websocket, message: Dict[str, Any]):
        """Shadow-aware WebSocket handler"""
        try:
            # Extract room state if available
            room_state = None
            if hasattr(websocket, "room_id"):
                # Get room state from room manager
                # This would connect to your actual room management
                room_state = {
                    "room_id": websocket.room_id,
                    # Add other room state as needed
                }

            # Handle with shadow mode if enabled
            response = await handle_with_shadow(websocket, message, room_state)

            # Send response back
            if response:
                await websocket.send_json(response)

        except Exception as e:
            logger.error(f"Shadow mode handler error: {e}")
            # Fall back to current handler
            await current_ws_handler(websocket, message)

    return shadow_aware_handler


class RefactoredHandlerAdapter:
    """
    Adapter to make refactored handlers compatible with shadow mode.

    This bridges the gap between new clean architecture handlers
    and the existing WebSocket interface.
    """

    def __init__(self, command_bus):
        """
        Initialize with command bus from clean architecture.

        Args:
            command_bus: The command bus that routes to use cases
        """
        self.command_bus = command_bus

    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]],
        broadcast_func: Callable,
    ):
        """Adapt refactored handler to shadow mode interface"""
        action = message.get("action")
        data = message.get("data", {})

        # Map WebSocket message to command
        command = self._map_to_command(action, data, room_state)

        if not command:
            return {"event": "error", "data": {"message": f"Unknown action: {action}"}}

        # Execute command through command bus
        result = await self.command_bus.execute(command)

        # Map command result to WebSocket response
        response = self._map_to_response(action, result)

        # Handle any broadcasts
        if hasattr(result, "broadcasts"):
            for broadcast in result.broadcasts:
                await broadcast_func(
                    broadcast["room_id"], broadcast["event"], broadcast["data"]
                )

        return response

    def _map_to_command(
        self, action: str, data: Dict[str, Any], room_state: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """Map WebSocket action to command object"""
        # This would map to your actual command classes
        command_mapping = {
            "create_room": lambda: CreateRoomCommand(
                player_name=data.get("player_name")
            ),
            "join_room": lambda: JoinRoomCommand(
                room_id=data.get("room_id"), player_name=data.get("player_name")
            ),
            "start_game": lambda: StartGameCommand(
                room_id=room_state.get("room_id") if room_state else None
            ),
            "declare": lambda: DeclareCommand(
                player_name=data.get("player_name"),
                value=data.get("value"),
                room_id=room_state.get("room_id") if room_state else None,
            ),
            "play": lambda: PlayPiecesCommand(
                player_name=data.get("player_name"),
                indices=data.get("indices"),
                room_id=room_state.get("room_id") if room_state else None,
            ),
        }

        creator = command_mapping.get(action)
        return creator() if creator else None

    def _map_to_response(self, action: str, result: Any) -> Dict[str, Any]:
        """Map command result to WebSocket response"""
        # Map based on action and result
        if hasattr(result, "success") and not result.success:
            return {
                "event": "error",
                "data": {
                    "message": getattr(result, "error_message", "Operation failed"),
                    "type": f"{action}_error",
                },
            }

        # Success responses
        response_mapping = {
            "create_room": lambda r: {
                "event": "room_created",
                "data": {
                    "room_id": r.room_id,
                    "host_name": r.host_name,
                    "success": True,
                },
            },
            "join_room": lambda r: {
                "event": "room_joined",
                "data": {
                    "room_id": r.room_id,
                    "player_name": r.player_name,
                    "assigned_slot": r.assigned_slot,
                    "success": True,
                },
            },
            "start_game": lambda r: {
                "event": "game_started",
                "data": {"room_id": r.room_id, "success": True},
            },
        }

        mapper = response_mapping.get(action)
        if mapper:
            return mapper(result)

        # Default response
        return {"event": f"{action}_success", "data": {"success": True}}


# Example command classes (these would be in your clean architecture)
class CreateRoomCommand:
    def __init__(self, player_name: str):
        self.player_name = player_name


class JoinRoomCommand:
    def __init__(self, room_id: str, player_name: str):
        self.room_id = room_id
        self.player_name = player_name


class StartGameCommand:
    def __init__(self, room_id: str):
        self.room_id = room_id


class DeclareCommand:
    def __init__(self, player_name: str, value: int, room_id: str):
        self.player_name = player_name
        self.value = value
        self.room_id = room_id


class PlayPiecesCommand:
    def __init__(self, player_name: str, indices: list, room_id: str):
        self.player_name = player_name
        self.indices = indices
        self.room_id = room_id


def integrate_shadow_mode_with_websocket(app):
    """
    Integrate shadow mode with FastAPI WebSocket routes.

    This would be called during app initialization.
    """

    # Import existing handler
    from api.routes.ws import handle_websocket_message

    # Create shadow adapter
    adapter = ShadowModeWebSocketAdapter(handle_websocket_message)

    # Store adapter for later configuration
    app.state.shadow_adapter = adapter

    # Create wrapped handler
    shadow_handler = create_shadow_mode_wrapper(handle_websocket_message)

    # Replace WebSocket handler with shadow-aware version
    # This depends on your app structure

    logger.info("Shadow mode integration complete")

    return adapter
