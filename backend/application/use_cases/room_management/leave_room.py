"""
Use case for leaving a room.

This use case handles players leaving rooms, including host migration
and room cleanup when empty.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.room_management import LeaveRoomRequest, LeaveRoomResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import ResourceNotFoundException, ValidationException
from backend.domain.events.room_events import PlayerLeftRoom, HostChanged, RoomClosed
from backend.domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class LeaveRoomUseCase(UseCase[LeaveRoomRequest, LeaveRoomResponse]):
    """
    Handles players leaving rooms.
    
    This use case:
    1. Removes player from room
    2. Handles host migration if needed
    3. Closes room if empty
    4. Converts to bot if game in progress
    5. Emits appropriate events
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics
    
    async def execute(self, request: LeaveRoomRequest) -> LeaveRoomResponse:
        """
        Leave a room.
        
        Args:
            request: The leave request
            
        Returns:
            Response with leave details
            
        Raises:
            ResourceNotFoundException: If room or player not found
            ValidationException: If request is invalid
        """
        # Validate request
        if not request.player_id:
            raise ValidationException({"player_id": "Player ID is required"})
        if not request.room_id:
            raise ValidationException({"room_id": "Room ID is required"})
        
        async with self._uow:
            # Get the room
            room = await self._uow.rooms.get_by_id(request.room_id)
            if not room:
                raise ResourceNotFoundException("Room", request.room_id)
            
            # Find player in room
            player_slot = None
            slot_index = None
            for i, slot in enumerate(room.slots):
                if slot and slot.id == request.player_id:
                    player_slot = slot
                    slot_index = i
                    break
            
            if not player_slot:
                raise ResourceNotFoundException("Player", request.player_id)
            
            # Check if player is host
            was_host = room.host_id == request.player_id
            
            # Remove player or convert to bot if game in progress
            if room.current_game:
                # Convert to bot instead of removing
                player_slot.is_bot = True
                player_slot.is_connected = False
                logger.info(f"Converted player {request.player_id} to bot in active game")
            else:
                # Remove player from room
                room.remove_player(request.player_id)
            
            # Handle host migration if needed
            new_host_id = None
            if was_host and room.player_count > 0:
                # Find new host (first connected non-bot player)
                for slot in room.slots:
                    if slot and not slot.is_bot and slot.id != request.player_id:
                        if getattr(slot, 'is_connected', True):
                            new_host_id = slot.id
                            room.host_id = new_host_id
                            break
                
                # Fallback to any player if no connected players
                if not new_host_id:
                    for slot in room.slots:
                        if slot and slot.id != request.player_id:
                            new_host_id = slot.id
                            room.host_id = new_host_id
                            break
            
            # Check if room should be closed
            room_closed = False
            if room.player_count == 0 or (
                room.player_count > 0 and 
                all(slot.is_bot for slot in room.slots if slot)
            ):
                room_closed = True
            
            # Save or delete room
            if room_closed:
                await self._uow.rooms.delete(room.id)
            else:
                await self._uow.rooms.save(room)
            
            # Emit PlayerLeftRoom event
            event = PlayerLeftRoom(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                player_id=request.player_id,
                player_name=player_slot.name,
                reason=request.reason or "Player left",
                remaining_players=room.player_count if not room_closed else 0,
                converted_to_bot=room.current_game is not None
            )
            await self._event_publisher.publish(event)
            
            # Emit HostChanged if needed
            if new_host_id:
                new_host = next(
                    (slot for slot in room.slots if slot and slot.id == new_host_id),
                    None
                )
                if new_host:
                    host_event = HostChanged(
                        metadata=EventMetadata(user_id=request.user_id),
                        room_id=room.id,
                        old_host_id=request.player_id,
                        new_host_id=new_host_id,
                        new_host_name=new_host.name,
                        reason="Previous host left room"
                    )
                    await self._event_publisher.publish(host_event)
            
            # Emit RoomClosed if needed
            if room_closed:
                close_event = RoomClosed(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    room_code=room.code,
                    reason="All players left" if room.player_count == 0 else "Only bots remain"
                )
                await self._event_publisher.publish(close_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "room.left",
                    tags={
                        "was_host": str(was_host).lower(),
                        "room_closed": str(room_closed).lower(),
                        "reason": request.reason or "voluntary"
                    }
                )
            
            # Create response
            response = LeaveRoomResponse(
                success=True,
                request_id=request.request_id,
                room_id=room.id,
                new_host_id=new_host_id,
                room_closed=room_closed
            )
            
            logger.info(
                f"Player {player_slot.name} left room {room.code}",
                extra={
                    "player_id": request.player_id,
                    "room_id": room.id,
                    "new_host_id": new_host_id,
                    "room_closed": room_closed
                }
            )
            
            self._log_execution(request, response)
            return response