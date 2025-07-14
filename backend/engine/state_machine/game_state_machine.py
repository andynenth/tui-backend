# backend/engine/state_machine/game_state_machine.py

import asyncio
import logging
from typing import Dict, Optional, List, Set
from datetime import datetime

from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .base_state import GameState
from .states import PreparationState, DeclarationState, TurnState, ScoringState
from .states.game_over_state import GameOverState
from .states.waiting_state import WaitingState
from .states.turn_results_state import TurnResultsState
from .states.round_start_state import RoundStartState


logger = logging.getLogger(__name__)


class GameStateMachine:
    """
    Central coordinator for game state management.
    Manages phase transitions and delegates action handling to appropriate states.
    """

    def __init__(self, game, broadcast_callback=None):
        self.game = game
        logger.info(
            f"🔍 ROUND_DEBUG: GameStateMachine created with game: {game}, round_number: {getattr(game, 'round_number', 'NO_ATTR') if game else 'NO_GAME'}"
        )
        # Initialize room_id as None - will be set by Room class before starting
        self.room_id = None
        # Pass room_id to ActionQueue for event storage
        room_id = getattr(game, "room_id", None) if game else None
        self.action_queue = ActionQueue(room_id=room_id)
        self.current_state: Optional[GameState] = None
        self.current_phase: Optional[GamePhase] = None
        self.is_running = False
        self._process_task: Optional[asyncio.Task] = None
        self.broadcast_callback = broadcast_callback  # For WebSocket broadcasting

        # Initialize all available states
        self.states: Dict[GamePhase, GameState] = {
            GamePhase.WAITING: WaitingState(self),
            GamePhase.PREPARATION: PreparationState(self),
            GamePhase.ROUND_START: RoundStartState(self),
            GamePhase.DECLARATION: DeclarationState(self),
            GamePhase.TURN: TurnState(self),
            GamePhase.TURN_RESULTS: TurnResultsState(self),
            GamePhase.SCORING: ScoringState(self),
            GamePhase.GAME_OVER: GameOverState(self),
        }

        # Transition validation map
        self._valid_transitions = {
            GamePhase.WAITING: {GamePhase.PREPARATION},
            GamePhase.PREPARATION: {GamePhase.ROUND_START},
            GamePhase.ROUND_START: {GamePhase.DECLARATION},
            GamePhase.DECLARATION: {GamePhase.TURN},
            GamePhase.TURN: {GamePhase.TURN_RESULTS},
            GamePhase.TURN_RESULTS: {GamePhase.TURN, GamePhase.SCORING},
            GamePhase.SCORING: {
                GamePhase.PREPARATION,
                GamePhase.GAME_OVER,
            },  # Next round or game over
            GamePhase.GAME_OVER: set(),  # Terminal state - no transitions
        }

    async def start(self, initial_phase: GamePhase = GamePhase.WAITING):
        """Start the state machine with initial phase"""
        if self.is_running:
            logger.warning("State machine already running")
            return

        logger.info(f"🚀 Starting state machine in {initial_phase} phase")
        self.is_running = True

        # Start processing loop
        self._process_task = asyncio.create_task(self._process_loop())

        # Enter initial phase
        await self._transition_to(initial_phase)

    async def stop(self):
        """Stop the state machine"""
        logger.info("🛑 Stopping state machine")
        self.is_running = False

        # Cancel processing task
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
        Add action to queue for processing.
        Returns immediately with acknowledgment.
        """
        if not self.is_running:
            return {"success": False, "error": "State machine not running"}

        await self.action_queue.add_action(action)
        return {"success": True, "queued": True}

    async def _process_loop(self):
        """Main processing loop for queued actions and polling-based transitions"""
        logger.info("State machine process loop started")
        while self.is_running:
            try:

                # Process any pending actions
                await self.process_pending_actions()

                # Check for phase transitions (polling-based approach)
                if self.current_state:
                    next_phase = await self.current_state.check_transition_conditions()
                    if next_phase:
                        await self._transition_to(next_phase)

                # Improved delay: 0.5s instead of original 100ms for better performance
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ STATE_MACHINE_DEBUG: Error in process loop: {e}")
                logger.error(f"Error in process loop: {e}", exc_info=True)

        logger.info("State machine process loop ended")

    async def process_pending_actions(self):
        """Process all actions in queue"""
        if not self.current_state:
            return

        actions = await self.action_queue.process_actions()
        for action in actions:
            try:
                result = await self.current_state.handle_action(action)

                # 🔧 FIX: Validate action result and notify bot manager of failures
                if result is None:
                    logger.info(
                        f"Action rejected: {action.action_type.value} from {action.player_name}"
                    )
                    await self._notify_bot_manager_action_rejected(action)
                else:
                    await self._notify_bot_manager_action_accepted(action, result)

            except Exception as e:
                logger.error(f"Error processing action: {e}", exc_info=True)
                await self._notify_bot_manager_action_failed(action, str(e))

    async def _transition_to(self, new_phase: GamePhase):
        """Transition to a new phase"""
        logger.info(f"Transitioning from {self.current_phase} to {new_phase}")

        # Validate transition (skip validation for initial transition)
        if self.current_phase and new_phase not in self._valid_transitions.get(
            self.current_phase, set()
        ):
            logger.error(f"❌ Invalid transition: {self.current_phase} -> {new_phase}")
            print(f"❌ STATE_MACHINE_DEBUG: Invalid transition blocked!")
            return

        # Get new state
        new_state = self.states.get(new_phase)
        if not new_state:
            logger.error(f"❌ No state handler for phase: {new_phase}")
            return

        logger.info(f"🔄 Transitioning: {self.current_phase} -> {new_phase}")
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()

        # Update phase and state
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.current_state = new_state

        # Enter new state
        await self.current_state.on_enter()

        # Store phase change event for replay capability
        await self._store_phase_change_event(old_phase, new_phase)

        # 🔧 REMOVED: Duplicate broadcast - enterprise architecture already handles this
        # The base_state.py auto-broadcasts phase_change with round number included
        # await self._broadcast_phase_change_with_hands(new_phase)

        # 🤖 Trigger bot manager for phase changes
        await self._notify_bot_manager(new_phase)

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
            if key == "declaration_order" and isinstance(value, list):
                # Convert Player objects to player names
                serializable_data[key] = [
                    getattr(player, "name", str(player)) for player in value
                ]
            elif hasattr(value, "__dict__"):
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
            "phase_data": self.get_phase_data(),
        }

        # Add player hands to the data
        if hasattr(self, "game") and self.game and hasattr(self.game, "players"):
            players_data = {}
            for player in self.game.players:
                player_name = getattr(player, "name", str(player))
                player_hand = []

                # Get player's hand
                if hasattr(player, "hand") and player.hand:
                    player_hand = [str(piece) for piece in player.hand]

                players_data[player_name] = {
                    "hand": player_hand,
                    "hand_size": len(player_hand),
                }

            base_data["players"] = players_data

        # Send to all players
        await self.broadcast_event("phase_change", base_data)

    async def broadcast_event(self, event_type: str, event_data: Dict):
        """Broadcast WebSocket event if callback is available"""
        if self.broadcast_callback:
            await self.broadcast_callback(event_type, event_data)
        else:
            logger.debug(f"No broadcast callback set - event {event_type} not sent")

    async def _notify_bot_manager(self, new_phase: GamePhase):
        """Notify bot manager about phase changes to trigger bot actions"""
        try:
            from ..bot_manager import BotManager

            bot_manager = BotManager()
            room_id = getattr(self, "room_id", None)
            if not room_id:
                logger.warning(
                    "⚠️ Room ID not set on state machine - skipping bot manager notification"
                )
                return

            logger.info(f"Notifying bot manager about phase {new_phase.value}")

            if new_phase == GamePhase.ROUND_START:
                # Just notify about round start, don't trigger bot actions yet
                await bot_manager.handle_game_event(
                    room_id,
                    "phase_change",
                    {
                        "phase": new_phase.value,
                        "phase_data": self.get_phase_data(),
                    },
                )
            elif new_phase == GamePhase.DECLARATION:
                # Now trigger bot declarations
                await bot_manager.handle_game_event(
                    room_id,
                    "round_started",
                    {
                        "phase": new_phase.value,
                        "starter": getattr(
                            self.game,
                            "round_starter",
                            (
                                self.game.players[0].name
                                if self.game.players
                                else "unknown"
                            ),
                        ),
                    },
                )
            elif new_phase == GamePhase.GAME_OVER:
                # Notify bot manager that the game has ended
                game_over_data = {
                    "phase": new_phase.value,
                    "final_scores": {},
                    "winner": None,
                    "round_number": getattr(self.game, "round_number", 0),
                }

                # Get final scores and winner if available
                if hasattr(self.game, "players") and self.game.players:
                    for player in self.game.players:
                        player_name = getattr(player, "name", str(player))
                        player_score = getattr(player, "score", 0)
                        game_over_data["final_scores"][player_name] = player_score

                    # Find winner (highest score)
                    if game_over_data["final_scores"]:
                        winner = max(
                            game_over_data["final_scores"].items(), key=lambda x: x[1]
                        )
                        game_over_data["winner"] = winner[0]

                await bot_manager.handle_game_event(
                    room_id, "game_over", game_over_data
                )

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
            room_id = getattr(self, "room_id", None)
            if not room_id:
                logger.warning(
                    "⚠️ Room ID not set on state machine - skipping bot manager notification"
                )
                return

            # Check if it's declaration phase and if there's a current declarer
            if self.current_phase == GamePhase.DECLARATION:
                current_declarer = phase_data.get("current_declarer")
                if current_declarer:

                    # Send phase_change event with full data for bot to decide action
                    try:
                        await bot_manager.handle_game_event(
                            room_id,
                            "phase_change",
                            {
                                "phase": "declaration",
                                "phase_data": phase_data,
                                "current_declarer": current_declarer,
                                "reason": reason,
                            },
                        )
                    except Exception as e:
                        print(
                            f"❌ ENTERPRISE_ERROR: bot_manager.handle_game_event failed: {e}"
                        )
                        raise

            elif self.current_phase == GamePhase.PREPARATION:
                weak_players_awaiting = phase_data.get("weak_players_awaiting", set())
                if weak_players_awaiting:
                    # Send phase_change event for bot redeal decisions
                    await bot_manager.handle_game_event(
                        room_id,
                        "phase_change",
                        {
                            "phase": "preparation",
                            "phase_data": phase_data,
                            "reason": reason,
                        },
                    )

            elif self.current_phase == GamePhase.TURN:
                current_player = phase_data.get("current_player")
                if current_player:

                    # Send phase_change event with full data for bot to decide action
                    await bot_manager.handle_game_event(
                        room_id,
                        "phase_change",
                        {
                            "phase": "turn",
                            "phase_data": phase_data,
                            "current_player": current_player,
                            "reason": reason,
                        },
                    )

        except Exception as e:
            logger.error(
                f"Failed to notify bot manager about data change: {e}", exc_info=True
            )

    async def _store_phase_change_event(
        self, old_phase: Optional[GamePhase], new_phase: GamePhase
    ):
        """
        Store phase change event for replay capability

        Args:
            old_phase: Previous phase (can be None for initial transition)
            new_phase: New phase being entered
        """
        try:
            payload = {
                "old_phase": old_phase.value if old_phase else None,
                "new_phase": new_phase.value,
                "timestamp": datetime.now().isoformat(),
                "game_state": (
                    self.get_serializable_state()
                    if hasattr(self, "get_serializable_state")
                    else {}
                ),
            }

            # Add game-specific context if available
            if hasattr(self, "game") and self.game:
                payload["game_context"] = {
                    "round_number": getattr(self.game, "round_number", 0),
                    "player_count": len(getattr(self.game, "players", [])),
                    "current_player": getattr(self.game, "current_player", None),
                }

            # Store via action queue which has access to event store
            await self.action_queue.store_state_event(
                event_type="phase_change", payload=payload
            )

            logger.info(f"Stored phase change event: {old_phase} -> {new_phase}")

        except Exception as e:
            # Don't let event storage failures break the game
            logger.error(f"Failed to store phase change event: {e}")

    async def store_game_event(
        self, event_type: str, payload: dict, player_id: Optional[str] = None
    ):
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
            from ..bot_manager import BotManager

            bot_manager = BotManager()
            room_id = getattr(self, "room_id", None)
            if not room_id:
                logger.warning(
                    "⚠️ Room ID not set on state machine - skipping bot manager notification"
                )
                return

            await bot_manager.handle_game_event(
                room_id,
                "action_rejected",
                {
                    "player_name": action.player_name,
                    "action_type": action.action_type.value,
                    "reason": "Invalid action for current game state",
                    "payload": action.payload,
                    "is_bot": action.is_bot,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to notify bot manager of rejected action: {e}", exc_info=True
            )

    async def _notify_bot_manager_action_accepted(
        self, action: GameAction, result: dict
    ):
        """Notify bot manager that an action was accepted and processed"""
        try:
            from ..bot_manager import BotManager

            bot_manager = BotManager()
            room_id = getattr(self, "room_id", None)
            if not room_id:
                logger.warning(
                    "⚠️ Room ID not set on state machine - skipping bot manager notification"
                )
                return

            await bot_manager.handle_game_event(
                room_id,
                "action_accepted",
                {
                    "player_name": action.player_name,
                    "action_type": action.action_type.value,
                    "result": result,
                    "payload": action.payload,
                    "is_bot": action.is_bot,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to notify bot manager of accepted action: {e}", exc_info=True
            )

    async def _notify_bot_manager_action_failed(
        self, action: GameAction, error_message: str
    ):
        """Notify bot manager that an action failed during processing"""
        try:
            from ..bot_manager import BotManager

            bot_manager = BotManager()
            room_id = getattr(self, "room_id", None)
            if not room_id:
                logger.warning(
                    "⚠️ Room ID not set on state machine - skipping bot manager notification"
                )
                return

            await bot_manager.handle_game_event(
                room_id,
                "action_failed",
                {
                    "player_name": action.player_name,
                    "action_type": action.action_type.value,
                    "error": error_message,
                    "payload": action.payload,
                    "is_bot": action.is_bot,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to notify bot manager of failed action: {e}", exc_info=True
            )

    async def force_end_game(self, reason: str) -> None:
        """Force end the game due to critical error"""
        logger.critical(f"Force ending game: {reason}")
        self.is_running = False

        if self._process_task and not self._process_task.done():
            self._process_task.cancel()

        # Notify room manager if available
        if hasattr(self, "room_id") and self.room_id:
            from ...room_manager import room_manager

            room = room_manager.get_room(self.room_id)
            if room:
                await room.handle_critical_error(reason)
