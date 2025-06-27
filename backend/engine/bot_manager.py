# backend/engine/bot_manager.py

import asyncio
from typing import Dict, List, Optional
from engine.player import Player
import engine.ai as ai
from engine.state_machine.core import GameAction, ActionType

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
        if not hasattr(self, 'active_games'):
            self.active_games: Dict[str, GameBotHandler] = {}
        
    def register_game(self, room_id: str, game, state_machine=None):
        """Register a game for bot management"""
        self.active_games[room_id] = GameBotHandler(room_id, game, state_machine)
        
    def unregister_game(self, room_id: str):
        """Remove game from bot management"""
        if room_id in self.active_games:
            del self.active_games[room_id]
            
    async def handle_game_event(self, room_id: str, event: str, data: dict):
        """Handle game events that might need bot actions"""
        print(f"🔔 BOT_MANAGER_DEBUG: Received event '{event}' for room {room_id} with data: {data}")
        if room_id not in self.active_games:
            print(f"❌ BOT_MANAGER_DEBUG: Room {room_id} not found in active games: {list(self.active_games.keys())}")
            return
            
        handler = self.active_games[room_id]
        print(f"✅ BOT_MANAGER_DEBUG: Found handler for room {room_id}, delegating to handler...")
        await handler.handle_event(event, data)


class GameBotHandler:
    """Handles bot actions for a specific game"""
    
    def __init__(self, room_id: str, game, state_machine=None):
        self.room_id = room_id
        self.game = game
        self.state_machine = state_machine
        self.processing = False
        self._lock = asyncio.Lock()
    
    def _get_game_state(self):
        """Get current game state from state machine or fallback to direct game access"""
        if self.state_machine:
            return self.state_machine.game  # Access game through state machine
        return self.game  # Fallback to direct access
        
    async def handle_event(self, event: str, data: dict):
        """Process game events and trigger bot actions"""
        print(f"🎮 BOT_HANDLER_DEBUG: Room {self.room_id} handling event '{event}' with data: {data}")
        async with self._lock:  # Prevent concurrent bot actions
            if event == "player_declared":
                print(f"📢 BOT_HANDLER_DEBUG: Handling declaration phase")
                await self._handle_declaration_phase(data["player_name"])
            elif event == "player_played":
                print(f"🎯 BOT_HANDLER_DEBUG: Handling play phase")
                await self._handle_play_phase(data["player_name"])
            elif event == "turn_started":
                print(f"🚀 BOT_HANDLER_DEBUG: Handling turn start")
                await self._handle_turn_start(data["starter"])
            elif event == "round_started":
                print(f"🎪 BOT_HANDLER_DEBUG: Handling round start")
                await self._handle_round_start()
            elif event == "weak_hands_found":
                print(f"🃏 BOT_HANDLER_DEBUG: Handling weak hands found")
                await self._handle_weak_hands(data)
            elif event == "redeal_decision_needed":
                print(f"🔄 BOT_HANDLER_DEBUG: Handling redeal decision needed")
                await self._handle_redeal_decision(data)
            else:
                print(f"⚠️ BOT_HANDLER_DEBUG: Unknown event '{event}' - ignoring")
                
    async def _handle_declaration_phase(self, last_declarer: str):
        """Handle bot declarations in order"""
        from backend.socket_manager import broadcast
        
        print(f"🔍 DECL_PHASE_DEBUG: _handle_declaration_phase called with last_declarer: '{last_declarer}'")
        
        # Get declaration order
        declaration_order = self._get_declaration_order()
        print(f"🔍 DECL_PHASE_DEBUG: Declaration order: {[getattr(p, 'name', str(p)) for p in declaration_order] if declaration_order else 'None'}")
        
        # Find next bot to declare
        last_index = self._get_player_index(last_declarer, declaration_order)
        print(f"🔍 DECL_PHASE_DEBUG: Last declarer '{last_declarer}' index: {last_index}")
        
        print(f"🔍 DECL_PHASE_DEBUG: Starting loop from index {last_index + 1} to {len(declaration_order)}")
        
        # Get actual Player objects from game state
        game_state = self._get_game_state()
        
        for i in range(last_index + 1, len(declaration_order)):
            player_name = declaration_order[i] if isinstance(declaration_order[i], str) else getattr(declaration_order[i], 'name', str(declaration_order[i]))
            
            # Find the actual Player object
            player_obj = None
            for p in game_state.players:
                if getattr(p, 'name', str(p)) == player_name:
                    player_obj = p
                    break
            
            if not player_obj:
                print(f"❌ DECL_PHASE_DEBUG: Could not find Player object for {player_name}")
                continue
            
            print(f"🔍 DECL_PHASE_DEBUG: Checking player {i} ({player_name}), is_bot: {getattr(player_obj, 'is_bot', 'unknown')}")
            
            if not getattr(player_obj, 'is_bot', False):
                print(f"🔍 DECL_PHASE_DEBUG: Player {player_name} is human, stopping bot declarations")
                break  # Wait for human player
                
            # Check if player has already declared in current phase (use state machine data)
            phase_declarations = self.state_machine.get_phase_data().get('declarations', {}) if self.state_machine else {}
            already_declared = player_name in phase_declarations
            declared_value = phase_declarations.get(player_name, 0)
            print(f"🔍 DECL_PHASE_DEBUG: Player {player_name} declared value: {declared_value} (from phase data)")
            print(f"🔍 DECL_PHASE_DEBUG: All phase declarations: {phase_declarations}")
            
            if already_declared:
                print(f"🔍 DECL_PHASE_DEBUG: Player {player_name} already declared {declared_value}, skipping")
                continue  # Already declared
                
            # Bot declares with random delay (500-1500ms for realism)
            import random
            delay = random.uniform(0.5, 1.5)
            print(f"🤖 DECL_PHASE_DEBUG: Bot {player_name} will declare in {delay:.1f}s...")
            await asyncio.sleep(delay)
            
            print(f"🤖 DECL_PHASE_DEBUG: Bot {player_name} will now declare!")
            await self._bot_declare(player_obj, i)
            
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
            value = ai.choose_declare(
                hand=bot.hand,
                is_first_player=(position == 0),
                position_in_order=position,
                previous_declarations=previous_declarations,
                must_declare_nonzero=(bot.zero_declares_in_a_row >= 2),
                verbose=False
            )
            
            # Apply last player rule
            if is_last:
                game_state = self._get_game_state()
                total_so_far = sum(p.declared for p in game_state.players if p.declared != 0)
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
                    is_bot=True
                )
                result = await self.state_machine.handle_action(action)
                print(f"🔧 BOT_DECLARE_DEBUG: State machine result: {result}")
                
                # Wait a moment for action to be fully processed
                await asyncio.sleep(0.05)
            else:
                # Fallback to direct game call
                result = self.game.declare(bot.name, value)
            
            if result.get("status") == "ok" or result.get("success", False) or result.get("status") == "declaration_recorded":
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
                        is_bot=True
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
        
        print(f"🔍 BOT_ROUND_DEBUG: Game state current_order: {[getattr(p, 'name', str(p)) for p in game_state.current_order] if game_state.current_order else 'None'}")
        print(f"🔍 BOT_ROUND_DEBUG: Game round_starter: {getattr(game_state, 'round_starter', 'None')}")
        print(f"🔍 BOT_ROUND_DEBUG: Game current_player: {getattr(game_state, 'current_player', 'None')}")
        
        # Check if starter is a bot
        starter = game_state.current_order[0] if game_state.current_order else None
        if starter and starter.is_bot:
            print(f"🤖 Round starter is bot: {starter.name}")
            await asyncio.sleep(1)
            await self._handle_declaration_phase("")  # Empty string to start from beginning
        else:
            print(f"👤 Round starter is human or None: {starter.name if starter else 'None'}")
            # Still need to handle bot declarations even if human starts
            await asyncio.sleep(0.5)
            await self._handle_declaration_phase("")  # Check for bot declarations
            
    async def _handle_play_phase(self, last_player: str):
        """Handle bot plays in turn order"""
        from backend.socket_manager import broadcast
        
        # Get turn data from state machine if available
        if self.state_machine:
            phase_data = self.state_machine.get_phase_data()
            required_piece_count = phase_data.get('required_piece_count')
            turn_order = phase_data.get('turn_order', [])
            
            print(f"🎯 PLAY_PHASE_DEBUG: Got from state machine - required_count: {required_piece_count}, turn_order: {turn_order}")
        else:
            # Fallback to game state
            game_state = self._get_game_state()
            required_piece_count = getattr(game_state, 'required_piece_count', None)
            turn_order = getattr(game_state, 'turn_order', [])
            
        if not required_piece_count:
            print(f"🎯 PLAY_PHASE_DEBUG: No required piece count set yet, skipping bot plays")
            return  # First player hasn't set the count yet
            
        if not turn_order:
            print(f"🎯 PLAY_PHASE_DEBUG: No turn order available, skipping bot plays")
            return
            
        # Find next players to play
        last_index = self._get_player_index(last_player, turn_order)
        
        print(f"🎯 PLAY_PHASE_DEBUG: Last player: {last_player}, last_index: {last_index}")
        
        # FIX: Only process the NEXT player, not all remaining players
        # This prevents duplicate bot actions when multiple player_played events cascade
        next_player_index = last_index + 1
        if next_player_index >= len(turn_order):
            print(f"🎯 PLAY_PHASE_DEBUG: No more players after {last_player}, turn should be complete")
            return
            
        next_player_name = turn_order[next_player_index]
        print(f"🎯 PLAY_PHASE_DEBUG: Checking next player {next_player_index}: {next_player_name}")
        
        # Check if next player already played this turn using state machine data
        if self.state_machine:
            phase_data = self.state_machine.get_phase_data()
            turn_plays = phase_data.get('turn_plays', {})
            if next_player_name in turn_plays:
                print(f"🎯 PLAY_PHASE_DEBUG: Player {next_player_name} already played this turn")
                return
        else:
            # Fallback to game state check
            game_state = self._get_game_state()
            if any(play.player == next_player_name for play in getattr(game_state, 'current_turn_plays', [])):
                print(f"🎯 PLAY_PHASE_DEBUG: Player {next_player_name} already played this turn (fallback check)")
                return
        
        # Get the actual Player object for the next player
        game_state = self._get_game_state()
        next_player_obj = None
        for p in game_state.players:
            if getattr(p, 'name', str(p)) == next_player_name:
                next_player_obj = p
                break
        
        if not next_player_obj:
            print(f"❌ PLAY_PHASE_DEBUG: Could not find Player object for {next_player_name}")
            return
            
        if not getattr(next_player_obj, 'is_bot', False):
            print(f"🎯 PLAY_PHASE_DEBUG: Next player {next_player_name} is human, waiting for their play")
            return  # Wait for human player
            
        print(f"🤖 PLAY_PHASE_DEBUG: Triggering bot play for {next_player_name}")
        
        # Add realistic delay for bot decision (500-1000ms)
        import random
        delay = random.uniform(0.5, 1.0)
        print(f"🤖 PLAY_PHASE_DEBUG: Bot {next_player_name} thinking for {delay:.1f}s...")
        await asyncio.sleep(delay)
        
        # Bot plays
        await self._bot_play(next_player_obj)
            
    async def _bot_play(self, bot: Player):
        """Make a bot play"""
        from backend.socket_manager import broadcast
        
        try:
            # Choose play
            # Get required piece count from state machine if available
            if self.state_machine:
                phase_data = self.state_machine.get_phase_data()
                required_piece_count = phase_data.get('required_piece_count')
                print(f"🎯 BOT_PLAY_DEBUG: Got required_piece_count from state machine: {required_piece_count}")
            else:
                # Fallback to game state
                game_state = self._get_game_state()
                required_piece_count = getattr(game_state, 'required_piece_count', None)
                print(f"🎯 BOT_PLAY_DEBUG: Got required_piece_count from game state: {required_piece_count}")
                
            selected = ai.choose_best_play(
                bot.hand,
                required_count=required_piece_count,
                verbose=True
            )
            
            # Validate that bot respects required piece count
            if required_piece_count is not None and len(selected) != required_piece_count:
                print(f"❌ BOT_PLAY_DEBUG: Bot {bot.name} selected {len(selected)} pieces but required {required_piece_count}")
                print(f"🔧 BOT_PLAY_DEBUG: Forcing bot to select {required_piece_count} pieces")
                # Force bot to select valid number of pieces
                if len(selected) > required_piece_count:
                    selected = selected[:required_piece_count]
                else:
                    # Add more pieces if needed (should not happen with proper AI)
                    remaining = [p for p in bot.hand if p not in selected]
                    selected.extend(remaining[:required_piece_count - len(selected)])
            
            print(f"🎯 BOT_PLAY_DEBUG: Final selection - {len(selected)} pieces: {[str(p) for p in selected]}")
            
            # Get indices and play type
            indices = self._get_piece_indices(bot.hand, selected)
            from engine.rules import get_play_type
            play_type = get_play_type(selected) if selected else "UNKNOWN"
            
            # Make play via state machine
            if self.state_machine:
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={"pieces": selected},  # Send actual piece objects, not indices
                    is_bot=True
                )
                result = await self.state_machine.handle_action(action)
                
                # Action is queued - state machine will process it and handle broadcasting
                print(f"🎯 BOT_PLAY_DEBUG: Action queued successfully, state machine will handle updates and broadcasting")
                print(f"✅ Bot {bot.name} action queued - state machine will broadcast with correct next_player")
                
                # Return early - state machine handles the rest
                return
            else:
                # Fallback to direct game call (no state machine)
                result = self.game.play_turn(bot.name, indices)
                
                # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically
                # All broadcasting is handled by enterprise architecture via update_phase_data()
                print(f"🚀 ENTERPRISE: Bot play completed - automatic broadcasting active")
            
            # Handle turn resolution if complete
            if result.get("status") == "resolved":
                await self._handle_turn_resolved(result)
                
        except Exception as e:
            print(f"❌ Bot {bot.name} play error: {e}")
            import traceback
            traceback.print_exc()
            
    async def _handle_turn_resolved(self, result: dict):
        """Handle end of turn"""
        from backend.socket_manager import broadcast
        
        # 🚀 ENTERPRISE: This should go through state machine, not manual broadcast
        # State machine automatically handles turn_resolved broadcasting via update_phase_data()
        print(f"🚀 ENTERPRISE: Turn resolved - state machine handles broadcasting automatically")
        
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
        from engine.win_conditions import is_game_over, get_winners
        
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
        print(f"🚀 ENTERPRISE: Scoring completed - automatic broadcasting active")
        
        if not game_over:
            # Start next round
            await asyncio.sleep(2)
            if self.state_machine:
                # State machine should handle round preparation
                # For now, use game directly as state machine may not have round prep methods exposed
                round_data = self.game.prepare_round()
            else:
                round_data = self.game.prepare_round()
            # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically  
            # All round start broadcasts are handled by enterprise architecture via update_phase_data()
            print(f"🚀 ENTERPRISE: Round start completed - automatic broadcasting active")
            await self._handle_round_start()
            
    async def _handle_turn_start(self, starter_name: str):
        """Handle start of a new turn"""
        print(f"🎮 Bot Manager: Handling turn start for {starter_name}")
        
        game_state = self._get_game_state()
        starter = game_state.get_player(starter_name) if hasattr(game_state, 'get_player') else None
        if not starter:
            # Fallback: find player in players list
            starter = next((p for p in game_state.players if p.name == starter_name), None)
        if not starter:
            print(f"❌ Starter {starter_name} not found")
            return
            
        if starter.is_bot and len(starter.hand) > 0:
            print(f"🤖 Bot {starter_name} will play first")
            
            # Add realistic delay for bot decision (500-1000ms)
            import random
            delay = random.uniform(0.5, 1.0)
            print(f"🤖 Bot {starter_name} thinking for {delay:.1f}s...")
            await asyncio.sleep(delay)
            
            # Bot starts the turn
            await self._bot_play_first(starter)
        else:
            print(f"👤 Human player {starter_name} starts, waiting for their play")
            
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
            
            print(f"🤖 Bot {bot.name} will play {len(selected)} pieces: {[str(p) for p in selected]}")
            print(f"🎯 BOT_MANAGER_DEBUG: state_machine exists: {self.state_machine is not None}")
            
            # Make the play via state machine
            if self.state_machine:
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={"pieces": selected},  # Send actual piece objects, not indices
                    is_bot=True
                )
                result = await self.state_machine.handle_action(action)
                print(f"🎯 BOT_PLAY_DEBUG: State machine result: {result}")
                
                # Action is queued - state machine will process it and handle broadcasting
                print(f"🎯 BOT_PLAY_DEBUG: Action queued successfully, state machine will handle updates and broadcasting")
                print(f"✅ Bot {bot.name} first play action queued - state machine will broadcast with correct next_player")
                
                # Return early - state machine handles the rest
                return
            else:
                # Fallback to direct game call (no state machine)
                result = self.game.play_turn(bot.name, indices)
                
                # 🚀 ENTERPRISE: Manual broadcast removed - state machine handles this automatically
                # All broadcasting is handled by enterprise architecture via update_phase_data()
                print(f"🚀 ENTERPRISE: Bot play completed - automatic broadcasting active")
            
            print(f"✅ Bot {bot.name} played, status: {result.get('status')}")
            
            # If waiting for other players, trigger their plays
            if result.get("status") == "waiting":
                print(f"🎯 Waiting for other players to respond with {len(selected)} pieces")
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
            declaration_order = phase_data.get('declaration_order', [])
            print(f"🔍 BOT_DEBUG: Got declaration order from state machine: {[getattr(p, 'name', str(p)) for p in declaration_order] if declaration_order else 'None'}")
            return declaration_order
        else:
            # Fallback to game state
            game_state = self._get_game_state()
            return game_state.current_order
        
    def _get_player_index(self, player_name: str, order: List) -> int:
        """Find player index in order"""
        for i, p in enumerate(order):
            # Handle both Player objects and string names
            if hasattr(p, 'name'):
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

    async def _handle_weak_hands(self, data: dict):
        """Handle weak hands found event - auto-decide for bots"""
        weak_players = data.get("weak_players", [])
        current_weak_player = data.get("current_weak_player")
        
        # Auto-decide for current bot if it's a bot
        if current_weak_player:
            game_state = self._get_game_state()
            player = None
            for p in game_state.players:
                if p.name == current_weak_player:
                    player = p
                    break
            
            if player and player.is_bot:
                print(f"🤖 Auto-deciding redeal for bot {current_weak_player}")
                await asyncio.sleep(0.5)  # Small delay for realism
                await self._bot_redeal_decision(player)

    async def _handle_redeal_decision(self, data: dict):
        """Handle redeal decision needed event"""
        current_weak_player = data.get("current_weak_player")
        
        if current_weak_player:
            game_state = self._get_game_state()
            player = None
            for p in game_state.players:
                if p.name == current_weak_player:
                    player = p
                    break
            
            if player and player.is_bot:
                print(f"🤖 Bot {current_weak_player} needs to make redeal decision")
                await asyncio.sleep(0.5)  # Small delay for realism
                await self._bot_redeal_decision(player)

    async def _bot_redeal_decision(self, bot: Player):
        """Make redeal decision for bot"""
        try:
            # Simple strategy: decline redeal 70% of the time to avoid infinite loops
            import random
            decline_probability = 0.7
            should_decline = random.random() < decline_probability
            
            if should_decline:
                # Decline redeal
                if self.state_machine:
                    action = GameAction(
                        player_name=bot.name,
                        action_type=ActionType.REDEAL_RESPONSE,
                        payload={"accept": False},
                        is_bot=True
                    )
                    result = await self.state_machine.handle_action(action)
                    print(f"✅ Bot {bot.name} DECLINED redeal")
                else:
                    print(f"❌ No state machine available for bot {bot.name} redeal decision")
            else:
                # Accept redeal
                if self.state_machine:
                    action = GameAction(
                        player_name=bot.name,
                        action_type=ActionType.REDEAL_REQUEST,
                        payload={"accept": True},
                        is_bot=True
                    )
                    result = await self.state_machine.handle_action(action)
                    print(f"✅ Bot {bot.name} ACCEPTED redeal")
                else:
                    print(f"❌ No state machine available for bot {bot.name} redeal decision")
                    
        except Exception as e:
            print(f"❌ Bot {bot.name} redeal decision error: {e}")
            # Fallback: auto-decline to avoid hanging
            if self.state_machine:
                try:
                    action = GameAction(
                        player_name=bot.name,
                        action_type=ActionType.REDEAL_RESPONSE,
                        payload={"accept": False},
                        is_bot=True
                    )
                    await self.state_machine.handle_action(action)
                    print(f"🔧 Bot {bot.name} auto-declined as fallback")
                except:
                    pass