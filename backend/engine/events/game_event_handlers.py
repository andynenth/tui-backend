# backend/engine/events/game_event_handlers.py

import asyncio
import logging
from typing import Dict, Set, Any, Optional, TYPE_CHECKING

from .event_types import (
    GameEvent, EventType, EventPriority,
    PhaseChangeEvent, ActionEvent, BroadcastEvent, 
    BotNotificationEvent, StateUpdateEvent, ErrorEvent
)
from .event_handlers import EventHandler, AsyncEventHandler

if TYPE_CHECKING:
    from ..state_machine.game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class PhaseChangeHandler(EventHandler):
    """
    🎯 **Phase Change Handler** - Handles game phase transitions
    
    Processes phase change events and coordinates state machine transitions.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__({
            EventType.PHASE_CHANGE_REQUESTED,
            EventType.PHASE_CHANGE_STARTED,
            EventType.PHASE_CHANGE_COMPLETED,
            EventType.PHASE_CHANGE_FAILED
        })
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle phase change events."""
        try:
            if event.event_type == EventType.PHASE_CHANGE_REQUESTED:
                await self._handle_phase_change_request(event)
            
            elif event.event_type == EventType.PHASE_CHANGE_STARTED:
                await self._handle_phase_change_start(event)
            
            elif event.event_type == EventType.PHASE_CHANGE_COMPLETED:
                await self._handle_phase_change_completion(event)
            
            elif event.event_type == EventType.PHASE_CHANGE_FAILED:
                await self._handle_phase_change_failure(event)
                
        except Exception as e:
            logger.error(f"❌ PHASE_HANDLER_ERROR: {str(e)}")
            event.add_error(f"Phase handler error: {str(e)}")
    
    async def _handle_phase_change_request(self, event: GameEvent):
        """Handle phase change request."""
        logger.info(f"📋 PHASE_REQUEST: Processing phase change request")
        
        # Extract phase change data
        phase_data = event.get_event_data()
        new_phase = phase_data.get('new_phase')
        reason = phase_data.get('reason', 'Event-driven transition')
        
        if new_phase and self.state_machine.phase_manager:
            # Validate and execute phase transition
            from ..state_machine.core import GamePhase
            try:
                target_phase = GamePhase[new_phase.upper()]
                success = await self.state_machine.phase_manager.trigger_immediate_transition(
                    event=event.event_type.value,
                    target_state=target_phase,
                    reason=reason
                )
                
                if success:
                    logger.info(f"✅ PHASE_TRANSITION: Successfully transitioned to {new_phase}")
                else:
                    logger.warning(f"⚠️ PHASE_TRANSITION: Failed to transition to {new_phase}")
                    
            except KeyError:
                logger.error(f"❌ INVALID_PHASE: Unknown phase {new_phase}")
                event.add_error(f"Invalid phase: {new_phase}")
    
    async def _handle_phase_change_start(self, event: GameEvent):
        """Handle phase change start."""
        logger.debug(f"🚀 PHASE_START: Phase change started")
        
        # Store phase change start event
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="phase_change_started",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_phase_change_completion(self, event: GameEvent):
        """Handle phase change completion."""
        logger.info(f"🎉 PHASE_COMPLETE: Phase change completed")
        
        # Update metrics and store completion event
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="phase_change_completed",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_phase_change_failure(self, event: GameEvent):
        """Handle phase change failure."""
        logger.error(f"❌ PHASE_FAILURE: Phase change failed")
        
        # Store failure event and attempt recovery
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="phase_change_failed",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


class ActionHandler(AsyncEventHandler):
    """
    🎯 **Action Handler** - Handles game actions and validation
    
    Processes player actions with async validation and execution.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__(
            supported_events={
                EventType.ACTION_RECEIVED,
                EventType.ACTION_VALIDATED,
                EventType.ACTION_EXECUTED,
                EventType.ACTION_REJECTED,
                EventType.ACTION_FAILED
            },
            max_concurrent=5
        )
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle action events."""
        try:
            if event.event_type == EventType.ACTION_RECEIVED:
                return await self._handle_action_received(event)
            
            elif event.event_type == EventType.ACTION_VALIDATED:
                return await self._handle_action_validated(event)
            
            elif event.event_type == EventType.ACTION_EXECUTED:
                return await self._handle_action_executed(event)
            
            elif event.event_type == EventType.ACTION_REJECTED:
                return await self._handle_action_rejected(event)
            
            elif event.event_type == EventType.ACTION_FAILED:
                return await self._handle_action_failed(event)
                
        except Exception as e:
            logger.error(f"❌ ACTION_HANDLER_ERROR: {str(e)}")
            event.add_error(f"Action handler error: {str(e)}")
    
    async def _handle_action_received(self, event: GameEvent) -> Dict[str, Any]:
        """Handle received action."""
        logger.debug(f"📨 ACTION_RECEIVED: Processing action")
        
        action_data = event.get_event_data()
        action_type = action_data.get('action_type')
        player_name = action_data.get('player_name')
        
        # Create game action and validate
        if self.state_machine.action_processor:
            from ..state_machine.core import GameAction, ActionType
            try:
                game_action = GameAction(
                    action_type=ActionType[action_type.upper()],
                    player_name=player_name,
                    payload=action_data.get('action_payload', {})
                )
                
                # Validate the action
                validation_result = await self.state_machine.action_processor.validate_action(game_action)
                
                return {
                    'action_validated': True,
                    'validation_result': validation_result,
                    'action_id': game_action.action_id
                }
                
            except (KeyError, ValueError) as e:
                logger.error(f"❌ INVALID_ACTION: {str(e)}")
                return {
                    'action_validated': False,
                    'error': f"Invalid action: {str(e)}"
                }
        
        return {'action_validated': False, 'error': 'Action processor not available'}
    
    async def _handle_action_validated(self, event: GameEvent):
        """Handle validated action."""
        logger.debug(f"✅ ACTION_VALIDATED: Action validation complete")
        
        # Store validation result
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="action_validated",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_action_executed(self, event: GameEvent):
        """Handle executed action."""
        logger.info(f"🎬 ACTION_EXECUTED: Action execution complete")
        
        # Store execution result
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="action_executed",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_action_rejected(self, event: GameEvent):
        """Handle rejected action."""
        logger.warning(f"❌ ACTION_REJECTED: Action was rejected")
        
        # Store rejection reason
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="action_rejected",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_action_failed(self, event: GameEvent):
        """Handle failed action."""
        logger.error(f"❌ ACTION_FAILED: Action execution failed")
        
        # Store failure details
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="action_failed",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


class BroadcastHandler(EventHandler):
    """
    🎯 **Broadcast Handler** - Handles WebSocket broadcasting events
    
    Processes broadcast events and coordinates message distribution.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__({
            EventType.BROADCAST_REQUESTED,
            EventType.BROADCAST_SENT,
            EventType.BROADCAST_FAILED
        })
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle broadcast events."""
        try:
            if event.event_type == EventType.BROADCAST_REQUESTED:
                await self._handle_broadcast_request(event)
            
            elif event.event_type == EventType.BROADCAST_SENT:
                await self._handle_broadcast_sent(event)
            
            elif event.event_type == EventType.BROADCAST_FAILED:
                await self._handle_broadcast_failed(event)
                
        except Exception as e:
            logger.error(f"❌ BROADCAST_HANDLER_ERROR: {str(e)}")
            event.add_error(f"Broadcast handler error: {str(e)}")
    
    async def _handle_broadcast_request(self, event: GameEvent):
        """Handle broadcast request."""
        logger.debug(f"📡 BROADCAST_REQUEST: Processing broadcast request")
        
        broadcast_data = event.get_event_data()
        broadcast_type = broadcast_data.get('broadcast_type')
        message_data = broadcast_data.get('message_data', {})
        
        # Execute broadcast through event broadcaster
        if self.state_machine.event_broadcaster:
            await self.state_machine.event_broadcaster.broadcast_event(
                event_type=broadcast_type,
                event_data=message_data
            )
    
    async def _handle_broadcast_sent(self, event: GameEvent):
        """Handle successful broadcast."""
        logger.debug(f"✅ BROADCAST_SENT: Broadcast sent successfully")
        
        # Record broadcast success
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="broadcast_sent",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_broadcast_failed(self, event: GameEvent):
        """Handle failed broadcast."""
        logger.error(f"❌ BROADCAST_FAILED: Broadcast failed")
        
        # Record broadcast failure
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="broadcast_failed",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


class BotNotificationHandler(EventHandler):
    """
    🎯 **Bot Notification Handler** - Handles bot communication events
    
    Processes bot notification events and coordinates AI interactions.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__({
            EventType.BOT_NOTIFICATION_SENT,
            EventType.BOT_ACTION_REQUEST,
            EventType.BOT_RESPONSE_RECEIVED
        })
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle bot notification events."""
        try:
            if event.event_type == EventType.BOT_NOTIFICATION_SENT:
                await self._handle_bot_notification_sent(event)
            
            elif event.event_type == EventType.BOT_ACTION_REQUEST:
                await self._handle_bot_action_request(event)
            
            elif event.event_type == EventType.BOT_RESPONSE_RECEIVED:
                await self._handle_bot_response_received(event)
                
        except Exception as e:
            logger.error(f"❌ BOT_HANDLER_ERROR: {str(e)}")
            event.add_error(f"Bot handler error: {str(e)}")
    
    async def _handle_bot_notification_sent(self, event: GameEvent):
        """Handle bot notification sent."""
        logger.debug(f"🤖 BOT_NOTIFICATION: Bot notification sent")
        
        # Record bot notification
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="bot_notification_sent",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_bot_action_request(self, event: GameEvent):
        """Handle bot action request."""
        logger.debug(f"🤖 BOT_ACTION_REQUEST: Bot action requested")
        
        # Process bot action request
        notification_data = event.get_event_data()
        bot_targets = notification_data.get('bot_targets', [])
        
        logger.info(f"🤖 BOT_REQUEST: Requesting action from {len(bot_targets)} bots")
    
    async def _handle_bot_response_received(self, event: GameEvent):
        """Handle bot response received."""
        logger.debug(f"🤖 BOT_RESPONSE: Bot response received")
        
        # Process bot response
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="bot_response_received",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


class StateUpdateHandler(EventHandler):
    """
    🎯 **State Update Handler** - Handles game state change events
    
    Processes state update events and maintains state consistency.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__({
            EventType.STATE_UPDATED,
            EventType.STATE_SAVED,
            EventType.STATE_LOADED,
            EventType.STATE_CORRUPTED
        })
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle state update events."""
        try:
            if event.event_type == EventType.STATE_UPDATED:
                await self._handle_state_updated(event)
            
            elif event.event_type == EventType.STATE_SAVED:
                await self._handle_state_saved(event)
            
            elif event.event_type == EventType.STATE_LOADED:
                await self._handle_state_loaded(event)
            
            elif event.event_type == EventType.STATE_CORRUPTED:
                await self._handle_state_corrupted(event)
                
        except Exception as e:
            logger.error(f"❌ STATE_HANDLER_ERROR: {str(e)}")
            event.add_error(f"State handler error: {str(e)}")
    
    async def _handle_state_updated(self, event: GameEvent):
        """Handle state updated."""
        logger.debug(f"📊 STATE_UPDATED: Game state updated")
        
        # Record state update
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="state_updated",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_state_saved(self, event: GameEvent):
        """Handle state saved."""
        logger.debug(f"💾 STATE_SAVED: Game state saved")
        
        # Record state save
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="state_saved",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_state_loaded(self, event: GameEvent):
        """Handle state loaded."""
        logger.info(f"📂 STATE_LOADED: Game state loaded")
        
        # Record state load
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="state_loaded",
                payload=event.get_event_data(),
                player_id=event.player_id
            )
    
    async def _handle_state_corrupted(self, event: GameEvent):
        """Handle state corrupted."""
        logger.error(f"💥 STATE_CORRUPTED: Game state corrupted")
        
        # Record state corruption and attempt recovery
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="state_corrupted",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


class ErrorHandler(EventHandler):
    """
    🎯 **Error Handler** - Handles error and warning events
    
    Processes error events and coordinates error recovery.
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        super().__init__({
            EventType.ERROR_OCCURRED,
            EventType.WARNING_ISSUED,
            EventType.RECOVERY_ATTEMPTED
        })
        self.state_machine = state_machine
        
    async def _handle_event(self, event: GameEvent) -> Any:
        """Handle error events."""
        try:
            if event.event_type == EventType.ERROR_OCCURRED:
                await self._handle_error_occurred(event)
            
            elif event.event_type == EventType.WARNING_ISSUED:
                await self._handle_warning_issued(event)
            
            elif event.event_type == EventType.RECOVERY_ATTEMPTED:
                await self._handle_recovery_attempted(event)
                
        except Exception as e:
            logger.error(f"❌ ERROR_HANDLER_ERROR: {str(e)}")
            # Don't add error to event to avoid infinite recursion
    
    async def _handle_error_occurred(self, event: GameEvent):
        """Handle error occurred."""
        error_data = event.get_event_data()
        error_type = error_data.get('error_type', 'Unknown')
        error_message = error_data.get('error_message', 'No message')
        
        logger.error(f"❌ ERROR_EVENT: {error_type} - {error_message}")
        
        # Record error
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="error_occurred",
                payload=error_data,
                player_id=event.player_id
            )
        
        # Attempt recovery if suggestions provided
        recovery_suggestions = error_data.get('recovery_suggestions', [])
        if recovery_suggestions:
            logger.info(f"🔧 RECOVERY_SUGGESTIONS: {recovery_suggestions}")
    
    async def _handle_warning_issued(self, event: GameEvent):
        """Handle warning issued."""
        warning_data = event.get_event_data()
        warning_message = warning_data.get('error_message', 'No message')
        
        logger.warning(f"⚠️ WARNING_EVENT: {warning_message}")
        
        # Record warning
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="warning_issued",
                payload=warning_data,
                player_id=event.player_id
            )
    
    async def _handle_recovery_attempted(self, event: GameEvent):
        """Handle recovery attempted."""
        logger.info(f"🔧 RECOVERY_ATTEMPTED: System recovery attempted")
        
        # Record recovery attempt
        if hasattr(self.state_machine, 'store_game_event'):
            await self.state_machine.store_game_event(
                event_type="recovery_attempted",
                payload=event.get_event_data(),
                player_id=event.player_id
            )


# Factory function to create all game handlers
def create_game_handlers(state_machine: 'GameStateMachine') -> Dict[str, EventHandler]:
    """
    Create all game event handlers for a state machine.
    
    Args:
        state_machine: The game state machine instance
        
    Returns:
        Dictionary of handler name to handler instance
    """
    handlers = {
        'phase_change': PhaseChangeHandler(state_machine),
        'action': ActionHandler(state_machine),
        'broadcast': BroadcastHandler(state_machine),
        'bot_notification': BotNotificationHandler(state_machine),
        'state_update': StateUpdateHandler(state_machine),
        'error': ErrorHandler(state_machine)
    }
    
    logger.info(f"🏭 HANDLERS_CREATED: Created {len(handlers)} game event handlers")
    return handlers