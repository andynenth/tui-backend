# backend/engine/state_machine/action_processor_di.py

import asyncio
import logging
from typing import Dict, Optional, TYPE_CHECKING

from ..dependency_injection.interfaces import IBotNotifier, IEventStore
from .core import GameAction

if TYPE_CHECKING:
    from .game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class ActionProcessor:
    """
    🎯 **ActionProcessor with Dependency Injection** - Phase 3 Circular Dependency Resolution
    
    Handles all action validation, execution, and bot notifications using dependency injection
    instead of direct imports to eliminate circular dependencies.
    
    Dependencies injected:
    - IBotNotifier: For bot notifications (replaces direct bot_manager import)
    - IEventStore: For event storage (replaces direct event store access)
    """
    
    def __init__(
        self, 
        state_machine: 'GameStateMachine',
        bot_notifier: IBotNotifier,
        event_store: IEventStore
    ):
        self.state_machine = state_machine
        self.bot_notifier = bot_notifier
        self.event_store = event_store
        
    async def validate_action(self, action: GameAction) -> Dict:
        """
        Validates if an action can be executed in the current state.
        
        Returns:
            dict: Validation result with 'valid' boolean and optional 'error'
        """
        logger.debug(f"🔍 ACTION_VALIDATION: Validating action {action.action_type} from {action.player_name}")
        
        # Check if state machine is running
        if not self.state_machine.is_running:
            logger.warning(f"❌ ACTION_VALIDATION: State machine not running")
            return {"valid": False, "error": "Game not running"}
        
        # Check if we have a current state
        if not self.state_machine.current_state:
            logger.warning(f"❌ ACTION_VALIDATION: No current state")
            return {"valid": False, "error": "No active game state"}
        
        # Delegate validation to current state
        try:
            validation_result = await self.state_machine.current_state.validate_action(action)
            logger.debug(f"✅ ACTION_VALIDATION: State validation result: {validation_result}")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ ACTION_VALIDATION: Error during validation: {str(e)}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def execute_action(self, action: GameAction) -> Dict:
        """
        Executes a pre-validated action.
        
        Args:
            action: The action to execute
            
        Returns:
            dict: Execution result
        """
        logger.info(f"⚙️ ACTION_EXECUTION: Executing {action.action_type} from {action.player_name}")
        
        if not self.state_machine.current_state:
            error_msg = "No active game state for execution"
            logger.error(f"❌ ACTION_EXECUTION: {error_msg}")
            return {"success": False, "error": error_msg}
        
        try:
            # Delegate execution to current state
            result = await self.state_machine.current_state.execute_action(action)
            logger.info(f"✅ ACTION_EXECUTION: Execution completed with result: {result}")
            
            # Notify bot manager of successful action
            if result.get("success", False):
                await self._notify_bot_action_accepted(action, result)
            else:
                await self._notify_bot_action_failed(action, result.get("error", "Unknown error"))
            
            return result
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            logger.error(f"❌ ACTION_EXECUTION: {error_msg}")
            
            # Notify bot manager of failed action
            await self._notify_bot_action_failed(action, error_msg)
            
            return {"success": False, "error": error_msg}
    
    async def handle_action(self, action: GameAction) -> Dict:
        """
        Complete action handling: validation + execution + notifications.
        
        This is the main entry point for all game actions.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"🎮 ACTION_HANDLER: Processing {action.action_type} from {action.player_name}")
        
        # Store the action attempt
        await self._store_event(
            "action_attempted", 
            {"action": action.action_type, "player": action.player_name, "payload": action.payload}
        )
        
        try:
            # Step 1: Validate the action
            validation_result = await self.validate_action(action)
            
            if not validation_result.get("valid", False):
                logger.warning(f"❌ ACTION_REJECTED: {action.action_type} - {validation_result.get('error', 'Unknown error')}")
                
                # Notify bot manager of rejection
                await self._notify_bot_action_rejected(action)
                
                # Store rejection event
                await self._store_event(
                    "action_rejected",
                    {
                        "action": action.action_type,
                        "player": action.player_name,
                        "reason": validation_result.get("error", "Unknown error"),
                        "payload": action.payload
                    }
                )
                
                return {
                    "success": False,
                    "error": validation_result.get("error", "Action not valid"),
                    "action_type": action.action_type,
                    "player": action.player_name
                }
            
            # Step 2: Execute the validated action
            execution_result = await self.execute_action(action)
            
            # Step 3: Store execution result
            if execution_result.get("success", False):
                await self._store_event(
                    "action_executed",
                    {
                        "action": action.action_type,
                        "player": action.player_name,
                        "result": execution_result,
                        "payload": action.payload
                    }
                )
            else:
                await self._store_event(
                    "action_failed",
                    {
                        "action": action.action_type,
                        "player": action.player_name,
                        "error": execution_result.get("error", "Unknown error"),
                        "payload": action.payload
                    }
                )
            
            # Performance logging
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"⏱️ ACTION_PERFORMANCE: {action.action_type} completed in {duration:.3f}s")
            
            return execution_result
            
        except Exception as e:
            error_msg = f"Action handling error: {str(e)}"
            logger.error(f"❌ ACTION_HANDLER: {error_msg}")
            
            # Store error event
            await self._store_event(
                "action_error",
                {
                    "action": action.action_type,
                    "player": action.player_name,
                    "error": error_msg,
                    "payload": action.payload
                }
            )
            
            return {"success": False, "error": error_msg}
    
    # === Bot Notification Methods (Using Dependency Injection) ===
    
    async def _notify_bot_action_rejected(self, action: GameAction):
        """Notify bot manager when an action is rejected."""
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                await self.bot_notifier.notify_action_result(
                    room_id=room_id,
                    action_type=action.action_type.value,
                    player_name=action.player_name,
                    success=False,
                    reason="Action rejected by game state"
                )
                logger.debug(f"🤖 BOT_NOTIFICATION: Notified bot manager of rejected action: {action.action_type}")
            else:
                logger.warning(f"⚠️ BOT_NOTIFICATION: No room_id available for bot notification")
                
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Error notifying bot manager of rejected action: {str(e)}")
    
    async def _notify_bot_action_accepted(self, action: GameAction, result: dict):
        """Notify bot manager when an action is accepted and executed."""
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                await self.bot_notifier.notify_action_result(
                    room_id=room_id,
                    action_type=action.action_type.value,
                    player_name=action.player_name,
                    success=True,
                    result=result
                )
                logger.debug(f"🤖 BOT_NOTIFICATION: Notified bot manager of accepted action: {action.action_type}")
            else:
                logger.warning(f"⚠️ BOT_NOTIFICATION: No room_id available for bot notification")
                
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Error notifying bot manager of accepted action: {str(e)}")
    
    async def _notify_bot_action_failed(self, action: GameAction, error_message: str):
        """Notify bot manager when an action execution fails."""
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                await self.bot_notifier.notify_action_result(
                    room_id=room_id,
                    action_type=action.action_type.value,
                    player_name=action.player_name,
                    success=False,
                    reason=error_message
                )
                logger.debug(f"🤖 BOT_NOTIFICATION: Notified bot manager of failed action: {action.action_type}")
            else:
                logger.warning(f"⚠️ BOT_NOTIFICATION: No room_id available for bot notification")
                
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Error notifying bot manager of failed action: {str(e)}")
    
    # === Event Storage Methods (Using Dependency Injection) ===
    
    async def _store_event(self, event_type: str, payload: dict):
        """Store game event using injected event store."""
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                event_data = {
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": asyncio.get_event_loop().time(),
                    "phase": self.state_machine.current_phase.name if self.state_machine.current_phase else None,
                    "round": getattr(self.state_machine.game, 'round_number', 0) if self.state_machine.game else 0
                }
                await self.event_store.store_event(room_id, event_data)
            else:
                logger.warning(f"⚠️ EVENT_STORAGE: No room_id available for event storage")
                
        except Exception as e:
            logger.error(f"❌ EVENT_STORAGE: Error storing event {event_type}: {str(e)}")