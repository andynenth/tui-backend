# backend/engine/bot_manager.py

import asyncio
import hashlib
import random
import time
from typing import Dict, List, Optional, Set

import engine.ai as ai
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction


class BotManager:
    """
    Centralized bot management system

    🚀 ENTERPRISE ARCHITECTURE COMPLIANCE:
    - All bot actions MUST go through state machine for automatic broadcasting
    - NO manual broadcast() calls allowed - violates enterprise architecture
    - State machine ensures automatic phase_change events and sync bug prevention
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_games = {}
        return cls._instance

    def __init__(self):
        if not hasattr(self, "active_games"):
            self.active_games: Dict[str, GameBotHandler] = {}

    def register_game(self, room_id: str, game, state_machine=None):
        """
        Register a game for bot management.

        Creates a GameBotHandler instance to manage bot actions for the game.

        Args:
            room_id: Unique identifier for the game room
            game: Game instance to manage
            state_machine: Optional state machine for coordinating bot actions
        """
        self.active_games[room_id] = GameBotHandler(room_id, game, state_machine)

    def unregister_game(self, room_id: str):
        """
        Remove a game from bot management.

        Cleans up the GameBotHandler instance when a game ends.

        Args:
            room_id: Unique identifier for the game room to remove
        """
        if room_id in self.active_games:
            del self.active_games[room_id]

    async def handle_game_event(self, room_id: str, event: str, data: dict):
        """
        Handle game events that might trigger bot actions.

        Delegates event handling to the appropriate GameBotHandler.

        Args:
            room_id: Unique identifier for the game room
            event: Name of the game event (e.g., 'phase_change', 'player_action')
            data: Event data containing relevant game state information
        """
        if room_id not in self.active_games:
            return

        handler = self.active_games[room_id]
        await handler.handle_event(event, data)


class GameBotHandler:
    """Handles bot actions for a specific game"""

    def __init__(self, room_id: str, game, state_machine=None):
        self.room_id = room_id
        self.game = game
        self.state_machine = state_machine
        self.processing = False
        self._lock = asyncio.Lock()

        # 🔧 RACE_CONDITION_FIX: Bot action deduplication system
        self._bot_action_cache: Dict[str, Dict[str, float]] = (
            {}
        )  # bot_name -> {action_hash: timestamp}
        self._cache_timeout = 5.0  # Actions expire after 5 seconds
        self._turn_sequence_tracking: Dict[str, int] = (
            {}
        )  # bot_name -> last_turn_number
        self._phase_sequence_tracking: Dict[str, str] = (
            {}
        )  # bot_name -> last_phase_context

        # 🔧 PHASE_TRACKING_FIX: Prevent duplicate phase action triggers
        self._last_processed_phase: Optional[str] = None
        self._phase_action_triggered: Dict[str, bool] = {}  # phase -> triggered

        # 🔧 TURN_START_FIX: Prevent duplicate turn_started events
        self._last_turn_start: Optional[Dict[str, Any]] = (
            None  # {turn_number, starter, timestamp}
        )

        # 🔧 REDEAL_DECISION_FIX: Track which bots have been triggered in current redeal cycle
        self._current_redeal_cycle_triggered: Set[str] = (
            set()
        )  # Bot names triggered this cycle

    def _get_game_state(self):
        """Get current game state from state machine or fallback to direct game access"""
        if self.state_machine:
            return self.state_machine.game  # Access game through state machine
        return self.game  # Fallback to direct access

    def _generate_action_hash(
        self, bot_name: str, action_type: str, context: dict
    ) -> str:
        """Generate a unique hash for a bot action to detect duplicates"""
        # Include bot name, action type, relevant context, and trigger source for uniqueness
        trigger_source = context.get("trigger_source", "unknown")
        context_str = f"{bot_name}:{action_type}:{context.get('turn_number', 0)}:{context.get('phase', '')}:{context.get('required_count', 'none')}:{trigger_source}"
        return hashlib.md5(context_str.encode()).hexdigest()[:12]

    def _is_duplicate_action(
        self, bot_name: str, action_type: str, context: dict
    ) -> bool:
        """Check if this bot action is a duplicate within the timeout window"""
        current_time = time.time()
        action_hash = self._generate_action_hash(bot_name, action_type, context)
        trigger_source = context.get("trigger_source", "unknown")
        current_player = context.get("current_player", "")

        # Initialize bot cache if needed
        if bot_name not in self._bot_action_cache:
            self._bot_action_cache[bot_name] = {}

        bot_cache = self._bot_action_cache[bot_name]

        # Clean expired actions first
        expired_hashes = [
            h
            for h, timestamp in bot_cache.items()
            if current_time - timestamp > self._cache_timeout
        ]
        for h in expired_hashes:
            del bot_cache[h]

        # 🔧 REFINED_FIX: Allow legitimate sequential triggers for current player
        # If this bot is the current player, allow sequential triggers from different sources
        if bot_name == current_player:
            # For current player, only block rapid triggers from the EXACT same source
            if action_hash in bot_cache:
                age = current_time - bot_cache[action_hash]
                if age < 0.5:  # Very recent same trigger
                    return True
                else:
                    pass
            else:
                pass
        else:
            # For non-current players, be more strict - block any recent duplicates
            # Check all recent actions regardless of source
            for existing_hash, timestamp in bot_cache.items():
                age = current_time - timestamp
                if age < 1.0:  # Any recent action within 1 second
                    return True

        # Record this action
        bot_cache[action_hash] = current_time
        return False

    def _should_skip_bot_trigger(self, bot_name: str, context: dict) -> bool:
        """Advanced logic to prevent duplicate bot triggers based on sequence tracking"""
        turn_number = context.get("turn_number", 0)
        phase = context.get("phase", "")
        phase_context = f"{phase}:{turn_number}:{context.get('current_player', '')}"

        # Check turn sequence - skip if bot already acted in this turn
        if bot_name in self._turn_sequence_tracking:
            last_turn = self._turn_sequence_tracking[bot_name]
            if last_turn == turn_number and phase == "turn":
                return True

        # Check phase sequence - skip if same phase context
        if bot_name in self._phase_sequence_tracking:
            last_context = self._phase_sequence_tracking[bot_name]
            if last_context == phase_context:
                return True

        # Update tracking
        if phase == "turn":
            self._turn_sequence_tracking[bot_name] = turn_number
        self._phase_sequence_tracking[bot_name] = phase_context

        return False

    async def handle_event(self, event: str, data: dict):
        """Process game events and trigger bot actions"""

        # 🔧 PHASE_TRACKING_FIX: Detect actual phase transitions and reset tracking
        if event == "phase_change":
            new_phase = data.get("phase")
            if new_phase != self._last_processed_phase:
                # Clear action tracking for new phase
                self._phase_action_triggered.clear()
                self._last_processed_phase = new_phase
            else:
                pass

        async with self._lock:  # Prevent concurrent bot actions
            if event == "player_declared":
                await self._handle_declaration_phase(data["player_name"])
            elif event == "phase_change":
                await self._handle_enterprise_phase_change(data)
            # 🚀 ENTERPRISE: Legacy player_played handler removed to prevent race condition
            # Enterprise architecture handles all bot triggering via phase_change events
            # elif event == "player_played":
            #     await self._handle_play_phase(data["player_name"])
            elif event == "turn_started":
                await self._handle_turn_start(data["starter"])
            elif event == "round_started":

                # 🔧 PHASE_TRACKING_FIX: Check if we already triggered actions for this phase
                current_phase = data.get("phase", "unknown")
                if (
                    current_phase in self._phase_action_triggered
                    and self._phase_action_triggered[current_phase]
                ):
                    return

                await self._handle_round_start()
            # 🔧 FIX: Add validation feedback events
            elif event == "action_rejected":
                await self._handle_action_rejected(data)
            elif event == "action_accepted":
                await self._handle_action_accepted(data)
            elif event == "action_failed":
                await self._handle_action_failed(data)

    async def _handle_enterprise_phase_change(self, data: dict):
        """
        🚀 ENTERPRISE: Handle automatic phase change events from enterprise broadcasting

        This implements the proper enterprise architecture where bot manager automatically
        reacts to phase data changes without manual calls from state machine.
        """
        phase = data.get("phase")
        phase_data = data.get("phase_data", {})
        reason = data.get("reason", "")

        # 🔧 PHASE_TRACKING_FIX: Check if we already triggered actions for this phase
        # EXCEPTION: Declaration phase allows multiple bot actions (each bot must declare)
        if (
            phase != "declaration"
            and phase in self._phase_action_triggered
            and self._phase_action_triggered[phase]
        ):
            return

        if phase == "declaration":
            current_declarer = data.get("current_declarer") or phase_data.get(
                "current_declarer"
            )
            if current_declarer:

                # Check if current declarer is a bot
                game_state = self._get_game_state()
                if hasattr(game_state, "players"):
                    for player in game_state.players:
                        if getattr(player, "name", str(player)) == current_declarer:
                            if getattr(player, "is_bot", False):
                                # 🔧 PHASE_TRACKING_FIX: Mark this phase as having triggered actions
                                self._phase_action_triggered[phase] = True
                                # Get last declarer to continue sequence
                                declarations = phase_data.get("declarations", {})
                                declared_players = list(declarations.keys())
                                last_declarer = (
                                    declared_players[-1] if declared_players else ""
                                )
                                try:
                                    await self._handle_declaration_phase(last_declarer)
                                except Exception as e:
                                    print(
                                        f"❌ BOT_MANAGER_ERROR: _handle_declaration_phase failed: {e}"
                                    )
                                    raise
                            else:
                                pass
                            break

        elif phase == "preparation":
            # Handle redeal decisions through phase data
            weak_players_awaiting = phase_data.get("weak_players_awaiting", set())
            if weak_players_awaiting:
                await self._handle_redeal_decision_phase(phase_data)

        elif phase == "turn":
            # 🚀 ENTERPRISE: Use sequential turn play handler like declarations
            # This ensures consistent delays for all bot plays (0.5-1.5s)
            turn_plays = phase_data.get("turn_plays", {})
            current_player = data.get("current_player") or phase_data.get(
                "current_player"
            )

            # If there are turn plays, find the last player who played
            if turn_plays:
                # Get the last player who played from turn_plays
                last_player = list(turn_plays.keys())[-1]
                # Use sequential handler for next bot(s)
                await self._handle_turn_play_phase(last_player)
            elif current_player:
                # No plays yet, but current player is set
                # Check if it's the turn starter (first play of the turn)
                if phase_data.get("current_turn_starter") == current_player:
                    # Start from beginning of turn order
                    await self._handle_turn_play_phase("")
                else:
                    # Find who played before current player
                    turn_order = phase_data.get("turn_order", [])
                    if current_player in turn_order:
                        curr_idx = turn_order.index(current_player)
                        if curr_idx > 0:
                            last_player = turn_order[curr_idx - 1]
                            await self._handle_turn_play_phase(last_player)

    async def _handle_declaration_phase(self, last_declarer: str):
        """Handle bot declarations in order"""
        from backend.socket_manager import broadcast

        # Get declaration order
        declaration_order = self._get_declaration_order()

        # Find next bot to declare
        last_index = self._get_player_index(last_declarer, declaration_order)

        # Get actual Player objects from game state
        game_state = self._get_game_state()

        for i in range(last_index + 1, len(declaration_order)):
            player_name = (
                declaration_order[i]
                if isinstance(declaration_order[i], str)
                else getattr(declaration_order[i], "name", str(declaration_order[i]))
            )

            # Find the actual Player object
            player_obj = None
            for p in game_state.players:
                if getattr(p, "name", str(p)) == player_name:
                    player_obj = p
                    break

            if not player_obj:
                continue

            if not getattr(player_obj, "is_bot", False):
                break  # Wait for human player

            # Check if player has already declared in current phase (use state machine data)
            phase_declarations = (
                self.state_machine.get_phase_data().get("declarations", {})
                if self.state_machine
                else {}
            )
            already_declared = player_name in phase_declarations
            declared_value = phase_declarations.get(player_name, 0)

            if already_declared:
                continue  # Already declared

            # Bot declares with random delay (500-1500ms for realism)
            import random

            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)

            try:
                await self._bot_declare(player_obj, i)
            except Exception as e:
                print(
                    f"❌ BOT_AI_ERROR: Bot AI declaration failed for {player_name}: {e}"
                )
                raise

            # Small delay for UI processing
            await asyncio.sleep(0.2)

    async def _bot_declare(self, bot: Player, position: int):
        """Make a bot declaration"""
        from backend.socket_manager import broadcast

        try:
            # Get previous declarations
            game_state = self._get_game_state()
            previous_declarations = [
                p.declared for p in game_state.players if p.declared != 0
            ]

            # Check if last player
            is_last = position == len(game_state.players) - 1

            # Calculate declaration
            try:
                value = ai.choose_declare(
                    hand=bot.hand,
                    is_first_player=(position == 0),
                    position_in_order=position,
                    previous_declarations=previous_declarations,
                    must_declare_nonzero=(bot.zero_declares_in_a_row >= 2),
                    verbose=False,
                )
            except Exception as e:
                print(f"❌ BOT_AI_ERROR: ai.choose_declare failed for {bot.name}: {e}")
                raise

            # Apply last player rule
            if is_last:
                game_state = self._get_game_state()
                total_so_far = sum(
                    p.declared for p in game_state.players if p.declared != 0
                )
                forbidden = 8 - total_so_far
                if value == forbidden and 0 <= forbidden <= 8:
                    print(f"⚠️ Bot {bot.name} cannot declare {value} (total would be 8)")
                    value = 1 if forbidden != 1 else 2

            # Apply declaration via state machine
            if self.state_machine:
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.DECLARE,
                    payload={"value": value},
                    is_bot=True,
                )
                result = await self.state_machine.handle_action(action)

                # Wait a moment for action to be fully processed
                await asyncio.sleep(0.05)
            else:
                # Fallback to direct game call
                result = self.game.declare(bot.name, value)

            if (
                result.get("status") == "ok"
                or result.get("success", False)
                or result.get("status") == "declaration_recorded"
            ):
                # 🚀 ENTERPRISE: State machine already handled broadcasting automatically
                # No manual broadcast needed - enterprise architecture handles this
                print(f"✅ Bot {bot.name} declared {value}")

                # Don't recursively call - let the declaration sequence complete naturally

        except Exception as e:
            print(f"❌ Bot {bot.name} declaration error: {e}")
            import traceback

            traceback.print_exc()
            # Fallback declaration
            try:
                if self.state_machine:
                    action = GameAction(
                        player_name=bot.name,
                        action_type=ActionType.DECLARE,
                        payload={"value": 1},
                        is_bot=True,
                    )
                    await self.state_machine.handle_action(action)
                else:
                    self.game.declare(bot.name, 1)
                # 🚀 ENTERPRISE: State machine already handled broadcasting automatically
                # No manual broadcast needed - enterprise architecture handles this
            except:
                pass

    async def _handle_round_start(self):
        """Handle start of a new round"""
        game_state = self._get_game_state()

        # Check if starter is a bot
        starter = game_state.current_order[0] if game_state.current_order else None
        if starter and starter.is_bot:
            print(f"🤖 Round starter is bot: {starter.name}")
            await asyncio.sleep(1)
            await self._handle_declaration_phase(
                ""
            )  # Empty string to start from beginning
        else:
            print(
                f"👤 Round starter is human or None: {starter.name if starter else 'None'}"
            )
            # Still need to handle bot declarations even if human starts
            await asyncio.sleep(0.5)
            await self._handle_declaration_phase("")  # Check for bot declarations

    async def _handle_turn_play_phase(self, last_player: str):
        """Handle bot plays in turn order - IDENTICAL to declaration pattern"""

        # Get turn order from phase data
        turn_order = self._get_turn_order()
        if not turn_order:
            return

        # Find next bot to play
        last_index = self._get_player_index(last_player, turn_order)

        if last_index >= len(turn_order) - 1:
            return

        # Get actual Player objects from game state
        game_state = self._get_game_state()

        # Loop through remaining players - EXACT SAME PATTERN as declarations
        for i in range(last_index + 1, len(turn_order)):
            player_name = turn_order[i]

            # Find the actual Player object
            player_obj = None
            for p in game_state.players:
                if getattr(p, "name", str(p)) == player_name:
                    player_obj = p
                    break

            if not player_obj:
                continue

            if not getattr(player_obj, "is_bot", False):
                break  # Stop at human player

            # Check if bot already played this turn (using phase data)
            if self.state_machine:
                phase_data = self.state_machine.get_phase_data()
                turn_plays = phase_data.get("turn_plays", {})
                if player_name in turn_plays:
                    continue

            # Bot plays with SAME delay as declarations (0.5-1.5s)
            import random

            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)

            try:
                await self._bot_play(player_obj)
            except Exception as e:
                print(f"❌ BOT_AI_ERROR: Bot AI play failed for {player_name}: {e}")
                import traceback

                traceback.print_exc()
                # Continue with next bot even if one fails
                continue

            # Small delay for UI processing
            await asyncio.sleep(0.2)

    async def _bot_play(self, bot: Player):
        """Make a bot play"""
        try:
            from backend.socket_manager import broadcast
        except ImportError:

            def broadcast(*args, **kwargs):
                pass

        try:
            # Choose play
            # Get required piece count from state machine if available
            if self.state_machine:
                phase_data = self.state_machine.get_phase_data()
                required_piece_count = phase_data.get("required_piece_count")
            else:
                # Fallback to game state
                game_state = self._get_game_state()
                required_piece_count = getattr(game_state, "required_piece_count", None)

            selected = ai.choose_best_play(
                bot.hand, required_count=required_piece_count, verbose=True
            )

            # Validate that bot respects required piece count
            if (
                required_piece_count is not None
                and len(selected) != required_piece_count
            ):
                # Force bot to select valid number of pieces
                if len(selected) > required_piece_count:
                    selected = selected[:required_piece_count]
                else:
                    # Add more pieces if needed (should not happen with proper AI)
                    remaining = [p for p in bot.hand if p not in selected]
                    selected.extend(remaining[: required_piece_count - len(selected)])

            # Get indices and play type
            indices = self._get_piece_indices(bot.hand, selected)
            from engine.rules import get_play_type

            play_type = get_play_type(selected) if selected else "UNKNOWN"

            # Make play via state machine
            if self.state_machine:
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={
                        "pieces": selected
                    },  # Send actual piece objects, not indices
                    is_bot=True,
                )
                result = await self.state_machine.handle_action(action)

                # Action is queued - state machine will process it and handle broadcasting
                print(
                    f"✅ Bot {bot.name} action queued - state machine will broadcast with correct next_player"
                )

                # Return early - state machine handles the rest
                return
            else:
                # Fallback to direct game call (no state machine)
                result = self.game.play_turn(bot.name, indices)

                # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically
                # All broadcasting is handled by enterprise architecture via update_phase_data()

            # Handle turn resolution if complete
            if result.get("status") == "resolved":
                await self._handle_turn_resolved(result)

        except Exception as e:
            print(f"❌ Bot {bot.name} play error: {e}")
            import traceback

            traceback.print_exc()

    async def _handle_redeal_decision_phase(self, phase_data: dict):
        """Handle bot redeal decisions one at a time - follows enterprise pattern"""
        weak_players_awaiting = phase_data.get("weak_players_awaiting", set())
        redeal_decisions = phase_data.get("redeal_decisions", {})
        decisions_received = phase_data.get("decisions_received", 0)

        # 🔧 REDEAL_DECISION_FIX: Detect new decision cycle
        if decisions_received == 0:
            self._current_redeal_cycle_triggered.clear()

        game_state = self._get_game_state()

        # Process one bot at a time, just like declarations and turns
        for player_name in weak_players_awaiting:
            # 🔧 REDEAL_DECISION_FIX: Skip if already triggered this cycle
            if player_name in self._current_redeal_cycle_triggered:
                continue

            if player_name in redeal_decisions:
                continue

            # Find the actual Player object
            player = None
            for p in game_state.players:
                if getattr(p, "name", str(p)) == player_name:
                    player = p
                    break

            if not player:
                continue

            if not getattr(player, "is_bot", False):
                continue

            # Bot decides with standard delay (0.5-1.5s)
            import random

            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)

            try:
                await self._bot_redeal_decision(player)
                # 🔧 REDEAL_DECISION_FIX: Mark bot as triggered for this cycle
                self._current_redeal_cycle_triggered.add(player_name)
            except Exception as e:
                print(
                    f"❌ BOT_AI_ERROR: Bot redeal decision failed for {player_name}: {e}"
                )
                import traceback

                traceback.print_exc()
                # Continue with next bot even if one fails
                continue

            # Small delay for UI processing
            await asyncio.sleep(0.2)

    async def _handle_turn_resolved(self, result: dict):
        """Handle end of turn"""
        from backend.socket_manager import broadcast

        # 🚀 ENTERPRISE: This should go through state machine, not manual broadcast
        # State machine automatically handles turn_resolved broadcasting via update_phase_data()
        # Check if round is complete
        game_state = self._get_game_state()
        if all(len(p.hand) == 0 for p in game_state.players):
            await self._handle_round_complete()
        elif result["winner"]:
            # Start next turn with winner
            await asyncio.sleep(0.5)
            await self._handle_turn_start(result["winner"])

    async def _handle_round_complete(self):
        """Handle round scoring"""
        from backend.socket_manager import broadcast

        from engine.win_conditions import get_winners, is_game_over

        # Handle scoring via state machine or fallback
        if self.state_machine:
            # State machine should handle scoring phase
            # For now, use game directly as state machine may not have scoring methods exposed
            summary = self.game.score_round()
            game_over = is_game_over(self.game)
            winners = get_winners(self.game) if game_over else []
        else:
            summary = self.game.score_round()
            game_over = is_game_over(self.game)
            winners = get_winners(self.game) if game_over else []

        # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically
        # All scoring broadcasts are handled by enterprise architecture via update_phase_data()

        if not game_over:
            # 🚀 ENTERPRISE: State machine handles round preparation automatically
            # No manual round preparation needed - transition to PREPARATION phase handles everything
            # The state machine's SCORING -> PREPARATION transition handles all round setup
            pass

    async def _handle_turn_start(self, starter_name: str):
        """Handle start of a new turn"""

        # 🔧 TURN_START_FIX: Check for duplicate turn_started events
        game_state = self._get_game_state()
        current_turn = getattr(game_state, "turn_number", 0)
        current_time = time.time()

        if self._last_turn_start:
            last_turn = self._last_turn_start.get("turn_number", -1)
            last_starter = self._last_turn_start.get("starter", "")
            last_time = self._last_turn_start.get("timestamp", 0)

            # If same turn and starter within 2 seconds, it's a duplicate
            if (
                last_turn == current_turn
                and last_starter == starter_name
                and (current_time - last_time) < 2.0
            ):
                return

        # Record this turn start
        self._last_turn_start = {
            "turn_number": current_turn,
            "starter": starter_name,
            "timestamp": current_time,
        }

        starter = (
            game_state.get_player(starter_name)
            if hasattr(game_state, "get_player")
            else None
        )
        if not starter:
            # Fallback: find player in players list
            starter = next(
                (p for p in game_state.players if p.name == starter_name), None
            )
        if not starter:
            print(f"❌ Starter {starter_name} not found")
            return

        # 🚀 ENTERPRISE: Use sequential turn play handler for ALL bot plays
        # This ensures consistent 0.5-1.5s delays for turn starters too

        # Start sequential processing from beginning of turn order
        # Empty string means start from index -1, so loop begins at index 0
        await self._handle_turn_play_phase("")

    async def _bot_play_first(self, bot: Player):
        """Bot plays as first player"""
        from backend.socket_manager import broadcast

        try:
            print(f"🤖 Bot {bot.name} choosing first play...")

            # Reset turn state (handled by state machine)
            # Note: State machine manages turn state internally

            # Choose play
            selected = ai.choose_best_play(bot.hand, required_count=None, verbose=True)
            indices = self._get_piece_indices(bot.hand, selected)

            # Get the play type for the selected pieces
            from engine.rules import get_play_type

            play_type = get_play_type(selected) if selected else "UNKNOWN"

            print(
                f"🤖 Bot {bot.name} will play {len(selected)} pieces: {[str(p) for p in selected]}"
            )

            # Make the play via state machine
            if self.state_machine:
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={
                        "pieces": selected
                    },  # Send actual piece objects, not indices
                    is_bot=True,
                )
                result = await self.state_machine.handle_action(action)

                # Action is queued - state machine will process it and handle broadcasting
                print(
                    f"✅ Bot {bot.name} first play action queued - state machine will broadcast with correct next_player"
                )

                # Return early - state machine handles the rest
                return
            else:
                # Fallback to direct game call (no state machine)
                result = self.game.play_turn(bot.name, indices)

                # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically
                # All broadcasting is handled by enterprise architecture via update_phase_data()

            print(f"✅ Bot {bot.name} played, status: {result.get('status')}")

            # If waiting for other players, trigger their plays
            if result.get("status") == "waiting":
                print(
                    f"🎯 Waiting for other players to respond with {len(selected)} pieces"
                )
                await asyncio.sleep(0.5)
                await self._handle_play_phase(bot.name)

        except Exception as e:
            print(f"❌ Bot {bot.name} first play error: {e}")
            import traceback

            traceback.print_exc()

    def _get_declaration_order(self) -> List[Player]:
        """Get players in declaration order"""
        if self.state_machine:
            # Get declaration order from state machine phase data
            phase_data = self.state_machine.get_phase_data()
            declaration_order = phase_data.get("declaration_order", [])
            return declaration_order
        else:
            # Fallback to game state
            game_state = self._get_game_state()
            return game_state.current_order

    def _get_turn_order(self) -> List[str]:
        """Get players in turn order - identical pattern to declaration order"""
        if self.state_machine:
            # Get turn order from state machine phase data
            phase_data = self.state_machine.get_phase_data()
            turn_order = phase_data.get("turn_order", [])
            return turn_order
        else:
            # Fallback to game state
            game_state = self._get_game_state()
            return getattr(game_state, "turn_order", [])

    def _get_player_index(self, player_name: str, order: List) -> int:
        """Find player index in order"""
        for i, p in enumerate(order):
            # Handle both Player objects and string names
            if hasattr(p, "name"):
                current_name = p.name
            else:
                current_name = str(p)

            if current_name == player_name:
                return i
        return -1

    def _get_piece_indices(self, hand: List, selected: List) -> List[int]:
        """Convert selected pieces to indices"""
        indices = []
        hand_copy = list(hand)
        for piece in selected:
            if piece in hand_copy:
                idx = hand_copy.index(piece)
                indices.append(idx)
                hand_copy[idx] = None  # Mark as used
        return indices

    async def _bot_redeal_decision(self, bot: Player):
        """Make bot redeal decision - uses standard pattern like declarations/turns"""
        # Bots always accept redeals for testing purposes
        # TODO: Add AI logic to make intelligent redeal decisions based on hand strength
        should_decline = False

        bot_name = bot.name
        print(
            f"🤖 Bot {bot_name} deciding: {'DECLINE' if should_decline else 'ACCEPT'} redeal"
        )

        # Send decision through state machine
        action = GameAction(
            player_name=bot_name,
            action_type=(
                ActionType.REDEAL_RESPONSE
                if should_decline
                else ActionType.REDEAL_REQUEST
            ),
            payload={"accept": not should_decline},
            is_bot=True,
        )

        try:
            await self.state_machine.handle_action(action)
            print(
                f"✅ Bot {bot_name} {'DECLINED' if should_decline else 'ACCEPTED'} redeal"
            )
        except Exception as e:
            print(f"❌ Bot {bot_name} redeal decision error: {e}")
            import traceback

            traceback.print_exc()

    # 🔧 FIX: Validation Feedback Event Handlers

    async def _handle_action_rejected(self, data: dict):
        """Handle notification that a bot action was rejected by state machine"""
        player_name = data.get("player_name")
        action_type = data.get("action_type")
        reason = data.get("reason", "Unknown reason")
        is_bot = data.get("is_bot", False)

        if is_bot:
            # For rejected bot actions, we need to:
            # 1. NOT process any turn completion logic
            # 2. NOT remove pieces from hands
            # 3. Clear tracking to allow retry with valid state

            # 🔧 RACE_CONDITION_FIX: Clear tracking for rejected actions to allow retry
            if player_name in self._bot_action_cache:
                # Clear recent action cache for this bot to allow legitimate retry
                self._bot_action_cache[player_name].clear()

            if player_name in self._turn_sequence_tracking:
                # Don't clear turn tracking - bot should not retry same turn
                pass

            if player_name in self._phase_sequence_tracking:
                # Clear phase tracking if it was an invalid attempt
                del self._phase_sequence_tracking[player_name]

            # Log the rejection for debugging
            game_state = self._get_game_state()
            if hasattr(game_state, "players"):
                for player in game_state.players:
                    if player.name == player_name:
                        break

    async def _handle_action_accepted(self, data: dict):
        """Handle notification that a bot action was accepted by state machine"""
        player_name = data.get("player_name")
        action_type = data.get("action_type")
        result = data.get("result", {})
        is_bot = data.get("is_bot", False)

        if is_bot and action_type == "play_pieces":
            # For accepted play actions, the state machine has already:
            # 1. Updated turn_plays with the valid play
            # 2. Advanced to next player
            # 3. Broadcast the play event
            # 4. Will handle piece removal during turn completion
            pass

    async def _handle_action_failed(self, data: dict):
        """Handle notification that a bot action failed during processing"""
        player_name = data.get("player_name")
        action_type = data.get("action_type")
        error = data.get("error", "Unknown error")
        is_bot = data.get("is_bot", False)

        if is_bot:
            # For failed bot actions, similar to rejection - prevent downstream processing
            pass
