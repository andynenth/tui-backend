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
        
        print(f"🔧 EVENT_PROCESSOR_DEBUG: handle_event called for {event.trigger} from {event.player_name}")
        start_time = time.perf_counter()
        
        # 🚀 LOCK_SCOPE_FIX: Step 1 - Validation (no lock needed)
        print(f"🔧 EVENT_PROCESSOR_DEBUG: Step 1 - Validating event for current state (no lock)")
        if not self._validate_event_for_current_state(event):
            print(f"❌ EVENT_PROCESSOR_DEBUG: Event validation failed for {event.trigger}")
            return EventResult(
                success=False, 
                reason=f"Invalid event {event.trigger} for current state {self.state_machine.current_phase}"
            )
        print(f"✅ EVENT_PROCESSOR_DEBUG: Event validation passed")
        
        # 🚀 LOCK_SCOPE_FIX: Step 2 - Critical section only (minimal lock scope)
        print(f"🔧 EVENT_PROCESSOR_DEBUG: Step 2 - About to acquire processing_lock for critical section only")
        result = None
        try:
            async with asyncio.timeout(5.0):  # Reduced timeout since lock scope is minimal
                async with self.processing_lock:
                    print(f"🔧 EVENT_PROCESSOR_DEBUG: Processing_lock acquired for critical section")
                    try:
                        # Only atomic state processing under lock
                        print(f"🔧 EVENT_PROCESSOR_DEBUG: Processing event in current state")
                        result = await self._process_event_in_state(event)
                        print(f"✅ EVENT_PROCESSOR_DEBUG: _process_event_in_state completed: {result.success}")
                        
                        # 🚀 TRANSITION_LOCK_FIX: Only detect transition, don't execute under lock
                        print(f"🔧 EVENT_PROCESSOR_DEBUG: Checking transitions: {result.triggers_transition}")
                        if result.triggers_transition:
                            print(f"🔧 EVENT_PROCESSOR_DEBUG: Transition detected - will execute after lock release")
                        
                        print(f"🔧 EVENT_PROCESSOR_DEBUG: Critical section completed - releasing lock")
                        
                    except Exception as e:
                        print(f"❌ EVENT_PROCESSOR_DEBUG: Exception in critical section: {e}")
                        import traceback
                        traceback.print_exc()
                        logger.error(f"Event processing error: {e}", exc_info=True)
                        result = EventResult(
                            success=False,
                            reason=f"Processing error: {str(e)}"
                        )
                        
        except asyncio.TimeoutError:
            print(f"❌ EVENT_PROCESSOR_DEBUG: Timeout waiting for processing_lock after 5 seconds")
            logger.error(f"EventProcessor timeout for event {event.trigger} from {event.player_name}")
            return EventResult(
                success=False,
                reason="EventProcessor timeout - possible deadlock"
            )
        
        # 🚀 TRANSITION_LOCK_FIX: Step 2.5 - Handle transitions (lock-free)
        if result and result.triggers_transition:
            print(f"🔧 EVENT_PROCESSOR_DEBUG: Step 2.5 - Executing transition (lock-free)")
            try:
                print(f"🔧 EVENT_PROCESSOR_DEBUG: About to handle immediate transition (lock-free)")
                transition_success = await self._handle_immediate_transition(event, result)
                result.transition_completed = transition_success
                print(f"✅ EVENT_PROCESSOR_DEBUG: Transition completed (lock-free): {transition_success}")
            except Exception as e:
                print(f"❌ EVENT_PROCESSOR_DEBUG: Exception in transition execution: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"Transition execution error: {e}", exc_info=True)
                result.transition_completed = False
        
        # 🚀 LOCK_SCOPE_FIX: Step 3 - Non-critical operations (lock-free)
        print(f"🔧 EVENT_PROCESSOR_DEBUG: Step 3 - Lock-free operations (stats, history)")
        try:
            # Update processing statistics (non-critical, lock-free)
            print(f"🔧 EVENT_PROCESSOR_DEBUG: Updating stats (lock-free)")
            self._update_processing_stats(start_time)
            
            # Store event in history for debugging (non-critical, lock-free)
            print(f"🔧 EVENT_PROCESSOR_DEBUG: Storing event history (lock-free)")
            processing_time = time.perf_counter() - start_time
            self._store_event_history(event, result, processing_time)
            
            print(f"✅ EVENT_PROCESSOR_DEBUG: handle_event completed successfully")
            return result
            
        except Exception as e:
            print(f"⚠️ EVENT_PROCESSOR_DEBUG: Exception in non-critical operations: {e}")
            # Don't fail the entire event for non-critical operation failures
            logger.warning(f"Non-critical operation failed: {e}")
            return result  # Return the main result anyway
    
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
        
        print(f"🔧 PROCESS_EVENT_DEBUG: _process_event_in_state called for {event.trigger}")
        current_state = self.state_machine.current_state
        print(f"🔧 PROCESS_EVENT_DEBUG: Current state: {current_state}")
        
        # Check if state has event-driven processing
        print(f"🔧 PROCESS_EVENT_DEBUG: Checking if state has process_event method")
        if hasattr(current_state, 'process_event'):
            print(f"🔧 PROCESS_EVENT_DEBUG: Using state's process_event method")
            result = await current_state.process_event(event)
            print(f"✅ PROCESS_EVENT_DEBUG: State process_event completed: {result.success}")
            return result
        
        # Fallback: Convert event to action and use legacy processing
        print(f"🔧 PROCESS_EVENT_DEBUG: Using legacy action processing")
        result = await self._legacy_action_processing(event)
        print(f"✅ PROCESS_EVENT_DEBUG: Legacy action processing completed: {result.success}")
        return result
    
    async def _legacy_action_processing(self, event: GameEvent) -> EventResult:
        """Fallback processing for states not yet converted to event-driven"""
        
        print(f"🔧 LEGACY_ACTION_DEBUG: _legacy_action_processing called for {event.trigger}")
        
        # Convert event back to action for legacy processing
        from ..core import GameAction, ActionType
        
        try:
            print(f"🔧 LEGACY_ACTION_DEBUG: Converting event to action type")
            action_type = ActionType(event.trigger)
            print(f"🔧 LEGACY_ACTION_DEBUG: Action type: {action_type}")
            
            action = GameAction(
                action_type=action_type,
                player_name=event.player_name,
                payload=event.data
            )
            print(f"🔧 LEGACY_ACTION_DEBUG: GameAction created: {action}")
            
            # Process with legacy method
            print(f"🔧 LEGACY_ACTION_DEBUG: About to call state.handle_action")
            legacy_result = await self.state_machine.current_state.handle_action(action)
            print(f"✅ LEGACY_ACTION_DEBUG: state.handle_action completed: {legacy_result}")
            
            if legacy_result is None:
                print(f"❌ LEGACY_ACTION_DEBUG: Legacy action was rejected")
                return EventResult(success=False, reason="Legacy action rejected")
            
            # Check for immediate transitions by calling state's transition check
            print(f"🔧 LEGACY_ACTION_DEBUG: Checking transition conditions")
            next_phase = await self._check_immediate_transition_conditions()
            print(f"🔧 LEGACY_ACTION_DEBUG: Next phase: {next_phase}")
            
            if next_phase:
                print(f"✅ LEGACY_ACTION_DEBUG: Transition triggered to {next_phase}")
                return EventResult(
                    success=True,
                    triggers_transition=True,
                    target_state=next_phase,
                    transition_trigger="legacy_transition",
                    reason="Legacy state transition",
                    data=legacy_result
                )
            else:
                print(f"✅ LEGACY_ACTION_DEBUG: No transition, returning success")
                return EventResult(success=True, data=legacy_result)
                
        except ValueError as e:
            print(f"❌ LEGACY_ACTION_DEBUG: ValueError converting event trigger: {e}")
            logger.error(f"Cannot convert event trigger {event.trigger} to ActionType")
            return EventResult(success=False, reason="Invalid event trigger")
        except Exception as e:
            print(f"❌ LEGACY_ACTION_DEBUG: Exception in legacy action processing: {e}")
            import traceback
            traceback.print_exc()
            raise
    
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