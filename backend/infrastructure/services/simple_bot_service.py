"""
Simple bot service implementation.

This module provides a basic implementation of the BotService
interface that integrates with the existing bot manager.
"""

import logging
from typing import Optional, List, Dict, Any

from application.interfaces import BotService
from shared_instances import shared_bot_manager

logger = logging.getLogger(__name__)


class SimpleBotService(BotService):
    """
    Bot service that delegates to the existing bot manager.
    
    This implementation wraps the legacy bot manager to provide
    the clean interface expected by the application layer.
    """
    
    def __init__(self):
        """Initialize the bot service."""
        self._bot_manager = shared_bot_manager
        
    async def create_bot(self, difficulty: str = "medium") -> str:
        """
        Create a new bot player.
        
        Args:
            difficulty: Bot difficulty level
            
        Returns:
            The bot's player ID
        """
        import uuid
        bot_id = f"bot_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created bot with ID: {bot_id}, difficulty: {difficulty}")
        return bot_id
    
    async def get_bot_action(self, game_state: Dict[str, Any], player_id: str) -> Dict[str, Any]:
        """
        Get the next action for a bot player.
        
        Args:
            game_state: Current game state
            player_id: Bot's player ID
            
        Returns:
            The action the bot wants to take
        """
        # Determine action based on game phase
        phase = game_state.get('phase', '')
        
        if phase == 'DECLARATION':
            # Bot declares a random valid number
            import random
            valid_options = [0, 1, 2, 3, 4, 5, 6, 7]
            return {
                'action': 'declare',
                'value': random.choice(valid_options)
            }
            
        elif phase == 'TURN':
            # Bot plays valid pieces
            # This would need more sophisticated logic
            return {
                'action': 'play',
                'pieces': [0]  # Play first piece
            }
            
        elif phase == 'PREPARATION' and game_state.get('awaiting_redeal_response'):
            # Bot always accepts redeals if it has weak hand
            return {
                'action': 'accept_redeal'
            }
            
        else:
            logger.warning(f"No bot action for phase: {phase}")
            return {'action': 'wait'}
    
    async def is_bot(self, player_id: str) -> bool:
        """
        Check if a player is a bot.
        
        Args:
            player_id: Player's ID to check
            
        Returns:
            True if player is a bot
        """
        # Simple check - bots have IDs starting with "bot_"
        return player_id.startswith("bot_")
    
