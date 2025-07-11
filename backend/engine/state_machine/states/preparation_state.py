# backend/engine/state_machine/states/preparation_state.py

from typing import Dict, Any, Optional, List, Set
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState
import random
import asyncio
import time


class PreparationState(GameState):
    """
    Preparation Phase State

    Handles:
    - Initial dealing of 8 pieces to each player
    - Weak hand detection (no piece > 9 points)
    - Redeal requests and responses
    - Starter determination based on game rules
    - Transition to Declaration phase
    """

    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.PREPARATION

    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.DECLARATION]

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.REDEAL_REQUEST,
            ActionType.REDEAL_RESPONSE,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
        }

        # Phase-specific state
        self.weak_players: Set[str] = set()
        self.redeal_decisions: Dict[str, bool] = {}  # player -> accept/decline

        # Old sequential system (commented out for simultaneous system)
        # self.pending_weak_players: List[str] = []  # Queue of players to ask
        # self.current_weak_player: Optional[str] = None  # Currently being asked

        # New simultaneous system variables
        self.weak_players_awaiting: Set[str] = set()  # Players who need to decide
        self.decision_start_time: Optional[float] = None
        self.decision_timeout: float = 30.0  # 30 second timeout
        self._decision_lock = asyncio.Lock()  # Prevent race conditions
        self._processing_decisions: bool = False
        self.warning_sent: bool = False

        self.redeal_requester: Optional[str] = None
        self.initial_deal_complete: bool = False

    async def _setup_phase(self) -> None:
        """Initialize preparation phase by dealing cards"""
        self.logger.info("🎴 Preparation phase starting - dealing cards")
        await self._deal_cards()

    async def _cleanup_phase(self) -> None:
        """Finalize preparation results before transition"""
        game = self.state_machine.game

        # Ensure starter is set (but only if not already set by previous round's winner)
        if not hasattr(game, "current_player") or not game.current_player:
            starter = self._determine_starter()
            game.current_player = starter
            self.logger.info(f"🎯 Round starter set to: {starter}")
        else:
            self.logger.info(f"🎯 Round starter already set: {game.current_player}")

        # Ensure round_starter is also set (some code uses this)
        if game.current_player and (
            not hasattr(game, "round_starter") or not game.round_starter
        ):
            game.round_starter = game.current_player

        # Log final state
        multiplier = getattr(game, "redeal_multiplier", 1)
        self.logger.info(
            f"📋 Preparation complete - Starter: {game.current_player}, "
            f"Multiplier: {multiplier}x"
        )

    async def _deal_cards(self) -> None:
        """Deal cards and check for weak hands"""
        game = self.state_machine.game

        # Log when dealing starts
        current_multiplier = getattr(game, "redeal_multiplier", 1)
        # self.logger.info(f"🎴 DEBUG: _deal_cards called, redeal_multiplier={current_multiplier}")

        # Signal that dealing is starting
        # self.logger.info(f"🎴 DEBUG: Sending dealing_cards=True, multiplier={current_multiplier}")
        await self.update_phase_data(
            {"dealing_cards": True, "redeal_multiplier": current_multiplier},
            "Starting to deal cards",
        )

        # Reset player round data before dealing
        for player in game.players:
            player.declared = 0
            player.captured_piles = 0

        # Initialize pile_counts dictionary if not exists
        if not hasattr(game, "pile_counts"):
            game.pile_counts = {}

        # Reset pile counts for new round
        for player in game.players:
            game.pile_counts[player.name] = 0

        # Choose dealing mode - uncomment ONE of the following:

        # 1. Normal random dealing (production)
        game.deal_pieces()

        # 2. Guaranteed no weak hands (testing)
        # game._deal_guaranteed_no_redeal(red_general_player_index=1)

        # 3. Force weak hands (testing redeal logic)
        # game._deal_weak_hand(weak_player_indices=[0,1], max_weak_points=9, limit=3)

        # Examples:
        # game._deal_guaranteed_no_redeal()                              # Random RED_GENERAL assignment
        # game._deal_guaranteed_no_redeal(red_general_player_index=1)    # Player 1 gets RED_GENERAL
        # game._deal_weak_hand([0, 1])                                   # Players 1 & 2 get weak hands
        # game._deal_weak_hand([0], max_weak_points=7, limit=1)          # Player 1 weak, max 1 redeal

        self.initial_deal_complete = True

        # Check for weak hands
        if hasattr(game, "get_weak_hand_players"):
            weak_players = game.get_weak_hand_players()
            self.weak_players = set(weak_players) if weak_players else set()
        else:
            # Fallback for testing
            self.weak_players = set()

        self.logger.info(
            f"🔍 Weak hand check - Found {len(self.weak_players)} "
            f"weak players: {self.weak_players}"
        )

        if self.weak_players:
            # Get current play order (might have changed due to redeal)
            if hasattr(game, "get_player_order_from"):
                # Determine current starter
                if game.current_player:
                    current_starter = game.current_player
                else:
                    # Get first player name properly
                    first_player = game.players[0]
                    current_starter = (
                        first_player
                        if isinstance(first_player, str)
                        else getattr(first_player, "name", str(first_player))
                    )

                play_order = game.get_player_order_from(current_starter)
            else:
                # Extract player names from objects if needed
                play_order = []
                for p in game.players:
                    if isinstance(p, str):
                        play_order.append(p)
                    else:
                        play_order.append(getattr(p, "name", str(p)))

            # Set up simultaneous decision system
            self.weak_players_awaiting = self.weak_players.copy()
            self.decision_start_time = time.time()
            self.warning_sent = False

            # Notify about weak hands (frontend will prompt players)
            await self._notify_weak_hands()

            # Enterprise architecture handles bot triggering automatically via phase_change events
            # No manual trigger needed - bot manager watches phase data updates

            # Start timeout monitoring
            asyncio.create_task(self._monitor_decision_timeout())
        else:
            # No weak hands, keep existing starter or determine new one
            if hasattr(game, "current_player") and game.current_player:
                # Starter already set (e.g., by scoring state for next round)
                starter = game.current_player
                game.round_starter = starter  # Ensure both are set
                self.logger.info(
                    f"✅ No weak hands - keeping existing starter: {starter}"
                )
            else:
                # No starter set, determine one
                starter = self._determine_starter()
                game.current_player = starter
                game.round_starter = starter  # Always set both
                self.logger.info(
                    f"✅ No weak hands - determined new starter: {starter}"
                )

        # Signal that dealing is complete
        final_multiplier = getattr(game, "redeal_multiplier", 1)
        # self.logger.info(f"🎴 DEBUG: Sending dealing_cards=False, multiplier={final_multiplier}, weak_players={list(self.weak_players)}")
        await self.update_phase_data(
            {
                "dealing_cards": False,
                "weak_players": list(self.weak_players),
                "redeal_multiplier": final_multiplier,
            },
            "Cards dealt, checking for weak hands",
        )

    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action is allowed in current state"""
        # Basic validation from parent
        if action.action_type not in self.allowed_actions:
            self.logger.warning(
                f"Action {action.action_type} not allowed in {self.phase_name}"
            )
            return False

        player_name = action.player_name

        if action.action_type == ActionType.REDEAL_REQUEST:
            # Must be in weak players set
            if player_name not in self.weak_players:
                self.logger.warning(
                    f"❌ Redeal request from non-weak player: {player_name}"
                )
                return False

            # Must not have already decided
            if player_name in self.redeal_decisions:
                self.logger.warning(f"❌ Duplicate redeal decision from: {player_name}")
                return False

            return True

        elif action.action_type == ActionType.REDEAL_RESPONSE:
            # Same validation as REQUEST (it's a decline)
            # Create a temporary action to validate
            temp_action = GameAction(
                player_name=player_name,
                action_type=ActionType.REDEAL_REQUEST,
                payload=action.payload,
                timestamp=action.timestamp,
                sequence_id=action.sequence_id,
            )
            return await self._validate_action(temp_action)

        return True

    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid preparation actions"""
        if action.action_type == ActionType.REDEAL_REQUEST:
            # Accept redeal
            action.payload["accept"] = True
            return await self._handle_redeal_decision(action)

        elif action.action_type == ActionType.REDEAL_RESPONSE:
            # Handle redeal response - accept value is already set by WebSocket handler
            accept_value = action.payload.get("accept", False)
            return await self._handle_redeal_decision(action)

        elif action.action_type == ActionType.PLAYER_DISCONNECT:
            return await self._handle_player_disconnect(action)

        elif action.action_type == ActionType.PLAYER_RECONNECT:
            return await self._handle_player_reconnect(action)

        return {"success": False, "error": "Unknown action"}

    async def _handle_redeal_decision(self, action: GameAction) -> Dict[str, Any]:
        """Handle redeal decision with race condition prevention"""
        async with self._decision_lock:
            # Prevent double processing
            if self._processing_decisions:
                return {"success": False, "error": "Processing in progress"}

            # NEW: Prevent late decisions after phase change
            if self.state_machine.current_phase != GamePhase.PREPARATION:
                return {"success": False, "error": "Phase has already changed"}

            player_name = action.player_name
            accept = action.payload.get("accept", False)

            # Validate player
            if player_name not in self.weak_players:
                # self.logger.warning(f"🎴 DEBUG: Rejecting decision - {player_name} not in weak_players: {self.weak_players}")
                return {"success": False, "error": "Not a weak player"}

            if player_name in self.redeal_decisions:
                # self.logger.warning(f"🎴 DEBUG: Rejecting decision - {player_name} already in redeal_decisions: {self.redeal_decisions}")
                return {"success": False, "error": "Already decided"}

            # Record decision
            self.redeal_decisions[player_name] = accept
            self.weak_players_awaiting.discard(player_name)

            self.logger.info(
                f"{'♻️' if accept else '🚫'} {player_name} {'ACCEPTS' if accept else 'DECLINES'} redeal"
            )

            # Check if all decided
            if self._all_weak_decisions_received():
                self._processing_decisions = True
                try:
                    result = await self._process_all_decisions()

                    # NEW: Direct transition if no weak players remain
                    if not self.weak_players:
                        # Check if this was from a redeal (not initial deal)
                        if result.get("redeal") and result.get("complete"):
                            # Allow time for dealing animation to complete
                            self.logger.info(
                                "🎴 Waiting for dealing animation to complete..."
                            )
                            await asyncio.sleep(4.0)
                        await self.state_machine._transition_to(GamePhase.DECLARATION)

                    return result
                finally:
                    self._processing_decisions = False

        # Broadcast update (outside lock)
        await self._broadcast_decision_update(player_name, accept)
        return {
            "success": True,
            "decisions_received": len(self.redeal_decisions),
            "decisions_needed": len(self.weak_players),
        }

    async def _process_all_decisions(self) -> Dict[str, Any]:
        """Process all collected decisions"""
        first_accepter = self._get_first_accepter_by_play_order()

        if first_accepter:
            # Execute redeal
            self.redeal_requester = first_accepter
            game = self.state_machine.game

            # Update game state
            old_multiplier = getattr(game, "redeal_multiplier", 1)
            game.redeal_multiplier = old_multiplier + 1
            game.current_player = first_accepter
            game.round_starter = first_accepter

            self.logger.info(f"♻️ Redeal accepted by {first_accepter} - new starter")
            self.logger.info(
                f"📈 Multiplier: {old_multiplier}x → {game.redeal_multiplier}x"
            )

            # Reset for new deal
            # self.logger.info(f"🎴 DEBUG: Clearing state before redeal - redeal_decisions was: {self.redeal_decisions}")
            self.weak_players.clear()
            self.redeal_decisions.clear()
            self.weak_players_awaiting.clear()
            self.decision_start_time = None

            # Execute redeal
            # self.logger.info(f"🎴 DEBUG: About to execute redeal #{game.redeal_multiplier - 1}")
            await self._deal_cards()

            # Check if new weak hands were found after redeal
            if self.weak_players:
                # New weak hands detected - stay in preparation phase
                self.logger.info(
                    f"🔄 New weak hands found after redeal: {self.weak_players}"
                )
                # self.logger.info(f"🎴 DEBUG: Weak players need to decide again")
                # self.logger.info(f"🎴 DEBUG: Setting up new decision cycle...")

                # Set up new decision cycle
                self.weak_players_awaiting = self.weak_players.copy()
                self.decision_start_time = time.time()
                self.warning_sent = False

                # Notify about new weak hands
                # self.logger.info(f"🎴 DEBUG: Calling _notify_weak_hands() for second decision cycle")
                await self._notify_weak_hands()

                # Start timeout monitoring
                asyncio.create_task(self._monitor_decision_timeout())

                # self.logger.info(f"🎴 DEBUG: New decision cycle started for {len(self.weak_players)} players")

                return {
                    "success": True,
                    "redeal": True,
                    "new_starter": first_accepter,
                    "multiplier": game.redeal_multiplier,
                    "new_weak_hands": True,
                    "weak_players": list(self.weak_players),
                }
            else:
                # No new weak hands - redeal complete
                # Broadcast the multiplier update before returning
                await self.update_phase_data(
                    {"redeal_multiplier": game.redeal_multiplier},
                    f"Redeal complete - no weak hands found, multiplier now {game.redeal_multiplier}x",
                )

                return {
                    "success": True,
                    "redeal": True,
                    "new_starter": first_accepter,
                    "multiplier": game.redeal_multiplier,
                    "complete": True,
                }
        else:
            # All declined - determine starter normally
            self.logger.info(
                "✅ All weak players declined - proceeding with current hands"
            )

            # Clear weak player tracking since all declined
            self.weak_players.clear()
            self.redeal_decisions.clear()
            self.weak_players_awaiting.clear()

            starter = self._determine_starter()
            game = self.state_machine.game
            game.current_player = starter
            game.round_starter = starter

            return {"success": True, "redeal": False, "starter": starter}

    async def _monitor_decision_timeout(self) -> None:
        """Monitor and handle decision timeouts"""
        while not self._all_weak_decisions_received():
            await asyncio.sleep(1.0)

            if not self.weak_players:  # Phase changed
                return

            elapsed = time.time() - self.decision_start_time

            # Warning at 20 seconds
            if elapsed > 20 and not self.warning_sent:
                await self.update_phase_data(
                    {"timeout_warning": True, "seconds_remaining": 10},
                    "10 seconds remaining for redeal decisions",
                )
                self.warning_sent = True

            # Force timeout at 30 seconds
            if elapsed > self.decision_timeout:
                await self._force_timeout_decisions()
                return

    async def _force_timeout_decisions(self) -> None:
        """Auto-decline for all pending decisions"""
        async with self._decision_lock:
            for player_name in list(self.weak_players_awaiting):
                if player_name not in self.redeal_decisions:
                    self.redeal_decisions[player_name] = False
                    self.logger.info(f"⏱️ Auto-declined for {player_name} (timeout)")

            self.weak_players_awaiting.clear()
            await self._process_all_decisions()

    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during preparation"""
        player_name = action.player_name

        # If disconnected player is awaiting redeal decision, auto-decline
        if player_name in self.weak_players_awaiting:
            self.logger.info(
                f"🔌 Weak player {player_name} disconnected - auto-declining"
            )
            # Create decline action
            decline_action = GameAction(
                player_name=player_name,
                action_type=ActionType.REDEAL_RESPONSE,
                payload={"accept": False},
                timestamp=action.timestamp,
                sequence_id=action.sequence_id,
            )
            return await self._handle_redeal_decision(decline_action)

        return {"success": True}

    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during preparation"""
        # Send current state to reconnected player
        return {
            "success": True,
            "weak_players": list(self.weak_players),
            "weak_players_awaiting": list(self.weak_players_awaiting),
            "redeal_decisions": self.redeal_decisions,
            "simultaneous_mode": True,
        }

    def _determine_starter(self) -> str:
        """Determine round starter based on game rules"""
        game = self.state_machine.game

        # Priority 1: Redeal requester (overrides all)
        if self.redeal_requester:
            self.logger.info(f"🎯 Starter: {self.redeal_requester} (requested redeal)")
            return self.redeal_requester

        # Priority 2: Round 1 - player with GENERAL_RED
        round_num = getattr(game, "round_number", 1)
        self.logger.info(f"🔍 STARTER_DEBUG: Current round number: {round_num}")
        if round_num == 1:
            # Check if game has player objects with hands
            if hasattr(game, "players") and game.players:
                for player in game.players:
                    player_name = getattr(player, "name", str(player))
                    if hasattr(player, "hand"):
                        for piece in player.hand:
                            piece_str = str(piece)
                            if "GENERAL_RED" in piece_str:
                                self.logger.info(
                                    f"🎯 Starter: {player_name} (has GENERAL_RED)"
                                )
                                return player_name
                    else:
                        pass

        # Priority 3: Previous round's last turn winner
        if hasattr(game, "last_turn_winner") and game.last_turn_winner:
            self.logger.info(f"🎯 Starter: {game.last_turn_winner} (won last turn)")
            return game.last_turn_winner

        # Fallback: First player
        if hasattr(game, "players") and game.players:
            if hasattr(game.players[0], "name"):
                starter = game.players[0].name
            else:
                starter = game.players[0]
        else:
            starter = "Player1"

        self.logger.info(f"🎯 Starter: {starter} (fallback - first player)")
        return starter

    def _all_weak_decisions_received(self) -> bool:
        """Check if all weak players have made their decisions"""
        return set(self.redeal_decisions.keys()) == self.weak_players

    def _get_first_accepter_by_play_order(self) -> Optional[str]:
        """Get first player in play order who accepted redeal"""
        game = self.state_machine.game

        # Get play order from current starter
        if hasattr(game, "get_player_order_from"):
            if game.current_player:
                current_starter = game.current_player
            else:
                first_player = game.players[0]
                current_starter = (
                    first_player
                    if isinstance(first_player, str)
                    else getattr(first_player, "name", str(first_player))
                )

            play_order = game.get_player_order_from(current_starter)
        else:
            # Fallback to direct player list
            play_order = []
            for p in game.players:
                if isinstance(p, str):
                    play_order.append(p)
                else:
                    play_order.append(getattr(p, "name", str(p)))

        # Find first accepter in play order
        for player in play_order:
            player_name = (
                player
                if isinstance(player, str)
                else getattr(player, "name", str(player))
            )
            if self.redeal_decisions.get(player_name) == True:
                return player_name

        return None

    def _count_acceptances(self) -> int:
        """Count how many players accepted redeal"""
        return sum(1 for decision in self.redeal_decisions.values() if decision)

    async def _validate_state_consistency(self) -> bool:
        """Ensure internal state is consistent"""
        # All decisions must be from weak players
        for player in self.redeal_decisions.keys():
            if player not in self.weak_players:
                self.logger.error(f"Invalid decision from non-weak player: {player}")
                return False

        # All awaiting players must be weak players
        if not self.weak_players_awaiting.issubset(self.weak_players):
            self.logger.error("Awaiting players not subset of weak players")
            return False

        # Decisions + awaiting should equal weak players
        decided = set(self.redeal_decisions.keys())
        if decided | self.weak_players_awaiting != self.weak_players:
            self.logger.error("Decision tracking inconsistent")
            return False

        return True

    async def _notify_weak_hands(self) -> None:
        """Notify about weak hands found using enterprise architecture"""
        game = self.state_machine.game

        # Prepare data for frontend
        weak_hand_data = {
            "weak_players": list(self.weak_players),
            "weak_players_awaiting": list(self.weak_players_awaiting),
            "decisions_received": len(self.redeal_decisions),
            "decisions_needed": len(self.weak_players),
            "redeal_multiplier": getattr(game, "redeal_multiplier", 1),
            "simultaneous_mode": True,
            "decision_timeout": self.decision_timeout,
        }

        # self.logger.info(f"🎴 DEBUG: _notify_weak_hands broadcasting data: {weak_hand_data}")

        # Use enterprise broadcasting
        await self.update_phase_data(
            weak_hand_data,
            f"Weak hands detected: {list(self.weak_players)} - awaiting simultaneous decisions",
        )

    async def _broadcast_decision_update(
        self, player_name: str, accepted: bool
    ) -> None:
        """Broadcast decision update to all clients"""
        update_data = {
            "player_decided": player_name,
            "decision": "accept" if accepted else "decline",
            "decisions_received": len(self.redeal_decisions),
            "decisions_needed": len(self.weak_players),
            "weak_players_awaiting": list(self.weak_players_awaiting),
            "redeal_decisions": dict(self.redeal_decisions),  # Add this for bot manager
            "all_decided": self._all_weak_decisions_received(),
            "redeal_multiplier": getattr(
                self.state_machine.game, "redeal_multiplier", 1
            ),
        }

        # Use enterprise broadcasting
        await self.update_phase_data(
            update_data,
            f"Player {player_name} {'accepted' if accepted else 'declined'} redeal ({len(self.redeal_decisions)}/{len(self.weak_players)} decided)",
        )

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to Declaration phase"""
        # Only check basic conditions - redeal decisions now trigger transitions directly

        if not self.initial_deal_complete:
            return None

        if not self.weak_players:
            # No weak hands found - this is the only polling-based transition now
            return GamePhase.DECLARATION

        # If we have weak players, wait for redeal decisions to trigger transition directly
        return None
