# application/use_cases/bot_management.py
"""
Use cases for bot management operations.
"""

import logging

from ..commands.game_commands import (
    AddBotCommand,
    RemoveBotCommand,
    ConfigureBotCommand
)
from ..commands.base import CommandHandler, CommandResult
from ..services.bot_service import BotService
from ..services.room_service import RoomService

logger = logging.getLogger(__name__)


class AddBotUseCase(CommandHandler[bool]):
    """Use case for adding a bot to a room."""
    
    def __init__(
        self,
        room_service: RoomService,
        bot_service: BotService,
        room_repository
    ):
        self._room_service = room_service
        self._bot_service = bot_service
        self._room_repository = room_repository
    
    def can_handle(self, command) -> bool:
        return isinstance(command, AddBotCommand)
    
    async def handle(self, command: AddBotCommand) -> CommandResult[bool]:
        try:
            # Get room info
            room_info = await self._room_service.get_room_info(command.room_id)
            if not room_info:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room_info.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can add bots")
            
            # Check if room is full
            if room_info.is_full:
                return CommandResult.fail("Room is full")
            
            # Check if game is in progress
            if room_info.game_in_progress:
                return CommandResult.fail("Cannot add bot while game is in progress")
            
            # Check if bot name is already taken
            if command.bot_name in room_info.players:
                return CommandResult.fail(f"Name '{command.bot_name}' is already taken")
            
            # Add bot to bot service
            bot_info = await self._bot_service.add_bot(
                room_id=command.room_id,
                bot_name=command.bot_name,
                difficulty=command.difficulty,
                play_speed=command.play_speed if hasattr(command, 'play_speed') else 2000
            )
            
            # Add bot as player to room
            room = await self._room_repository.get(command.room_id)
            if room:
                room.add_player(command.bot_name)
                await self._room_repository.save(room)
            
            logger.info(
                f"Bot {command.bot_name} ({command.difficulty}) added to room {command.room_id}"
            )
            
            return CommandResult.ok(True)
            
        except Exception as e:
            logger.error(f"Failed to add bot: {str(e)}")
            return CommandResult.fail(str(e))


class RemoveBotUseCase(CommandHandler[bool]):
    """Use case for removing a bot from a room."""
    
    def __init__(
        self,
        room_service: RoomService,
        bot_service: BotService
    ):
        self._room_service = room_service
        self._bot_service = bot_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, RemoveBotCommand)
    
    async def handle(self, command: RemoveBotCommand) -> CommandResult[bool]:
        try:
            # Get room info
            room_info = await self._room_service.get_room_info(command.room_id)
            if not room_info:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room_info.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can remove bots")
            
            # Check if game is in progress
            if room_info.game_in_progress:
                return CommandResult.fail("Cannot remove bot while game is in progress")
            
            # Check if it's actually a bot
            if not self._bot_service.is_bot(command.room_id, command.bot_name):
                return CommandResult.fail(f"'{command.bot_name}' is not a bot")
            
            # Remove bot from bot service
            success = await self._bot_service.remove_bot(
                room_id=command.room_id,
                bot_name=command.bot_name
            )
            
            if success:
                # Remove bot from room
                await self._room_service.remove_player(
                    command.room_id,
                    command.bot_name,
                    reason="removed"
                )
                
                logger.info(f"Bot {command.bot_name} removed from room {command.room_id}")
                return CommandResult.ok(True)
            else:
                return CommandResult.fail("Failed to remove bot")
                
        except Exception as e:
            logger.error(f"Failed to remove bot: {str(e)}")
            return CommandResult.fail(str(e))


class ConfigureBotUseCase(CommandHandler[bool]):
    """Use case for configuring bot settings."""
    
    def __init__(
        self,
        room_service: RoomService,
        bot_service: BotService
    ):
        self._room_service = room_service
        self._bot_service = bot_service
    
    def can_handle(self, command) -> bool:
        return isinstance(command, ConfigureBotCommand)
    
    async def handle(self, command: ConfigureBotCommand) -> CommandResult[bool]:
        try:
            # Get room info
            room_info = await self._room_service.get_room_info(command.room_id)
            if not room_info:
                return CommandResult.fail("Room not found")
            
            # Verify player is the host
            if room_info.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can configure bots")
            
            # Check if it's actually a bot
            if not self._bot_service.is_bot(command.room_id, command.bot_name):
                return CommandResult.fail(f"'{command.bot_name}' is not a bot")
            
            # Configure bot
            success = await self._bot_service.configure_bot(
                room_id=command.room_id,
                bot_name=command.bot_name,
                difficulty=command.difficulty,
                play_speed=command.play_speed
            )
            
            if success:
                logger.info(f"Bot {command.bot_name} configured in room {command.room_id}")
                return CommandResult.ok(True)
            else:
                return CommandResult.fail("Failed to configure bot")
                
        except Exception as e:
            logger.error(f"Failed to configure bot: {str(e)}")
            return CommandResult.fail(str(e))