# backend/engine/state_machine/game_state_machine.py

import asyncio
import logging
import time
from typing import Dict, Optional, List, Set
from datetime import datetime

from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .base_state import GameState
from .states import PreparationState, DeclarationState, TurnState, ScoringState


logger = logging.getLogger(__name__)


class GameStateMachine:
    """
    Central coordinator for game state management.
    Manages phase transitions and delegates action handling to appropriate states.
    """
    
    def __init__(self, game, broadcast_callback=None):
        self.game = game
        # Pass room_id to ActionQueue for event storage
        room_id = getattr(game, 'room_id', None) if game else None
        self.action_queue = ActionQueue(room_id=room_id)
        self.current_state: Optional[GameState] = None
        self.current_phase: Optional[GamePhase] = None
        self.is_running = False
        self.broadcast_callback = broadcast_callback  # For WebSocket broadcasting
        
        # 🚀 EVENT-DRIVEN ARCHITECTURE: Replace polling with immediate processing
        from .events import EventProcessor
        self.event_processor = EventProcessor(self)
        self.transition_lock = asyncio.Lock()  # Prevent race conditions
        self.active_tasks = set()              # Managed task lifecycle
        
        # Legacy support during transition
        self._process_task: Optional[asyncio.Task] = None  # Will be removed
        
        # Initialize all available states
        self.states: Dict[GamePhase, GameState] = {
            GamePhase.PREPARATION: PreparationState(self),
            GamePhase.DECLARATION: DeclarationState(self),
            GamePhase.TURN: TurnState(self), 
            GamePhase.SCORING: ScoringState(self), 
        }
        
        # Transition validation map
        self._valid_transitions = {
            GamePhase.PREPARATION: {GamePhase.DECLARATION},
            GamePhase.DECLARATION: {GamePhase.TURN},
            GamePhase.TURN: {GamePhase.SCORING},
            GamePhase.SCORING: {GamePhase.PREPARATION}  # Next round
        }
    
    async def start(self, initial_phase: GamePhase = GamePhase.PREPARATION):
        """Start the event-driven state machine"""
        if self.is_running:
            logger.warning("State machine already running")
            return
        
        logger.info(f"🚀 Starting EVENT-DRIVEN state machine in {initial_phase} phase")
        self.is_running = True
        
        # 🚀 EVENT-DRIVEN: No more background polling task
        # Actions are processed immediately when received
        
        # Enter initial phase
        await self._immediate_transition_to(initial_phase, "Initial state machine start")
    
    async def stop(self):
        """Stop the event-driven state machine"""
        logger.info("🛑 Stopping EVENT-DRIVEN state machine")
        self.is_running = False
        
        # 🚀 EVENT-DRIVEN: Clean up managed async tasks
        await self.cleanup_all_tasks()
        
        # Cancel legacy processing task if still exists
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()
    
    async def handle_action(self, action: GameAction) -> Dict:
        """
        🚀 EVENT-DRIVEN: Process action immediately - NO QUEUING, NO POLLING
        """
        print(f"🔧 HANDLE_ACTION_DEBUG: handle_action called for {action.player_name} {action.action_type.value}")
        
        try:
            print(f"🔧 HANDLE_ACTION_DEBUG: State machine running check: {self.is_running}")
            if not self.is_running:
                print(f"🔧 HANDLE_ACTION_DEBUG: State machine not running - returning error")
                return {"success": False, "error": "State machine not running"}
            
            # Convert action to event and process immediately
            print(f"🔧 HANDLE_ACTION_DEBUG: Converting action to event")
            from .events.event_types import GameEvent
            
            print(f"🔧 HANDLE_ACTION_DEBUG: Creating GameEvent from action")
            event = GameEvent.from_action(action, immediate=True)
            print(f"🔧 HANDLE_ACTION_DEBUG: GameEvent created successfully")
            
            # Process immediately - NO POLLING DELAYS
            print(f"🔧 HANDLE_ACTION_DEBUG: About to call event_processor.handle_event")
            start_time = time.time()
            result = await self.event_processor.handle_event(event)
            processing_time = time.time() - start_time
            print(f"🔧 HANDLE_ACTION_DEBUG: event_processor.handle_event completed in {processing_time:.3f}s")
            
            print(f"🔧 HANDLE_ACTION_DEBUG: Processing result")
            logger.info(f"🚀 EVENT-DRIVEN: Processed {action.action_type.value} from {action.player_name} in {processing_time:.3f}s")
            
            final_result = {
                "success": result.success,
                "immediate": True,
                "transition": result.triggers_transition,
                "processing_time": processing_time,
                "reason": result.reason,
                "data": result.data
            }
            
            print(f"✅ HANDLE_ACTION_DEBUG: handle_action returning result: {final_result}")
            return final_result
            
        except Exception as e:
            print(f"❌ HANDLE_ACTION_DEBUG: Exception in handle_action: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error result
            error_result = {
                "success": False,
                "error": str(e),
                "immediate": True,
                "processing_time": 0,
                "reason": f"Exception during action processing: {e}",
                "data": {}
            }
            print(f"❌ HANDLE_ACTION_DEBUG: Returning error result: {error_result}")
            return error_result
    
    # 🚀 EVENT-DRIVEN ARCHITECTURE: Async Task Lifecycle Management
    
    async def create_managed_task(self, coro, task_name: str) -> asyncio.Task:
        """Create task with proper lifecycle management"""
        task = asyncio.create_task(coro, name=task_name)
        self.active_tasks.add(task)
        
        # Auto-cleanup when task completes
        task.add_done_callback(lambda t: self.active_tasks.discard(t))
        return task
    
    async def cleanup_all_tasks(self):
        """Clean up all active tasks during state transitions"""
        if self.active_tasks:
            logger.info(f"🧹 Cleaning up {len(self.active_tasks)} active tasks")
            
            # Cancel all active tasks
            for task in self.active_tasks.copy():
                if not task.done():
                    task.cancel()
            
            # Wait for cancellation to complete
            if self.active_tasks:
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
            
            self.active_tasks.clear()
    
    # 🚀 EVENT-DRIVEN: Immediate state transitions replace polling
    
    async def trigger_immediate_transition(self, event, target_state: GamePhase, reason: str) -> bool:
        """Immediate state transition based on event - NO POLLING"""
        async with self.transition_lock:  # Prevent concurrent transitions
            
            # Validate transition
            if not self._validate_transition_for_event(target_state):
                logger.warning(f"Invalid transition to {target_state} from {self.current_phase}")
                return False
            
            # Immediate transition - NO DELAYS
            await self._immediate_transition_to(target_state, reason)
            return True
    
    def _validate_transition_for_event(self, target_state: GamePhase) -> bool:
        """Validate transition is allowed"""
        if not self.current_phase:
            return True  # Initial transition
        
        return target_state in self._valid_transitions.get(self.current_phase, set())
    
    async def _immediate_transition_to(self, new_phase: GamePhase, reason: str):
        """🚀 EVENT-DRIVEN: Immediate atomic state transition with proper cleanup"""
        
        print(f"🔧 TRANSITION_DEBUG: _immediate_transition_to called: {self.current_phase} -> {new_phase}")
        logger.info(f"🚀 EVENT-DRIVEN transition: {self.current_phase} -> {new_phase} ({reason})")
        
        # Debug async context
        import threading
        print(f"🔧 ASYNC_DEBUG: Thread: {threading.current_thread().name}")
        print(f"🔧 ASYNC_DEBUG: Is running: {self.is_running}")
        print(f"🔧 ASYNC_DEBUG: Transition lock acquired: {self.transition_lock.locked()}")
        
        try:
            # Validate transition (skip validation for initial transition)
            if self.current_phase and new_phase not in self._valid_transitions.get(self.current_phase, set()):
                print(f"❌ TRANSITION_DEBUG: Invalid transition rejected: {self.current_phase} -> {new_phase}")
                logger.error(f"❌ Invalid transition: {self.current_phase} -> {new_phase}")
                return
            
            # Get new state
            new_state = self.states.get(new_phase)
            if not new_state:
                print(f"❌ TRANSITION_DEBUG: No state handler for phase: {new_phase}")
                logger.error(f"❌ No state handler for phase: {new_phase}")
                return
            
            print(f"🔧 TRANSITION_DEBUG: Starting transition steps...")
            
            # 1. Cleanup current state tasks (prevent resource leaks)
            print(f"🔧 TRANSITION_DEBUG: Step 1 - Cleanup tasks")
            await self.cleanup_all_tasks()
            
            # 2. Exit current state
            print(f"🔧 TRANSITION_DEBUG: Step 2 - Exit current state")
            if self.current_state:
                logger.debug(f"🚪 Exiting current state: {self.current_state.__class__.__name__}")
                await self.current_state.on_exit()
            
            # 3. Atomic state update
            print(f"🔧 TRANSITION_DEBUG: Step 3 - Atomic state update")
            old_phase = self.current_phase
            self.current_phase = new_phase
            self.current_state = new_state
            
            # 4. Enter new state
            print(f"🔧 TRANSITION_DEBUG: Step 4 - Enter new state")
            logger.debug(f"🎯 Entering new state: {self.current_state.__class__.__name__}")
            print(f"🔧 TRANSITION_DEBUG: Step 4a - About to call on_enter() for {new_phase.value}")
            await self.current_state.on_enter()
            print(f"🔧 TRANSITION_DEBUG: Step 4b - on_enter() completed for {new_phase.value}")
            
            print(f"🔧 TRANSITION_DEBUG: Step 4c - Checking current state after on_enter()")
            print(f"🔧 TRANSITION_DEBUG: Current phase: {self.current_phase}")
            print(f"🔧 TRANSITION_DEBUG: Current state: {self.current_state}")
            print(f"🔧 TRANSITION_DEBUG: Is running: {self.is_running}")
            
            # 5. Store event for replay capability
            print(f"🔧 TRANSITION_DEBUG: Step 5 - About to store event")
            try:
                await self._store_phase_change_event(old_phase, new_phase)
                print(f"🔧 TRANSITION_DEBUG: Step 5 - Store event completed")
            except Exception as e:
                print(f"❌ TRANSITION_DEBUG: Step 5 failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # 6. Broadcast change with immediate frontend instructions
            print(f"🔧 TRANSITION_DEBUG: Step 6 - About to broadcast")
            print(f"🚀 STATE_MACHINE_DEBUG: Broadcasting phase change to {new_phase.value} with reason: {reason}")
            try:
                await self._broadcast_phase_change_with_display_metadata(new_phase, reason)
                print(f"✅ STATE_MACHINE_DEBUG: Phase change broadcast completed for {new_phase.value}")
            except Exception as e:
                print(f"❌ TRANSITION_DEBUG: Step 6 failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # 7. Trigger bot manager for phase changes
            print(f"🔧 TRANSITION_DEBUG: Step 7 - About to notify bot manager")
            try:
                await self._notify_bot_manager(new_phase)
                print(f"🔧 TRANSITION_DEBUG: Step 7 - Bot manager notification completed")
            except Exception as e:
                print(f"❌ TRANSITION_DEBUG: Step 7 failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            print(f"✅ TRANSITION_DEBUG: All transition steps completed successfully: {old_phase} -> {new_phase}")
            
        except Exception as e:
            print(f"❌ TRANSITION_DEBUG: Exception in _immediate_transition_to: {e}")
            logger.error(f"❌ Transition failed with exception: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
    
    def get_current_phase(self) -> Optional[GamePhase]:
        """Get current game phase"""
        return self.current_phase
    
    def get_allowed_actions(self) -> Set[ActionType]:
        """Get currently allowed action types"""
        if not self.current_state:
            return set()
        return self.current_state.allowed_actions
    
    def get_phase_data(self) -> Dict:
        """Get current phase-specific data (JSON serializable)"""
        if not self.current_state:
            return {}
        
        # Get raw phase data
        raw_data = self.current_state.phase_data.copy()
        
        # Convert Player objects to serializable format
        serializable_data = {}
        for key, value in raw_data.items():
            if key == 'declaration_order' and isinstance(value, list):
                # Convert Player objects to player names
                serializable_data[key] = [
                    getattr(player, 'name', str(player)) for player in value
                ]
            elif hasattr(value, '__dict__'):
                # Convert complex objects to string representation
                serializable_data[key] = str(value)
            else:
                serializable_data[key] = value
        
        return serializable_data
    
    async def _broadcast_phase_change_with_hands(self, phase: GamePhase):
        """Broadcast phase change with all player hand data"""
        base_data = {
            "phase": phase.value,
            "allowed_actions": [action.value for action in self.get_allowed_actions()],
            "phase_data": self.get_phase_data()
        }
        
        # Add player hands to the data
        if hasattr(self, 'game') and self.game and hasattr(self.game, 'players'):
            players_data = {}
            for player in self.game.players:
                player_name = getattr(player, 'name', str(player))
                player_hand = []
                
                # Get player's hand
                if hasattr(player, 'hand') and player.hand:
                    player_hand = [str(piece) for piece in player.hand]
                
                players_data[player_name] = {
                    'hand': player_hand,
                    'hand_size': len(player_hand)
                }
            
            base_data['players'] = players_data
        
        # Send to all players
        await self.broadcast_event("phase_change", base_data)
    
    async def _broadcast_phase_change_with_display_metadata(self, phase: GamePhase, reason: str):
        """🚀 EVENT-DRIVEN: Broadcast phase change with frontend display instructions"""
        
        print(f"🔧 BROADCAST_DEBUG: _broadcast_phase_change_with_display_metadata called for {phase.value}")
        
        try:
            base_data = {
                "phase": phase.value,
                "allowed_actions": [action.value for action in self.get_allowed_actions()],
                "phase_data": self.get_phase_data(),
                "immediate": True,
                "reason": reason
            }
            print(f"🔧 BROADCAST_DEBUG: Prepared base_data: {base_data}")
            
            # 🚀 MANDATORY: Add frontend display instructions (NO backend timing)
            display_config = self._get_display_config_for_phase(phase)
            if display_config:
                base_data["display"] = display_config
                print(f"🔧 BROADCAST_DEBUG: Added display config: {display_config}")
            
            # Add player hands to the data
            if hasattr(self, 'game') and self.game and hasattr(self.game, 'players'):
                players_data = {}
                for player in self.game.players:
                    player_name = getattr(player, 'name', str(player))
                    player_hand = []
                    
                    # Get player's hand
                    if hasattr(player, 'hand') and player.hand:
                        player_hand = [str(piece) for piece in player.hand]
                    
                    players_data[player_name] = {
                        'hand': player_hand,
                        'hand_size': len(player_hand)
                    }
                
                base_data['players'] = players_data
                print(f"🔧 BROADCAST_DEBUG: Added players data: {list(players_data.keys())}")
            
            # Send immediate update to all players
            print(f"🔧 BROADCAST_DEBUG: About to call broadcast_event with phase_change")
            await self.broadcast_event("phase_change", base_data)
            print(f"🔧 BROADCAST_DEBUG: broadcast_event completed successfully")
            
        except Exception as e:
            print(f"❌ BROADCAST_DEBUG: Exception in _broadcast_phase_change_with_display_metadata: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_display_config_for_phase(self, phase: GamePhase) -> Optional[Dict]:
        """Get frontend display configuration for phase"""
        
        # 🚀 MANDATORY: Frontend display timing only - NO backend delays
        display_configs = {
            GamePhase.TURN: {
                "type": "turn_active",
                "show_for_seconds": None,  # No auto-advance for active phases
                "auto_advance": False,
                "can_skip": False
            },
            GamePhase.PREPARATION: {
                "type": "preparation", 
                "show_for_seconds": None,
                "auto_advance": False,
                "can_skip": False
            },
            GamePhase.DECLARATION: {
                "type": "declaration",
                "show_for_seconds": None,
                "auto_advance": False, 
                "can_skip": False
            },
            GamePhase.SCORING: {
                "type": "scoring",
                "show_for_seconds": None,
                "auto_advance": False,
                "can_skip": False
            }
        }
        
        return display_configs.get(phase)
    
    async def broadcast_turn_completion(self, turn_data: Dict):
        """🚀 MANDATORY: Broadcast turn completion with frontend display delegation"""
        
        # Determine next phase based on game state
        next_phase = GamePhase.SCORING if self._all_hands_empty() else GamePhase.TURN
        
        event_data = {
            "winner": turn_data.get("winner"),
            "pieces_transferred": turn_data.get("pieces_transferred", 0),
            "turn_results": turn_data.get("turn_results", {}),
            
            # 🚀 MANDATORY: Frontend display instructions (NO backend delays)
            "display": {
                "type": "turn_results",
                "show_for_seconds": 7.0,
                "auto_advance": True,
                "can_skip": True,
                "next_phase": next_phase.value
            },
            
            # Logic state
            "logic_complete": True,
            "immediate": True
        }
        
        await self.broadcast_event("turn_completed", event_data)
    
    async def broadcast_scoring_completion(self, scores: Dict):
        """🚀 MANDATORY: Broadcast scoring completion with frontend display delegation"""
        
        # Determine next phase
        game_complete = scores.get("game_complete", False)
        next_phase = "game_end" if game_complete else GamePhase.PREPARATION.value
        
        event_data = {
            "scores": scores.get("final_scores", {}),
            "round_number": scores.get("round_number", 0),
            "game_complete": game_complete,
            
            # 🚀 MANDATORY: Frontend display instructions (NO backend timing)
            "display": {
                "type": "scoring_display",
                "show_for_seconds": 7.0,
                "auto_advance": True,
                "can_skip": True,
                "next_phase": next_phase
            },
            
            "logic_complete": True,
            "immediate": True
        }
        
        await self.broadcast_event("scoring_completed", event_data)
    
    def _all_hands_empty(self) -> bool:
        """Check if all player hands are empty"""
        if not hasattr(self, 'game') or not self.game or not hasattr(self.game, 'players'):
            return False
        
        for player in self.game.players:
            if hasattr(player, 'hand') and player.hand:
                return False
        
        return True
    
    async def broadcast_event(self, event_type: str, event_data: Dict):
        """Broadcast WebSocket event if callback is available"""
        print(f"🔧 BROADCAST_EVENT_DEBUG: broadcast_event called with type: {event_type}")
        
        if self.broadcast_callback:
            print(f"🔧 BROADCAST_EVENT_DEBUG: Callback available, calling broadcast_callback")
            try:
                await self.broadcast_callback(event_type, event_data)
                print(f"🔧 BROADCAST_EVENT_DEBUG: broadcast_callback completed successfully")
            except Exception as e:
                print(f"❌ BROADCAST_EVENT_DEBUG: Exception in broadcast_callback: {e}")
                import traceback
                traceback.print_exc()
                raise
        else:
            print(f"⚠️ BROADCAST_EVENT_DEBUG: No broadcast callback set - event {event_type} not sent")
            logger.debug(f"No broadcast callback set - event {event_type} not sent")
    
    async def _notify_bot_manager(self, new_phase: GamePhase):
        """Notify bot manager about phase changes to trigger bot actions"""
        try:
            from ..bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self, 'room_id', 'unknown')
            
            print(f"🤖 STATE_MACHINE_DEBUG: Notifying bot manager about phase {new_phase.value} for room {room_id}")
            
            # 🚀 AUTOMATIC_SYSTEM: All bot manager notifications now handled automatically via enterprise phase_change events
            print(f"🔧 AUTOMATIC_SYSTEM_DEBUG: Manual bot manager notifications removed for {new_phase.value} - using automatic enterprise system")
                
        except Exception as e:
            logger.error(f"Failed to notify bot manager: {e}", exc_info=True)
    
    async def _notify_bot_manager_data_change(self, phase_data: dict, reason: str):
        """
        🚀 ENTERPRISE: Notify bot manager about phase data changes for automatic bot actions
        
        This implements the enterprise principle of automatic bot triggering on data updates,
        not just phase transitions. Called from base_state enterprise broadcasting.
        """
        try:
            from ..bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self, 'room_id', 'unknown')
            
            print(f"🤖 ENTERPRISE_DATA_DEBUG: Notifying bot manager about data change - reason: {reason}")
            
            # Check if it's declaration phase and if there's a current declarer
            if self.current_phase == GamePhase.DECLARATION:
                current_declarer = phase_data.get('current_declarer')
                if current_declarer:
                    print(f"🤖 ENTERPRISE_DATA_DEBUG: Declaration phase - current declarer: {current_declarer}")
                    
                    # Send phase_change event with full data for bot to decide action
                    await bot_manager.handle_game_event(room_id, "phase_change", {
                        "phase": "declaration",
                        "phase_data": phase_data,
                        "current_declarer": current_declarer,
                        "reason": reason
                    })
                    
            elif self.current_phase == GamePhase.TURN:
                current_player = phase_data.get('current_player')
                if current_player:
                    print(f"🤖 ENTERPRISE_DATA_DEBUG: Turn phase - current player: {current_player}")
                    
                    # Send phase_change event with full data for bot to decide action
                    await bot_manager.handle_game_event(room_id, "phase_change", {
                        "phase": "turn", 
                        "phase_data": phase_data,
                        "current_player": current_player,
                        "reason": reason
                    })
                    
        except Exception as e:
            logger.error(f"Failed to notify bot manager about data change: {e}", exc_info=True)
    
    async def _store_phase_change_event(self, old_phase: Optional[GamePhase], new_phase: GamePhase):
        """
        Store phase change event for replay capability
        
        Args:
            old_phase: Previous phase (can be None for initial transition)
            new_phase: New phase being entered
        """
        print(f"🔧 STORE_EVENT_DEBUG: _store_phase_change_event called: {old_phase} -> {new_phase}")
        
        try:
            payload = {
                'old_phase': old_phase.value if old_phase else None,
                'new_phase': new_phase.value,
                'timestamp': datetime.now().isoformat(),
                'game_state': self.get_serializable_state() if hasattr(self, 'get_serializable_state') else {}
            }
            print(f"🔧 STORE_EVENT_DEBUG: Prepared payload: {payload}")
            
            # Add game-specific context if available
            if hasattr(self, 'game') and self.game:
                payload['game_context'] = {
                    'round_number': getattr(self.game, 'round_number', 0),
                    'player_count': len(getattr(self.game, 'players', [])),
                    'current_player': getattr(self.game, 'current_player', None)
                }
                print(f"🔧 STORE_EVENT_DEBUG: Added game context: {payload['game_context']}")
            
            # Store via action queue which has access to event store
            print(f"🔧 STORE_EVENT_DEBUG: About to call action_queue.store_state_event")
            await self.action_queue.store_state_event(
                event_type='phase_change',
                payload=payload
            )
            print(f"🔧 STORE_EVENT_DEBUG: action_queue.store_state_event completed")
            
            logger.info(f"Stored phase change event: {old_phase} -> {new_phase}")
            print(f"🔧 STORE_EVENT_DEBUG: Event storage successful")
            
        except Exception as e:
            # Don't let event storage failures break the game
            print(f"❌ STORE_EVENT_DEBUG: Exception in _store_phase_change_event: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to store phase change event: {e}")
    
    async def store_game_event(self, event_type: str, payload: dict, player_id: Optional[str] = None):
        """
        Public method to store arbitrary game events
        
        Args:
            event_type: Type of event (e.g., 'game_started', 'round_complete')
            payload: Event data
            player_id: Optional player identifier
        """
        try:
            await self.action_queue.store_state_event(event_type, payload, player_id)
        except Exception as e:
            logger.error(f"Failed to store game event {event_type}: {e}")
    
    # 🔧 FIX: Bot Manager Validation Feedback Methods
    
    async def _notify_bot_manager_action_rejected(self, action: GameAction):
        """Notify bot manager that an action was rejected by state machine"""
        try:
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.game, 'room_id', 'unknown') if self.game else 'unknown'
            
            print(f"🚫 BOT_VALIDATION_DEBUG: Notifying bot manager of rejected action from {action.player_name}")
            
            await bot_manager.handle_game_event(room_id, "action_rejected", {
                "player_name": action.player_name,
                "action_type": action.action_type.value,
                "reason": "Invalid action for current game state",
                "payload": action.payload,
                "is_bot": action.is_bot
            })
            
        except Exception as e:
            logger.error(f"Failed to notify bot manager of rejected action: {e}", exc_info=True)
    
    async def _notify_bot_manager_action_accepted(self, action: GameAction, result: dict):
        """Notify bot manager that an action was accepted and processed"""
        try:
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.game, 'room_id', 'unknown') if self.game else 'unknown'
            
            print(f"✅ BOT_VALIDATION_DEBUG: Notifying bot manager of accepted action from {action.player_name}")
            
            await bot_manager.handle_game_event(room_id, "action_accepted", {
                "player_name": action.player_name,
                "action_type": action.action_type.value,
                "result": result,
                "payload": action.payload,
                "is_bot": action.is_bot
            })
            
        except Exception as e:
            logger.error(f"Failed to notify bot manager of accepted action: {e}", exc_info=True)
    
    async def _notify_bot_manager_action_failed(self, action: GameAction, error_message: str):
        """Notify bot manager that an action failed during processing"""
        try:
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.game, 'room_id', 'unknown') if self.game else 'unknown'
            
            print(f"💥 BOT_VALIDATION_DEBUG: Notifying bot manager of failed action from {action.player_name}")
            
            await bot_manager.handle_game_event(room_id, "action_failed", {
                "player_name": action.player_name,
                "action_type": action.action_type.value,
                "error": error_message,
                "payload": action.payload,
                "is_bot": action.is_bot
            })
            
        except Exception as e:
            logger.error(f"Failed to notify bot manager of failed action: {e}", exc_info=True)