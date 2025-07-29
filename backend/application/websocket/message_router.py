"""
WebSocket Message Router
Routes WebSocket messages to appropriate handlers
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import WebSocket

from application.websocket.route_registry import (
    get_handler_for_event,
    is_supported_event,
    get_event_category
)
from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from application.websocket.websocket_config import websocket_config
from api.websocket.message_queue import message_queue_manager
from infrastructure.websocket.connection_singleton import broadcast
from infrastructure.dependencies import get_unit_of_work
from application.services.room_application_service import RoomApplicationService
from infrastructure.monitoring.metrics_integration import MetricsContext, metrics_collector

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Routes WebSocket messages to appropriate handlers.
    Handles business logic routing without infrastructure concerns.
    """
    
    def __init__(self):
        """Initialize the message router."""
        self.use_case_dispatcher = UseCaseDispatcher()
        self._message_count = 0
        self._error_count = 0
        
        # Lazy load adapter wrapper for migration mode
        self._adapter_wrapper = None
        
    async def route_message(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        room_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Route a message to the appropriate handler.
        
        Args:
            websocket: The WebSocket connection
            message: The message to route
            room_id: The room ID
            
        Returns:
            Response dict or None
        """
        self._message_count += 1
        
        # Extract event name (support both 'event' and 'action' for compatibility)
        event = message.get("event") or message.get("action")
        
        if not event:
            self._error_count += 1
            return {
                "event": "error",
                "data": {
                    "message": "Missing event/action in message",
                    "type": "routing_error"
                }
            }
            
        # Log routing decision
        category = get_event_category(event)
        logger.debug(
            f"Routing message {self._message_count}: "
            f"event={event}, category={category}, room={room_id}"
        )
        
        # Check if it's a supported event
        if not is_supported_event(event):
            logger.warning(f"Unsupported event: {event}")
            self._error_count += 1
            return {
                "event": "error",
                "data": {
                    "message": f"Unsupported event: {event}",
                    "type": "unsupported_event"
                }
            }
            
        try:
            # Track metrics for this event
            async with MetricsContext(event) as ctx:
                # Determine routing based on configuration
                if websocket_config.should_use_use_case(event):
                    # Route through use case dispatcher
                    response = await self._route_to_use_case(websocket, message, room_id, event)
                else:
                    # Route through adapter system (for migration)
                    response = await self._route_to_adapter(websocket, message, room_id)
                
                # Handle queued messages if needed
                await self._check_message_queue(websocket, room_id)
                
                # Record message metrics
                await metrics_collector.record_message_received(event, message)
                if response:
                    await metrics_collector.record_message_sent(
                        response.get("event", event),
                        response
                    )
                
                return response
            
        except Exception as e:
            logger.error(f"Error routing message: {e}", exc_info=True)
            self._error_count += 1
            return {
                "event": "error",
                "data": {
                    "message": f"Failed to process {event}",
                    "type": "routing_error",
                    "details": str(e)
                }
            }
            
    async def _route_to_use_case(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        room_id: str,
        event: str
    ) -> Optional[Dict[str, Any]]:
        """
        Route message to use case dispatcher.
        
        Args:
            websocket: The WebSocket connection
            message: The message to route
            room_id: The room ID
            event: The event name
            
        Returns:
            Response from use case or None
        """
        # Get room state if needed
        room_state = None
        if room_id != "lobby":
            room_state = await self._get_room_state(room_id)
        
        # Extract player info from connection
        player_id = None
        player_name = None
        
        websocket_id = getattr(websocket, "_ws_id", None)
        if websocket_id:
            from api.websocket.connection_manager import connection_manager
            connection = connection_manager.get_connection_by_websocket_id(websocket_id)
            if connection:
                player_id = connection.player_id
                player_name = connection.player_name
        
        # For client_ready events in rooms, extract player name from data
        if event == "client_ready" and room_id != "lobby":
            data_player_name = message.get("data", {}).get("player_name")
            if data_player_name:
                player_name = data_player_name
                # Update the connection manager with the real player name
                if websocket_id and (not connection or player_name != connection.player_name):
                    # Find the correct player_id from room state
                    correct_player_id = None
                    if room_state and room_state.get("players"):
                        for player in room_state["players"]:
                            if player and player.get("name") == player_name:
                                correct_player_id = player.get("player_id")
                                break
                    
                    await connection_manager.register_player(room_id, player_name, websocket_id, correct_player_id)
                    logger.info(f"Updated player registration: {player_name} for room {room_id} with player_id {correct_player_id}")
        
        # Create dispatch context
        context = DispatchContext(
            websocket=websocket,
            room_id=room_id,
            room_state=room_state,
            player_id=player_id,
            player_name=player_name
        )
        
        # Get event data
        data = message.get("data", {})
        
        # Dispatch to use case
        response = await self.use_case_dispatcher.dispatch(event, data, context)
        
        return response
    
    async def _route_to_adapter(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        room_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Route message to adapter system (for migration).
        
        Args:
            websocket: The WebSocket connection
            message: The message to route
            room_id: The room ID
            
        Returns:
            Response from adapter or None
        """
        # Lazy load adapter wrapper
        if self._adapter_wrapper is None:
            from api.routes.ws_adapter_wrapper import adapter_wrapper
            self._adapter_wrapper = adapter_wrapper
        
        # Get room state for adapters if needed
        room_state = None
        if room_id != "lobby":
            room_state = await self._get_room_state(room_id)
        
        # Call adapter wrapper
        response = await self._adapter_wrapper.try_handle_with_adapter(
            websocket,
            message,
            room_id,
            room_state
        )
        
        return response
        
    async def _get_room_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get room state for adapter processing.
        
        Args:
            room_id: The room ID
            
        Returns:
            Room state dict or None
        """
        try:
            uow = get_unit_of_work()
            # Don't use RoomApplicationService here - just get the room directly
            
            async with uow:
                room = await uow.rooms.get_by_id(room_id)
                
                if room:
                    # Get players from room slots
                    players = []
                    for i, slot in enumerate(room.slots):
                        if slot:
                            players.append({
                                "player_id": f"{room_id}_p{i}",
                                "name": slot.name,
                                "is_bot": slot.is_bot,
                                "is_host": i == 0,  # First slot is always host
                                "seat_position": i
                            })
                    
                    # Convert to dict format expected by adapters
                    return {
                        "room_id": room.room_id,
                        "host": f"{room.room_id}_p0",  # Host is always in slot 0
                        "players": players,
                        "status": room.status.value if hasattr(room.status, 'value') else str(room.status),
                        "game_config": {
                            "max_players": room.max_slots,
                            "max_score": 50,
                            "allow_bot_start": True
                        },
                        "current_round": room.current_round if hasattr(room, 'current_round') else 1,
                        "max_players": room.max_slots
                    }
                    
        except Exception as e:
            logger.error(f"Error getting room state: {e}")
            
        return None
        
    async def _check_message_queue(
        self,
        websocket: WebSocket,
        room_id: str
    ) -> None:
        """
        Check and send any queued messages for reconnected players.
        
        Args:
            websocket: The WebSocket connection
            room_id: The room ID
        """
        # Get websocket ID
        websocket_id = getattr(websocket, "_ws_id", None)
        if not websocket_id:
            return
            
        # Check for player info
        from api.websocket.connection_manager import connection_manager
        connection = connection_manager.get_connection_by_websocket_id(websocket_id)
        
        if connection and connection.player_name:
            # Check for queued messages
            queued_messages = await message_queue_manager.get_queued_messages(
                room_id,
                connection.player_name
            )
            
            if queued_messages:
                logger.info(
                    f"Sending {len(queued_messages)} queued messages to "
                    f"{connection.player_name}"
                )
                
                for message in queued_messages:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending queued message: {e}")
                        
    async def handle_room_validation(
        self,
        websocket: WebSocket,
        room_id: str
    ) -> bool:
        """
        Handle room validation for non-lobby connections.
        
        Args:
            websocket: The WebSocket connection  
            room_id: The room ID
            
        Returns:
            True if room exists or is lobby, False otherwise
        """
        if room_id == "lobby":
            return True
            
        logger.debug(f"[ROOM_LOOKUP_DEBUG] Checking if room exists: {room_id}")
        
        try:
            uow = get_unit_of_work()
            async with uow:
                room = await uow.rooms.get_by_id(room_id)
                
                if not room:
                    logger.warning(
                        f"[ROOM_LOOKUP_DEBUG] Room {room_id} not found in "
                        f"clean architecture repository!"
                    )
                    
                    # Send room_not_found event
                    await websocket.send_json({
                        "event": "room_not_found",
                        "data": {
                            "room_id": room_id,
                            "message": "This game room no longer exists",
                            "suggestion": "The server may have restarted. "
                                        "Please create or join a new game.",
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    })
                    
                    logger.info(f"Sent room_not_found for non-existent room: {room_id}")
                    return False
                else:
                    logger.info(
                        f"[ROOM_LOOKUP_DEBUG] Room {room_id} found successfully "
                        f"in clean architecture!"
                    )
                    return True
                    
        except Exception as e:
            logger.error(f"[ROOM_LOOKUP_DEBUG] Error checking room existence: {e}", exc_info=True)
            # Don't fail the connection, just log the error
            return True
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics.
        
        Returns:
            Stats dict
        """
        return {
            "messages_routed": self._message_count,
            "errors": self._error_count,
            "error_rate": self._error_count / max(1, self._message_count)
        }