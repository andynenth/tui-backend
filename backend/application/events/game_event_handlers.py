# application/events/game_event_handlers.py
"""
Event handlers for game-related domain events.
"""

import logging
from typing import Dict, Any, List

from domain.events.game_events import (
    GameStartedEvent,
    RoundStartedEvent,
    TurnPlayedEvent,
    PhaseChangedEvent,
    PlayerDeclaredEvent,
    RoundEndedEvent,
    GameEndedEvent,
    WeakHandRequestedEvent,
    RedealAcceptedEvent,
    RedealDeclinedEvent,
    PiecesDealtEvent,
    WinnerDeterminedEvent
)
from domain.events.player_events import (
    PlayerJoinedEvent,
    PlayerLeftEvent,
    PlayerReadyEvent,
    HostTransferredEvent
)
from domain.events.base import DomainEvent

from application.events.event_handler import AsyncEventHandler
from application.interfaces.notification_service import NotificationService
from application.services.room_service import RoomService

logger = logging.getLogger(__name__)


class GameNotificationHandler(AsyncEventHandler[DomainEvent]):
    """
    Handles game events and sends appropriate notifications.
    
    This handler translates domain events into WebSocket notifications
    that the frontend can understand.
    """
    
    def __init__(
        self,
        notification_service: NotificationService,
        room_service: RoomService
    ):
        """Initialize with required services."""
        self._notification_service = notification_service
        self._room_service = room_service
    
    async def handle(self, event: DomainEvent) -> None:
        """Route event to appropriate handler method."""
        handler_method = getattr(self, f'_handle_{event.__class__.__name__}', None)
        if handler_method:
            await handler_method(event)
        else:
            logger.debug(f"No handler for event type: {event.__class__.__name__}")
    
    async def _handle_GameStartedEvent(self, event: GameStartedEvent) -> None:
        """Handle game started event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "game_started",
            {
                "room_id": event.aggregate_id,
                "players": event.data["players"],
                "initial_phase": event.data["initial_phase"],
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_RoundStartedEvent(self, event: RoundStartedEvent) -> None:
        """Handle round started event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "round_started",
            {
                "room_id": event.aggregate_id,
                "round_number": event.data["round_number"],
                "dealer": event.data["dealer"],
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_TurnPlayedEvent(self, event: TurnPlayedEvent) -> None:
        """Handle turn played event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "turn_played",
            {
                "room_id": event.aggregate_id,
                "player": event.data["player"],
                "pieces": event.data["pieces"],
                "turn_number": event.data.get("turn_number", 0),
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_PhaseChangedEvent(self, event: PhaseChangedEvent) -> None:
        """Handle phase changed event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "phase_changed",
            {
                "room_id": event.aggregate_id,
                "old_phase": event.data["old_phase"],
                "new_phase": event.data["new_phase"],
                "phase_data": event.data.get("phase_data", {}),
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_PlayerDeclaredEvent(self, event: PlayerDeclaredEvent) -> None:
        """Handle player declared event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "player_declared",
            {
                "room_id": event.aggregate_id,
                "player": event.data["player"],
                "declared_piles": event.data["declared_piles"],
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_RoundEndedEvent(self, event: RoundEndedEvent) -> None:
        """Handle round ended event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "round_ended",
            {
                "room_id": event.aggregate_id,
                "round_number": event.data["round_number"],
                "scores": event.data["scores"],
                "total_scores": event.data.get("total_scores", {}),
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_GameEndedEvent(self, event: GameEndedEvent) -> None:
        """Handle game ended event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "game_ended",
            {
                "room_id": event.aggregate_id,
                "final_scores": event.data["final_scores"],
                "winner": event.data["winner"],
                "reason": event.data["reason"],
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_PlayerJoinedEvent(self, event: PlayerJoinedEvent) -> None:
        """Handle player joined event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "player_joined",
            {
                "room_id": event.aggregate_id,
                "player": event.data["player"],
                "players": event.data.get("players", []),
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def _handle_PlayerLeftEvent(self, event: PlayerLeftEvent) -> None:
        """Handle player left event."""
        await self._notification_service.notify_room(
            event.aggregate_id,
            "player_left",
            {
                "room_id": event.aggregate_id,
                "player": event.data["player"],
                "reason": event.data.get("reason", "disconnected"),
                "replacement": event.data.get("replacement"),
                "timestamp": event.timestamp.isoformat()
            }
        )


class GameStateUpdateHandler(AsyncEventHandler[DomainEvent]):
    """
    Updates game state projections based on domain events.
    
    This handler maintains read models for fast queries.
    """
    
    def __init__(self, room_service: RoomService):
        """Initialize with room service."""
        self._room_service = room_service
    
    async def handle(self, event: DomainEvent) -> None:
        """Update state based on event type."""
        # In a full implementation, this would update read models
        # For now, we'll just log the state change
        logger.debug(
            f"State update for {event.__class__.__name__}: "
            f"aggregate={event.aggregate_id}"
        )


class BotActionHandler(AsyncEventHandler[DomainEvent]):
    """
    Triggers bot actions based on game events.
    
    This handler watches for events that require bot responses
    and triggers the appropriate bot actions.
    """
    
    def __init__(self, bot_service):
        """Initialize with bot service."""
        self._bot_service = bot_service
    
    async def handle(self, event: DomainEvent) -> None:
        """Check if bots need to take action."""
        from application.services.bot_service import BotService
        
        # Handle events that might trigger bot actions
        if isinstance(event, PhaseChangedEvent):
            room_id = event.aggregate_id
            new_phase = event.data["new_phase"]
            
            # Check if any bots need to act in the new phase
            if new_phase in ["DECLARATION", "TURN"]:
                await self._trigger_bot_actions(room_id, new_phase)
        
        elif isinstance(event, TurnPlayedEvent):
            # Check if it's now a bot's turn
            room_id = event.aggregate_id
            await self._trigger_bot_actions(room_id, "TURN")
    
    async def _trigger_bot_actions(self, room_id: str, phase: str) -> None:
        """Trigger bot actions for the given phase."""
        try:
            # Get room info to check for bots
            room = await self._bot_service._get_room(room_id)
            if not room:
                return
            
            # Find bots that need to act
            for player in room.players:
                if player.is_bot:
                    # Bot service will handle the actual action
                    logger.debug(f"Bot {player.name} may need to act in {phase}")
                    # The bot service's own logic will handle when to act
        
        except Exception as e:
            logger.error(f"Error triggering bot actions: {str(e)}", exc_info=True)


class AuditLogHandler(AsyncEventHandler[DomainEvent]):
    """
    Creates audit log entries for important game events.
    
    This handler ensures compliance and provides a complete
    audit trail of game activities.
    """
    
    def __init__(self, audit_service=None):
        """Initialize with audit service."""
        self._audit_service = audit_service
    
    async def handle(self, event: DomainEvent) -> None:
        """Log event for audit purposes."""
        # Define which events to audit
        auditable_events = {
            GameStartedEvent,
            GameEndedEvent,
            PlayerJoinedEvent,
            PlayerLeftEvent,
            HostTransferredEvent,
            WinnerDeterminedEvent
        }
        
        if type(event) in auditable_events:
            await self._create_audit_entry(event)
    
    async def _create_audit_entry(self, event: DomainEvent) -> None:
        """Create an audit log entry."""
        entry = {
            "event_id": event.event_id,
            "event_type": event.__class__.__name__,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        # In a real implementation, this would persist to audit storage
        logger.info(f"Audit log: {entry}")