# backend/engine/state_machine/states/waiting_state.py

import asyncio
from typing import Any, Dict, List, Optional, Set

from ..base_state import GameState
from ..core import ActionType, GameAction, GamePhase


class WaitingState(GameState):
    """
    Waiting Phase State

    Handles:
    - Room setup and player connection management
    - Player readiness tracking and validation
    - Room capacity validation (exactly 4 players)
    - Connection status monitoring and recovery
    - Transition to Preparation phase when ready
    """

    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.WAITING

    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION]

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.PHASE_TRANSITION,  # Allow manual game start
        }

        # Phase-specific state for waiting room
        self.connected_players: Dict[str, dict] = {}  # player_id -> connection info
        self.ready_players: Set[str] = set()  # Players who confirmed ready
        self.room_capacity: int = 4  # Required player count
        self.game_start_requested: bool = False  # Host requested game start
        self.room_setup_complete: bool = False  # All setup validations passed

    async def _setup_phase(self) -> None:
        """Initialize waiting phase with room state"""
        self.logger.info("⏳ Waiting phase starting - room lobby active")

        # Initialize room state based on current room status
        await self._initialize_room_state()

        # Broadcast initial waiting phase to all connected clients
        await self._broadcast_waiting_state()

    async def _initialize_room_state(self) -> None:
        """Initialize room state from current room configuration"""
        try:
            # Get room instance from state machine
            room = getattr(self.state_machine, "room", None)
            if not room:
                self.logger.warning("No room instance found in state machine")
                return

            # Track connected players from room slots
            self.connected_players.clear()
            if hasattr(room, "players") and room.players:
                for i, player in enumerate(room.players):
                    if player is not None:
                        player_name = (
                            player
                            if isinstance(player, str)
                            else getattr(player, "name", f"Player{i+1}")
                        )
                        self.connected_players[player_name] = {
                            "slot": f"P{i+1}",
                            "is_bot": (
                                getattr(player, "is_bot", False)
                                if not isinstance(player, str)
                                else False
                            ),
                            "is_host": (
                                getattr(player, "is_host", False)
                                if not isinstance(player, str)
                                else (i == 0)
                            ),
                            "connected": True,
                            "ready": True,  # Assume bots and existing players are ready
                        }

            # 🚀 ENTERPRISE: Update phase data with room state
            await self.update_phase_data(
                {
                    "connected_players": len(self.connected_players),
                    "required_players": self.room_capacity,
                    "room_ready": len(self.connected_players) >= self.room_capacity,
                    "connected_player_names": list(
                        self.connected_players.keys()
                    ),  # Just names (base_state.py handles full players data)
                },
                "Initialized waiting room state",
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize room state: {e}", exc_info=True)

    async def _broadcast_waiting_state(self) -> None:
        """Broadcast current waiting state to all clients"""
        try:
            # Prepare room state data for frontend
            room_state = {
                "phase": self.phase_name.value,
                "connected_players": self.connected_players,
                "ready_players": list(self.ready_players),
                "room_capacity": self.room_capacity,
                "players_needed": max(
                    0, self.room_capacity - len(self.connected_players)
                ),
                "can_start_game": self._can_start_game(),
                "room_setup_complete": self.room_setup_complete,
            }

            # 🚀 ENTERPRISE: Broadcast custom event for waiting state updates
            await self.broadcast_custom_event("room_state_update", room_state)

        except Exception as e:
            self.logger.error(f"Failed to broadcast waiting state: {e}", exc_info=True)

    def _can_start_game(self) -> bool:
        """Check if game can be started based on room conditions"""
        return (
            len(self.connected_players) >= self.room_capacity
            and len(self.ready_players) >= len(self.connected_players)
            and not self.game_start_requested
        )

    async def handle_action(self, action: GameAction) -> bool:
        """Handle waiting phase specific actions"""
        try:
            if action.action_type == ActionType.PLAYER_DISCONNECT:
                return await self._handle_player_disconnect(action)
            elif action.action_type == ActionType.PLAYER_RECONNECT:
                return await self._handle_player_reconnect(action)
            elif action.action_type == ActionType.PHASE_TRANSITION:
                return await self._handle_game_start_request(action)
            else:
                self.logger.warning(
                    f"Unhandled action in waiting phase: {action.action_type}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error handling action {action.action_type}: {e}", exc_info=True
            )
            return False

    async def _handle_player_disconnect(self, action: GameAction) -> bool:
        """Handle player disconnection during waiting"""
        player_name = action.player_name

        if player_name in self.connected_players:
            # Mark player as disconnected but keep in room
            self.connected_players[player_name]["connected"] = False
            self.ready_players.discard(player_name)

            # 🚀 ENTERPRISE: Update phase data for disconnection
            await self.update_phase_data(
                {
                    "player_disconnected": player_name,
                    "connected_count": sum(
                        1 for p in self.connected_players.values() if p["connected"]
                    ),
                    "room_ready": self._can_start_game(),
                },
                f"Player {player_name} disconnected from waiting room",
            )

            # Broadcast updated room state
            await self._broadcast_waiting_state()

        return True

    async def _handle_player_reconnect(self, action: GameAction) -> bool:
        """Handle player reconnection during waiting"""
        player_name = action.player_name

        if player_name in self.connected_players:
            # Mark player as reconnected and ready
            self.connected_players[player_name]["connected"] = True
            self.ready_players.add(player_name)

            # 🚀 ENTERPRISE: Update phase data for reconnection
            await self.update_phase_data(
                {
                    "player_reconnected": player_name,
                    "connected_count": sum(
                        1 for p in self.connected_players.values() if p["connected"]
                    ),
                    "room_ready": self._can_start_game(),
                },
                f"Player {player_name} reconnected to waiting room",
            )

            # Broadcast updated room state
            await self._broadcast_waiting_state()

        return True

    async def _handle_game_start_request(self, action: GameAction) -> bool:
        """Handle request to start the game"""
        if not self._can_start_game():
            self.logger.warning("Game start requested but conditions not met")
            await self.broadcast_custom_event(
                "game_start_failed",
                {
                    "reason": "insufficient_players",
                    "required": self.room_capacity,
                    "current": len(self.connected_players),
                },
            )
            return False

        # Mark game start as requested
        self.game_start_requested = True
        self.room_setup_complete = True

        # 🚀 ENTERPRISE: Update phase data for game start
        await self.update_phase_data(
            {
                "game_start_requested": True,
                "transitioning_to": GamePhase.PREPARATION.value,
                "final_player_names": list(
                    self.connected_players.keys()
                ),  # Just names (base_state.py handles full players data)
            },
            "Game start requested - transitioning to preparation",
        )

        return True

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to preparation phase"""
        if self.game_start_requested and self.room_setup_complete:
            self.logger.info("🚀 Waiting phase complete - transitioning to preparation")
            return GamePhase.PREPARATION

        return None

    async def _cleanup_phase(self) -> None:
        """Clean up waiting phase before transition"""
        self.logger.info("⏳ Cleaning up waiting phase")

        # Clear waiting-specific state
        self.game_start_requested = False
        self.room_setup_complete = False

        # Keep connected players info for preparation phase
        # (will be used by preparation state for player setup)

    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action is appropriate for waiting phase"""
        if action.action_type == ActionType.PLAYER_DISCONNECT:
            return action.player_name in self.connected_players
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            return action.player_name in self.connected_players
        elif action.action_type == ActionType.PHASE_TRANSITION:
            return self._can_start_game()

        return False

    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process validated action and return result"""
        if action.action_type == ActionType.PLAYER_DISCONNECT:
            await self._handle_player_disconnect(action)
            return {"success": True, "action": "player_disconnected"}
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            await self._handle_player_reconnect(action)
            return {"success": True, "action": "player_reconnected"}
        elif action.action_type == ActionType.PHASE_TRANSITION:
            await self._handle_game_start_request(action)
            return {"success": True, "action": "game_start_requested"}

        return {"success": False, "error": "unhandled_action"}
