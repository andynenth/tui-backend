# backend/engine/state_machine/states/round_start_state.py

import time
from typing import Any, Dict, List, Optional

from ..base_state import GameState
from ..core import ActionType, GameAction, GamePhase


class RoundStartState(GameState):
    """
    Round Start Phase State

    Displays round information after preparation:
    - Round number
    - Who is the starter
    - Why they are the starter

    Auto-transitions to Declaration phase after 5 seconds
    """

    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.ROUND_START

    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.DECLARATION]

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
        }

        # Phase-specific state
        self.display_duration: float = 5.0  # 5 seconds
        self.start_time: Optional[float] = None

    async def _setup_phase(self) -> None:
        """Initialize round start display"""
        game = self.state_machine.game

        # Get starter reason (should be set by PreparationState)
        starter_reason = getattr(game, "starter_reason", "default")

        # Get current player (starter)
        starter = game.current_player

        # Log the round start
        self.logger.info(
            f"📋 Round {game.round_number} starting - Starter: {starter} ({starter_reason})"
        )

        # Send phase data to frontend
        await self.update_phase_data(
            {
                "round_number": game.round_number,
                "current_starter": starter,
                "starter_reason": starter_reason,
                "display_duration": self.display_duration,
            },
            f"Round {game.round_number} starting with {starter}",
        )

        # 🚀 V2 OPTIMIZATION: Fire semantic events
        if game.round_number == 1:
            # Fire game_started event for first round only
            players = []
            if hasattr(game, "players") and game.players:
                players = [p.name for p in game.players]
            
            await self.state_machine.store_game_event(
                "game_started",
                {
                    "players": players,
                    "timestamp": time.time(),
                    "round_number": game.round_number,
                },
            )
            self.logger.info(f"🚀 V2 EVENT: game_started event fired for room {self.state_machine.room_id}")
        
        # Fire round_started event for every round
        await self.state_machine.store_game_event(
            "round_started",
            {
                "round_number": game.round_number,
                "starter": starter,
                "starter_reason": starter_reason,
                "timestamp": time.time(),
            },
        )
        self.logger.info(f"🚀 V2 EVENT: round_started event fired for round {game.round_number}")

        # Record start time for auto-transition
        self.start_time = time.time()

    async def _cleanup_phase(self) -> None:
        """Clean up before transitioning to Declaration"""
        self.logger.info(
            "🎯 Round start display complete - transitioning to Declaration"
        )

    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action for round start phase"""
        # Only allow disconnect/reconnect during display
        return action.action_type in self.allowed_actions

    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions for round start phase"""
        result = {"success": False, "message": "", "data": {}}

        try:
            if action.action_type == ActionType.PLAYER_DISCONNECT:
                result = await self._handle_player_disconnect(action)
            elif action.action_type == ActionType.PLAYER_RECONNECT:
                result = await self._handle_player_reconnect(action)
            else:
                result["message"] = (
                    f"Action {action.action_type} not supported in Round Start Phase"
                )

        except Exception as e:
            self.logger.error(f"Error processing action {action.action_type}: {e}")
            result["message"] = f"Error processing action: {str(e)}"

        return result

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if display time has elapsed"""
        if self.start_time is None:
            return None

        elapsed = time.time() - self.start_time

        if elapsed >= self.display_duration:
            return GamePhase.DECLARATION

        return None

    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during round start"""
        player_name = action.player_name
        self.logger.info(f"🔌 Player {player_name} disconnected during Round Start")

        # Mark player as disconnected
        game = self.state_machine.game
        if hasattr(game, "players"):
            for player in game.players:
                if player.name == player_name:
                    player.connected = False
                    break

        return {"success": True, "message": f"Player {player_name} disconnected"}

    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during round start"""
        player_name = action.player_name
        self.logger.info(f"🔌 Player {player_name} reconnected during Round Start")

        # Mark player as connected
        game = self.state_machine.game
        if hasattr(game, "players"):
            for player in game.players:
                if player.name == player_name:
                    player.connected = True
                    break

        # Send current state to reconnected player
        return {
            "success": True,
            "message": f"Player {player_name} reconnected",
            "phase_data": {
                "round_number": game.round_number,
                "current_starter": game.current_player,
                "starter_reason": getattr(game, "starter_reason", "default"),
                "display_duration": self.display_duration,
                "elapsed": time.time() - self.start_time if self.start_time else 0,
            },
        }
