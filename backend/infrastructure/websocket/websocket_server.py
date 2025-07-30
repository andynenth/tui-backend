"""
WebSocket Server Infrastructure
Pure WebSocket handling without business logic
"""

import asyncio
import logging
import uuid
import time
from typing import Optional, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.websocket.connection_singleton import (
    register,
    unregister,
    get_connection_id_for_websocket,
)
from api.websocket.connection_manager import connection_manager
from api.validation import validate_websocket_message
from api.middleware.websocket_rate_limit import (
    check_websocket_rate_limit,
    send_rate_limit_error,
)

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    Pure WebSocket infrastructure handling.
    Manages connections, message reception, and basic validation.
    No business logic or routing decisions.
    """

    def __init__(self, rate_limit_config: Optional[Dict[str, Any]] = None):
        """
        Initialize WebSocket server.

        Args:
            rate_limit_config: Optional rate limiting configuration
        """
        self.rate_limit_config = rate_limit_config or {}
        self._cleanup_task = None

    async def accept_connection(self, websocket: WebSocket) -> None:
        """
        Accept a WebSocket connection.
        Note: This is now handled in the route handler to avoid double accept.

        Args:
            websocket: The WebSocket connection to accept
        """
        # Accept is now handled in the route handler
        pass

    async def handle_connection(self, websocket: WebSocket, room_id: str) -> str:
        """
        Handle WebSocket connection lifecycle.

        Args:
            websocket: The WebSocket connection
            room_id: The room ID to connect to

        Returns:
            connection_id: The unique connection identifier
        """
        # Generate unique ID for this websocket
        websocket._ws_id = str(uuid.uuid4())

        logger.info(
            f"🔌 [ROOM_DEBUG] New WebSocket connection to room '{room_id}', "
            f"ws_id: {websocket._ws_id} at {time.time()}"
        )

        # Register the connection
        connection_id = await register(room_id, websocket)

        # Store connection_id on websocket for later retrieval
        websocket._connection_id = connection_id

        return connection_id

    async def receive_message(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """
        Receive and validate a message from WebSocket.

        Args:
            websocket: The WebSocket connection

        Returns:
            Validated message dict or None if invalid
        """
        try:
            message = await websocket.receive_json()

            # Validate the message structure and content
            is_valid, error_msg, sanitized_data = validate_websocket_message(message)

            if not is_valid:
                await self.send_error(
                    websocket, f"Invalid message: {error_msg}", "validation_error"
                )
                return None

            return message

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """
        Send a message through WebSocket.

        Args:
            websocket: The WebSocket connection
            message: The message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def send_error(
        self, websocket: WebSocket, message: str, error_type: str = "error"
    ) -> None:
        """
        Send an error message through WebSocket.

        Args:
            websocket: The WebSocket connection
            message: The error message
            error_type: The type of error
        """
        error_response = {
            "event": "error",
            "data": {
                "message": message,
                "type": error_type,
            },
        }
        await self.send_message(websocket, error_response)

    async def check_rate_limit(
        self, websocket: WebSocket, event: str, websocket_id: str
    ) -> bool:
        """
        Check if the request is rate limited.

        Args:
            websocket: The WebSocket connection
            event: The event being processed
            websocket_id: The WebSocket ID

        Returns:
            True if rate limited, False otherwise
        """
        if not self.rate_limit_config.get("enabled", False):
            return False

        is_limited = await check_websocket_rate_limit(event, websocket_id)

        if is_limited:
            await send_rate_limit_error(websocket)

        return is_limited

    async def handle_disconnect(
        self, websocket: WebSocket, room_id: str, websocket_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Handle WebSocket disconnection.

        Args:
            websocket: The WebSocket connection
            room_id: The room ID
            websocket_id: Optional WebSocket ID

        Returns:
            connection_id if found, None otherwise
        """
        # Get websocket_id from the websocket object or use provided one
        if not websocket_id:
            websocket_id = getattr(websocket, "_ws_id", None)

        logger.info(
            f"🔌 [ROOM_DEBUG] Handling disconnect for room '{room_id}', "
            f"websocket_id: {websocket_id} at {time.time()}"
        )

        # Get connection info before unregistering
        connection = None
        connection_id = None

        if websocket_id:
            # Try to get player info from connection manager
            connection = connection_manager.get_connection_by_websocket_id(websocket_id)
            if connection:
                logger.info(
                    f"🔌 [ROOM_DEBUG] Found connection for websocket_id {websocket_id}: "
                    f"player={connection.player_name}, room={connection.room_id}"
                )

        # Try to get connection_id from websocket attribute
        connection_id = getattr(websocket, "_connection_id", None)
        if not connection_id:
            connection_id = await get_connection_id_for_websocket(websocket)

        if not connection_id:
            logger.warning(f"No connection_id found for websocket in room {room_id}")

        # Unregister the connection
        if connection_id:
            await unregister(connection_id)
            logger.info(
                f"🔌 [ROOM_DEBUG] WebSocket unregistered from room '{room_id}' "
                f"(connection_id: {connection_id})"
            )

        return connection_id

    def ensure_cleanup_task_running(self) -> None:
        """
        Ensure the room cleanup background task is running.
        This is a simple task starter, actual cleanup logic is elsewhere.
        """
        # This will be moved to a proper task manager in Phase 4
        # For now, just log that it should be started
        logger.info("🧹 [ROOM_DEBUG] Cleanup task check requested")
