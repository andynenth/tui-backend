# application/use_cases/room_management.py
"""
Use cases for room management operations.
"""

import logging

from domain.events.player_events import (
    RoomSettingsUpdatedEvent,
    PlayerKickedEvent,
    HostTransferredEvent,
    RoomClosedEvent
)

from ..commands.room_commands import (
    UpdateRoomSettingsCommand,
    KickPlayerCommand,
    TransferHostCommand,
    CloseRoomCommand,
    LeaveRoomCommand
)
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.notification_service import NotificationService
from ..services.room_service import RoomService

logger = logging.getLogger(__name__)


class UpdateRoomSettingsUseCase(CommandHandler[bool]):
    """Use case for updating room settings."""
    
    def __init__(
        self,
        room_service: RoomService,
        notification_service: NotificationService
    ):
        self._room_service = room_service
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, UpdateRoomSettingsCommand)
    
    async def handle(self, command: UpdateRoomSettingsCommand) -> CommandResult[bool]:
        try:
            # Get room info
            room_info = await self._room_service.get_room_info(command.room_id)
            if not room_info:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room_info.host_name != command.player_name:
                return CommandResult.fail("Only the host can update settings")
            
            # Update settings
            success = await self._room_service.update_room_settings(
                command.room_id,
                command.settings
            )
            
            if success:
                logger.info(f"Room {command.room_id} settings updated")
                return CommandResult.ok(True)
            else:
                return CommandResult.fail("Failed to update settings")
                
        except Exception as e:
            logger.error(f"Failed to update room settings: {str(e)}")
            return CommandResult.fail(str(e))


class KickPlayerUseCase(CommandHandler[bool]):
    """Use case for kicking a player from a room."""
    
    def __init__(
        self,
        room_service: RoomService,
        notification_service: NotificationService
    ):
        self._room_service = room_service
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, KickPlayerCommand)
    
    async def handle(self, command: KickPlayerCommand) -> CommandResult[bool]:
        try:
            # Get room info
            room_info = await self._room_service.get_room_info(command.room_id)
            if not room_info:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room_info.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can kick players")
            
            # Can't kick yourself
            if command.requesting_player == command.player_to_kick:
                return CommandResult.fail("Cannot kick yourself")
            
            # Remove player
            success = await self._room_service.remove_player(
                command.room_id,
                command.player_to_kick,
                reason="kicked"
            )
            
            if success:
                logger.info(
                    f"{command.player_to_kick} kicked from room {command.room_id} "
                    f"by {command.requesting_player}"
                )
                return CommandResult.ok(True)
            else:
                return CommandResult.fail("Player not found in room")
                
        except Exception as e:
            logger.error(f"Failed to kick player: {str(e)}")
            return CommandResult.fail(str(e))


class TransferHostUseCase(CommandHandler[bool]):
    """Use case for transferring host privileges."""
    
    def __init__(
        self,
        room_repository,
        event_publisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, TransferHostCommand)
    
    async def handle(self, command: TransferHostCommand) -> CommandResult[bool]:
        try:
            # Get room
            room = await self._room_repository.get(command.room_id)
            if not room:
                return CommandResult.fail("Room not found")
            
            # Verify current host
            if room.host_name != command.current_host:
                return CommandResult.fail("You are not the host")
            
            # Verify new host is in room
            if not room.has_player(command.new_host):
                return CommandResult.fail("New host is not in the room")
            
            # Transfer host
            room.host_name = command.new_host
            await self._room_repository.save(room)
            
            # Publish event
            await self._event_publisher.publish(
                HostTransferredEvent(
                    room_id=command.room_id,
                    old_host=command.current_host,
                    new_host=command.new_host
                )
            )
            
            # Notify room
            await self._notification_service.notify_room(
                command.room_id,
                "host_transferred",
                {
                    "old_host": command.current_host,
                    "new_host": command.new_host
                }
            )
            
            logger.info(
                f"Host transferred from {command.current_host} to {command.new_host} "
                f"in room {command.room_id}"
            )
            
            return CommandResult.ok(True)
            
        except Exception as e:
            logger.error(f"Failed to transfer host: {str(e)}")
            return CommandResult.fail(str(e))


class CloseRoomUseCase(CommandHandler[bool]):
    """Use case for closing a room."""
    
    def __init__(
        self,
        room_repository,
        event_publisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, CloseRoomCommand)
    
    async def handle(self, command: CloseRoomCommand) -> CommandResult[bool]:
        try:
            # Get room
            room = await self._room_repository.get(command.room_id)
            if not room:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can close the room")
            
            # Notify all players before closing
            await self._notification_service.notify_room(
                command.room_id,
                "room_closing",
                {
                    "reason": "host_closed"
                }
            )
            
            # Close room
            room.is_closed = True
            await self._room_repository.save(room)
            
            # Publish event
            await self._event_publisher.publish(
                RoomClosedEvent(
                    room_id=command.room_id,
                    reason="host_closed"
                )
            )
            
            logger.info(f"Room {command.room_id} closed by host")
            
            return CommandResult.ok(True)
            
        except Exception as e:
            logger.error(f"Failed to close room: {str(e)}")
            return CommandResult.fail(str(e))


class LeaveRoomUseCase(CommandHandler[bool]):
    """Use case for leaving a room."""
    
    def __init__(
        self,
        room_service: RoomService
    ):
        self._room_service = room_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, LeaveRoomCommand)
    
    async def handle(self, command: LeaveRoomCommand) -> CommandResult[bool]:
        try:
            # Remove player from room
            success = await self._room_service.remove_player(
                command.room_id,
                command.player_name,
                reason="left"
            )
            
            if success:
                logger.info(f"{command.player_name} left room {command.room_id}")
                return CommandResult.ok(True)
            else:
                return CommandResult.fail("Player not in room")
                
        except Exception as e:
            logger.error(f"Failed to leave room: {str(e)}")
            return CommandResult.fail(str(e))