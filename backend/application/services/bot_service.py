# application/services/bot_service.py
"""
Bot service orchestrates bot-related operations.
"""

import logging
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime, timedelta

from domain.entities.player import Player
from domain.interfaces.bot_strategy import BotStrategy, BotStrategyFactory
from domain.interfaces.event_publisher import EventPublisher
from domain.events.player_events import BotAddedEvent, BotRemovedEvent
from domain.events.game_events import BotThinkingEvent, BotActionEvent

from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class BotInfo:
    """Value object for bot information."""
    def __init__(
        self,
        name: str,
        difficulty: str,
        play_speed: int = 2000,  # milliseconds
        is_thinking: bool = False
    ):
        self.name = name
        self.difficulty = difficulty
        self.play_speed = play_speed
        self.is_thinking = is_thinking


class BotService:
    """
    Application service for bot operations.
    
    This service orchestrates bot AI, timing, and notifications.
    """
    
    def __init__(
        self,
        bot_strategy_factory: BotStrategyFactory,
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._strategy_factory = bot_strategy_factory
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        self._active_bots: Dict[str, BotInfo] = {}
        self._bot_strategies: Dict[str, BotStrategy] = {}
    
    async def add_bot(
        self,
        room_id: str,
        bot_name: str,
        difficulty: str = "medium",
        play_speed: int = 2000
    ) -> BotInfo:
        """
        Add a bot to a room.
        
        Args:
            room_id: The room ID
            bot_name: Name for the bot
            difficulty: Bot difficulty level
            play_speed: Time in ms the bot takes to "think"
            
        Returns:
            BotInfo for the created bot
        """
        # Create bot info
        bot_info = BotInfo(
            name=bot_name,
            difficulty=difficulty,
            play_speed=play_speed
        )
        
        # Create strategy
        strategy = self._strategy_factory.create_strategy(difficulty)
        
        # Store bot
        bot_key = f"{room_id}:{bot_name}"
        self._active_bots[bot_key] = bot_info
        self._bot_strategies[bot_key] = strategy
        
        # Publish bot added event
        await self._event_publisher.publish(
            BotAddedEvent(
                room_id=room_id,
                bot_name=bot_name,
                difficulty=difficulty
            )
        )
        
        # Notify players
        await self._notification_service.notify_room(
            room_id,
            "bot_added",
            {
                "bot_name": bot_name,
                "difficulty": difficulty
            }
        )
        
        logger.info(
            f"Bot {bot_name} ({difficulty}) added to room {room_id}"
        )
        
        return bot_info
    
    async def remove_bot(
        self,
        room_id: str,
        bot_name: str
    ) -> bool:
        """
        Remove a bot from a room.
        
        Args:
            room_id: The room ID
            bot_name: Name of the bot to remove
            
        Returns:
            True if bot was removed
        """
        bot_key = f"{room_id}:{bot_name}"
        
        if bot_key not in self._active_bots:
            return False
        
        # Remove bot
        del self._active_bots[bot_key]
        del self._bot_strategies[bot_key]
        
        # Publish bot removed event
        await self._event_publisher.publish(
            BotRemovedEvent(
                room_id=room_id,
                bot_name=bot_name
            )
        )
        
        # Notify players
        await self._notification_service.notify_room(
            room_id,
            "bot_removed",
            {
                "bot_name": bot_name
            }
        )
        
        logger.info(f"Bot {bot_name} removed from room {room_id}")
        
        return True
    
    async def get_bot_declaration(
        self,
        room_id: str,
        bot_name: str,
        game_state,
        previous_declarations: List[int],
        position_in_order: int
    ) -> int:
        """
        Get bot's declaration decision.
        
        Returns:
            Declaration value (0-8)
        """
        bot_key = f"{room_id}:{bot_name}"
        
        if bot_key not in self._bot_strategies:
            raise ValueError(f"Bot {bot_name} not found")
        
        bot_info = self._active_bots[bot_key]
        strategy = self._bot_strategies[bot_key]
        
        # Start thinking
        bot_info.is_thinking = True
        await self._event_publisher.publish(
            BotThinkingEvent(
                room_id=room_id,
                bot_name=bot_name,
                action_type="declare"
            )
        )
        
        # Notify players bot is thinking
        await self._notification_service.notify_room(
            room_id,
            "bot_thinking",
            {
                "bot_name": bot_name,
                "action": "declare"
            }
        )
        
        # Simulate thinking time
        await asyncio.sleep(bot_info.play_speed / 1000.0)
        
        # Get bot decision
        bot_player = Player(bot_name)  # Create temporary player object
        decision = await strategy.make_declaration(
            bot_player,
            game_state,
            previous_declarations,
            position_in_order
        )
        
        # Stop thinking
        bot_info.is_thinking = False
        
        # Publish bot action event
        await self._event_publisher.publish(
            BotActionEvent(
                room_id=room_id,
                bot_name=bot_name,
                action_type="declare",
                action_value=decision.value,
                confidence=decision.confidence
            )
        )
        
        logger.info(
            f"Bot {bot_name} declared {decision.value} "
            f"(confidence: {decision.confidence:.2f})"
        )
        
        return decision.value
    
    async def get_bot_play(
        self,
        room_id: str,
        bot_name: str,
        game_state,
        current_turn_plays: List[tuple[str, List]],
        required_piece_count: Optional[int]
    ) -> List[int]:
        """
        Get bot's play decision.
        
        Returns:
            List of piece indices to play
        """
        bot_key = f"{room_id}:{bot_name}"
        
        if bot_key not in self._bot_strategies:
            raise ValueError(f"Bot {bot_name} not found")
        
        bot_info = self._active_bots[bot_key]
        strategy = self._bot_strategies[bot_key]
        
        # Start thinking
        bot_info.is_thinking = True
        await self._event_publisher.publish(
            BotThinkingEvent(
                room_id=room_id,
                bot_name=bot_name,
                action_type="play"
            )
        )
        
        # Notify players bot is thinking
        await self._notification_service.notify_room(
            room_id,
            "bot_thinking",
            {
                "bot_name": bot_name,
                "action": "play"
            }
        )
        
        # Simulate thinking time
        await asyncio.sleep(bot_info.play_speed / 1000.0)
        
        # Get bot decision
        bot_player = Player(bot_name)  # Create temporary player object
        decision = await strategy.choose_play(
            bot_player,
            game_state,
            current_turn_plays,
            required_piece_count
        )
        
        # Stop thinking
        bot_info.is_thinking = False
        
        # Convert pieces to indices
        piece_indices = decision.value  # Assuming strategy returns indices
        
        # Publish bot action event
        await self._event_publisher.publish(
            BotActionEvent(
                room_id=room_id,
                bot_name=bot_name,
                action_type="play",
                action_value=piece_indices,
                confidence=decision.confidence
            )
        )
        
        logger.info(
            f"Bot {bot_name} played pieces {piece_indices} "
            f"(confidence: {decision.confidence:.2f})"
        )
        
        return piece_indices
    
    async def configure_bot(
        self,
        room_id: str,
        bot_name: str,
        difficulty: Optional[str] = None,
        play_speed: Optional[int] = None
    ) -> bool:
        """
        Configure bot settings.
        
        Args:
            room_id: The room ID
            bot_name: Name of the bot
            difficulty: New difficulty level
            play_speed: New play speed in ms
            
        Returns:
            True if bot was configured
        """
        bot_key = f"{room_id}:{bot_name}"
        
        if bot_key not in self._active_bots:
            return False
        
        bot_info = self._active_bots[bot_key]
        
        # Update difficulty if provided
        if difficulty and difficulty != bot_info.difficulty:
            bot_info.difficulty = difficulty
            # Create new strategy
            self._bot_strategies[bot_key] = self._strategy_factory.create_strategy(
                difficulty
            )
        
        # Update play speed if provided
        if play_speed is not None:
            bot_info.play_speed = max(500, min(10000, play_speed))  # 0.5-10 seconds
        
        # Notify players
        await self._notification_service.notify_room(
            room_id,
            "bot_configured",
            {
                "bot_name": bot_name,
                "difficulty": bot_info.difficulty,
                "play_speed": bot_info.play_speed
            }
        )
        
        return True
    
    def get_room_bots(self, room_id: str) -> List[BotInfo]:
        """Get all bots in a room."""
        bots = []
        for key, bot_info in self._active_bots.items():
            if key.startswith(f"{room_id}:"):
                bots.append(bot_info)
        return bots
    
    def is_bot(self, room_id: str, player_name: str) -> bool:
        """Check if a player is a bot."""
        bot_key = f"{room_id}:{player_name}"
        return bot_key in self._active_bots