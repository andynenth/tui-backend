# backend/engine/state_machine/events/event_processor.py

"""
EventProcessor - Core event-driven processing engine

This class replaces the polling-based _process_loop with immediate event processing.
All events are processed immediately without polling delays.
"""

import asyncio
import logging
import time
from typing import Dict, Set, Optional

from .event_types import GameEvent, EventResult, is_logic_event, is_display_event
from ..core import GamePhase


logger = logging.getLogger(__name__)


class EventProcessor:
    """Central event processing engine - replaces polling loop"""
    
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.processing_lock = asyncio.Lock()
        self.event_history = []
        self.processing_stats = {
            "events_processed": 0,
            "avg_processing_time": 0.0,
            "last_event_time": 0.0
        }
    
    async def handle_event(self, event: GameEvent) -> EventResult:
        """Process single event immediately - NO POLLING"""
        
        start_time = time.perf_counter()
        
        # Serialize event processing to prevent race conditions
        async with self.processing_lock:
            try:
                # 1. Validate event against current state
                if not self._validate_event_for_current_state(event):
                    return EventResult(
                        success=False, 
                        reason=f"Invalid event {event.trigger} for current state {self.state_machine.current_phase}"
                    )
                
                # 2. Process event in current state immediately
                result = await self._process_event_in_state(event)
                
                # 3. Handle immediate transitions if triggered
                if result.triggers_transition:
                    transition_success = await self._handle_immediate_transition(event, result)
                    result.transition_completed = transition_success
                
                # 4. Update processing statistics
                self._update_processing_stats(start_time)
                
                # 5. Store event in history for debugging
                self._store_event_history(event, result, time.perf_counter() - start_time)
                
                return result
                
            except Exception as e:
                logger.error(f"Event processing error: {e}", exc_info=True)
                return EventResult(
                    success=False,
                    reason=f"Processing error: {str(e)}"
                )
    
    def _validate_event_for_current_state(self, event: GameEvent) -> bool:
        """Validate event is allowed in current state"""
        
        if not self.state_machine.current_state:
            logger.warning("No current state for event validation")
            return False
        
        # Get valid events for current state
        valid_events = self._get_valid_events_for_state(self.state_machine.current_state)
        
        # Check if event trigger is valid
        if event.trigger not in valid_events:
            logger.debug(f"Event {event.trigger} not valid for state {self.state_machine.current_phase}")
            return False
        
        # Additional validation for user events
        if event.event_type == "user":
            return self._validate_user_event(event)
        
        return True
    
    def _get_valid_events_for_state(self, state) -> Set[str]:
        """Get set of valid event triggers for state"""
        
        # Map allowed actions to event triggers
        valid_events = set()
        
        # Add action-based events
        for action_type in state.allowed_actions:
            valid_events.add(action_type.value)
        
        # Add state-specific system events
        if hasattr(state, 'get_valid_system_events'):
            valid_events.update(state.get_valid_system_events())
        else:
            # Default system events for all states
            valid_events.update([
                "turn_complete",
                "round_complete", 
                "all_declared",
                "scores_calculated",
                "game_complete"
            ])
        
        return valid_events
    
    def _validate_user_event(self, event: GameEvent) -> bool:
        """Additional validation for user events"""
        
        # Check if player exists in game
        if event.player_name and hasattr(self.state_machine, 'game'):
            game = self.state_machine.game
            if hasattr(game, 'players'):
                player_names = [p.name for p in game.players]
                if event.player_name not in player_names:
                    logger.warning(f"Unknown player: {event.player_name}")
                    return False
        
        return True
    
    async def _process_event_in_state(self, event: GameEvent) -> EventResult:
        """Process event in current state"""
        
        current_state = self.state_machine.current_state
        
        # Check if state has event-driven processing
        if hasattr(current_state, 'process_event'):
            return await current_state.process_event(event)
        
        # Fallback: Convert event to action and use legacy processing
        return await self._legacy_action_processing(event)
    
    async def _legacy_action_processing(self, event: GameEvent) -> EventResult:
        """Fallback processing for states not yet converted to event-driven"""
        
        # Convert event back to action for legacy processing
        from ..core import GameAction, ActionType
        
        try:
            action_type = ActionType(event.trigger)
            action = GameAction(
                action_type=action_type,
                player_name=event.player_name,
                payload=event.data
            )
            
            # Process with legacy method
            legacy_result = await self.state_machine.current_state.handle_action(action)
            
            if legacy_result is None:
                return EventResult(success=False, reason="Legacy action rejected")
            
            # Check for immediate transitions by calling state's transition check
            next_phase = await self._check_immediate_transition_conditions()
            
            if next_phase:
                return EventResult(
                    success=True,
                    triggers_transition=True,
                    target_state=next_phase,
                    transition_trigger="legacy_transition",
                    reason="Legacy state transition",
                    data=legacy_result
                )
            else:
                return EventResult(success=True, data=legacy_result)
                
        except ValueError:
            logger.error(f"Cannot convert event trigger {event.trigger} to ActionType")
            return EventResult(success=False, reason="Invalid event trigger")
    
    async def _check_immediate_transition_conditions(self) -> Optional[GamePhase]:
        """Check transition conditions immediately (replaces polling)"""
        
        if not self.state_machine.current_state:
            return None
        
        # Use existing transition checking (will be replaced in Phase 3.2)
        return await self.state_machine.current_state.check_transition_conditions()
    
    async def _handle_immediate_transition(self, event: GameEvent, result: EventResult) -> bool:
        """Handle immediate state transition"""
        
        if not result.target_state:
            logger.error("Transition requested but no target state specified")
            return False
        
        try:
            # Perform immediate transition
            await self.state_machine._immediate_transition_to(
                result.target_state,
                result.reason or f"Event {event.trigger} triggered transition"
            )
            
            logger.info(f"Immediate transition: {self.state_machine.current_phase} triggered by {event.trigger}")
            return True
            
        except Exception as e:
            logger.error(f"Transition failed: {e}", exc_info=True)
            return False
    
    def _update_processing_stats(self, start_time: float):
        """Update event processing statistics"""
        
        processing_time = time.perf_counter() - start_time
        
        self.processing_stats["events_processed"] += 1
        self.processing_stats["last_event_time"] = processing_time
        
        # Update rolling average
        current_avg = self.processing_stats["avg_processing_time"]
        event_count = self.processing_stats["events_processed"]
        
        self.processing_stats["avg_processing_time"] = (
            (current_avg * (event_count - 1) + processing_time) / event_count
        )
    
    def _store_event_history(self, event: GameEvent, result: EventResult, processing_time: float):
        """Store event in history for debugging"""
        
        history_entry = {
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "trigger": event.trigger,
            "player": event.player_name,
            "success": result.success,
            "triggered_transition": result.triggers_transition,
            "target_state": result.target_state.value if result.target_state else None,
            "processing_time": processing_time,
            "phase": self.state_machine.current_phase.value if self.state_machine.current_phase else None
        }
        
        self.event_history.append(history_entry)
        
        # Keep only last 100 events
        if len(self.event_history) > 100:
            self.event_history.pop(0)
    
    def get_processing_stats(self) -> Dict:
        """Get event processing statistics"""
        return self.processing_stats.copy()
    
    def get_recent_events(self, limit: int = 10) -> list:
        """Get recent event history"""
        return self.event_history[-limit:] if self.event_history else []