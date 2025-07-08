# backend/engine/bot_manager.py

import asyncio
import time
import hashlib
import random
from typing import Dict, List, Optional, Set
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
        self._bot_action_cache: Dict[str, Dict[str, float]] = {}  # bot_name -> {action_hash: timestamp}
        self._cache_timeout = 5.0  # Actions expire after 5 seconds
        self._turn_sequence_tracking: Dict[str, int] = {}  # bot_name -> last_turn_number
        self._phase_sequence_tracking: Dict[str, str] = {}  # bot_name -> last_phase_context
        
        # 🔧 PHASE_TRACKING_FIX: Prevent duplicate phase action triggers
        self._last_processed_phase: Optional[str] = None
        self._phase_action_triggered: Dict[str, bool] = {}  # phase -> triggered
        
        # 🔧 TURN_START_FIX: Prevent duplicate turn_started events
        self._last_turn_start: Optional[Dict[str, Any]] = None  # {turn_number, starter, timestamp}
    
    def _get_game_state(self):
        """Get current game state from state machine or fallback to direct game access"""
        if self.state_machine:
            return self.state_machine.game  # Access game through state machine
        return self.game  # Fallback to direct access
    
    def _generate_action_hash(self, bot_name: str, action_type: str, context: dict) -> str:
        """Generate a unique hash for a bot action to detect duplicates"""
        # Include bot name, action type, relevant context, and trigger source for uniqueness
        trigger_source = context.get('trigger_source', 'unknown')
        context_str = f"{bot_name}:{action_type}:{context.get('turn_number', 0)}:{context.get('phase', '')}:{context.get('required_count', 'none')}:{trigger_source}"
        return hashlib.md5(context_str.encode()).hexdigest()[:12]
    
    def _is_duplicate_action(self, bot_name: str, action_type: str, context: dict) -> bool:
        """Check if this bot action is a duplicate within the timeout window"""
        current_time = time.time()
        action_hash = self._generate_action_hash(bot_name, action_type, context)
        trigger_source = context.get('trigger_source', 'unknown')
        current_player = context.get('current_player', '')
        
        # Initialize bot cache if needed
        if bot_name not in self._bot_action_cache:
            self._bot_action_cache[bot_name] = {}
        
        bot_cache = self._bot_action_cache[bot_name]
        
        # Clean expired actions first
        expired_hashes = [h for h, timestamp in bot_cache.items() if current_time - timestamp > self._cache_timeout]
        for h in expired_hashes:
            del bot_cache[h]
        
        # 🔧 REFINED_FIX: Allow legitimate sequential triggers for current player
        # If this bot is the current player, allow sequential triggers from different sources
        if bot_name == current_player:
            # For current player, only block rapid triggers from the EXACT same source
            if action_hash in bot_cache:
                age = current_time - bot_cache[action_hash]
                if age < 0.5:  # Very recent same trigger
                    print(f"🚫 REFINED_FIX: Blocking rapid same-source trigger for current player {bot_name} from {trigger_source} (age: {age:.1f}s)")
                    return True
                else:
                    print(f"✅ REFINED_FIX: Allowing delayed same-source trigger for current player {bot_name} from {trigger_source} (age: {age:.1f}s)")
            else:
                print(f"✅ REFINED_FIX: Allowing new trigger for current player {bot_name} from {trigger_source}")
        else:
            # For non-current players, be more strict - block any recent duplicates
            # Check all recent actions regardless of source
            for existing_hash, timestamp in bot_cache.items():
                age = current_time - timestamp
                if age < 1.0:  # Any recent action within 1 second
                    print(f"🚫 REFINED_FIX: Blocking non-current player {bot_name} trigger (recent action age: {age:.1f}s)")
                    return True
            
            print(f"✅ REFINED_FIX: Allowing trigger for non-current player {bot_name} from {trigger_source}")
        
        
        # Record this action
        bot_cache[action_hash] = current_time
        print(f"✅ RACE_CONDITION_FIX: New action recorded for {bot_name} - {action_type} from {trigger_source} (hash: {action_hash})")
        return False
    
    def _should_skip_bot_trigger(self, bot_name: str, context: dict) -> bool:
        """Advanced logic to prevent duplicate bot triggers based on sequence tracking"""
        turn_number = context.get('turn_number', 0)
        phase = context.get('phase', '')
        phase_context = f"{phase}:{turn_number}:{context.get('current_player', '')}"
        
        # Check turn sequence - skip if bot already acted in this turn
        if bot_name in self._turn_sequence_tracking:
            last_turn = self._turn_sequence_tracking[bot_name]
            if last_turn == turn_number and phase == 'turn':
                print(f"🚫 SEQUENCE_FIX: {bot_name} already acted in turn {turn_number} - skipping")
                return True
        
        # Check phase sequence - skip if same phase context
        if bot_name in self._phase_sequence_tracking:
            last_context = self._phase_sequence_tracking[bot_name]
            if last_context == phase_context:
                print(f"🚫 SEQUENCE_FIX: {bot_name} already processed phase context '{phase_context}' - skipping")
                return True
        
        # Update tracking
        if phase == 'turn':
            self._turn_sequence_tracking[bot_name] = turn_number
        self._phase_sequence_tracking[bot_name] = phase_context
        
        return False
        
    async def handle_event(self, event: str, data: dict):
        """Process game events and trigger bot actions"""
        
        # 🔧 PHASE_TRACKING_FIX: Detect actual phase transitions and reset tracking
        if event == "phase_change":
            new_phase = data.get("phase")
            if new_phase != self._last_processed_phase:
                print(f"🔄 PHASE_TRACKING_FIX: New phase detected {self._last_processed_phase} -> {new_phase}")
                # Clear action tracking for new phase
                self._phase_action_triggered.clear()
                self._last_processed_phase = new_phase
            else:
                print(f"🔍 PHASE_TRACKING_FIX: Same phase update: {new_phase}")
        
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
                print(f"🔍 DUPLICATE_DEBUG: Received turn_started event for {data.get('starter')} from {data.get('source', 'unknown')}")
                await self._handle_turn_start(data["starter"])
            elif event == "round_started":
                
                # 🔧 PHASE_TRACKING_FIX: Check if we already triggered actions for this phase
                current_phase = data.get("phase", "unknown")
                if current_phase in self._phase_action_triggered and self._phase_action_triggered[current_phase]:
                    print(f"🚫 PHASE_TRACKING_FIX: Already triggered actions for {current_phase} phase via round_started - skipping")
                    return
                
                await self._handle_round_start()
            elif event == "weak_hands_found":
                await self._handle_weak_hands(data)
            elif event == "redeal_decision_needed":
                print(f"🔄 BOT_HANDLER_DEBUG: Handling redeal decision needed")
                await self._handle_redeal_decision(data)
            elif event == "simultaneous_redeal_decisions":
                print(f"🔄 BOT_HANDLER_DEBUG: Handling simultaneous redeal decisions")
                await self._handle_simultaneous_redeal_decisions(data)
            # 🔧 FIX: Add validation feedback events
            elif event == "action_rejected":
                print(f"🚫 BOT_HANDLER_DEBUG: Handling action rejection")
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
        if phase != "declaration" and phase in self._phase_action_triggered and self._phase_action_triggered[phase]:
            print(f"🚫 PHASE_TRACKING_FIX: Already triggered actions for {phase} phase - skipping")
            return
        
        if phase == "declaration":
            current_declarer = data.get("current_declarer") or phase_data.get("current_declarer")
            if current_declarer:
                
                # Check if current declarer is a bot
                game_state = self._get_game_state()
                if hasattr(game_state, 'players'):
                    for player in game_state.players:
                        if getattr(player, 'name', str(player)) == current_declarer:
                            if getattr(player, 'is_bot', False):
                                # 🔧 PHASE_TRACKING_FIX: Mark this phase as having triggered actions
                                self._phase_action_triggered[phase] = True
                                print(f"✅ PHASE_TRACKING_FIX: Marked {phase} phase as triggered")
                                # Get last declarer to continue sequence
                                declarations = phase_data.get('declarations', {})
                                declared_players = list(declarations.keys())
                                last_declarer = declared_players[-1] if declared_players else ""
                                try:
                                    await self._handle_declaration_phase(last_declarer)
                                except Exception as e:
                                    print(f"❌ BOT_MANAGER_ERROR: _handle_declaration_phase failed: {e}")
                                    raise
                            else:
                                print(f"👤 ENTERPRISE_BOT_DEBUG: Current declarer {current_declarer} is human - waiting")
                            break
                            
        elif phase == "turn":
            current_player = data.get("current_player") or phase_data.get("current_player")
            if current_player:
                print(f"🚀 ENTERPRISE_BOT_DEBUG: Turn phase - checking if {current_player} is a bot")
                
                # Check if current player is a bot
                game_state = self._get_game_state()
                if hasattr(game_state, 'players'):
                    for player in game_state.players:
                        if getattr(player, 'name', str(player)) == current_player:
                            if getattr(player, 'is_bot', False):
                                print(f"🤖 ENTERPRISE_BOT_DEBUG: Current player {current_player} is a bot - checking for duplicates")
                                
                                # 🔧 RACE_CONDITION_FIX: Check for duplicate action before triggering
                                context = {
                                    'phase': phase,
                                    'turn_number': phase_data.get('current_turn_number', 0),
                                    'current_player': current_player,
                                    'required_count': phase_data.get('required_piece_count'),
                                    'trigger_source': 'phase_change'
                                }
                                
                                # Check both deduplication mechanisms
                                if self._is_duplicate_action(current_player, 'play_pieces', context):
                                    print(f"🚫 RACE_CONDITION_FIX: Skipping duplicate play action for {current_player}")
                                    return
                                
                                if self._should_skip_bot_trigger(current_player, context):
                                    print(f"🚫 RACE_CONDITION_FIX: Skipping bot trigger due to sequence tracking for {current_player}")
                                    return
                                
                                # 🚀 ENTERPRISE: Check if this is a new turn start (bot already triggered by turn_started event)
                                turn_plays = phase_data.get('turn_plays', {})
                                if not turn_plays or len(turn_plays) == 0:
                                    print(f"🚫 RACE_CONDITION_FIX: Skipping enterprise trigger for {current_player} - turn starter already triggered by turn_started event")
                                    return
                                
                                print(f"✅ RACE_CONDITION_FIX: Triggering bot play for {current_player} - no duplicates detected")
                                
                                # 🚀 ENTERPRISE: Direct bot triggering for current player (single-source triggering)
                                await self._bot_play(player)
                            else:
                                print(f"👤 ENTERPRISE_BOT_DEBUG: Current player {current_player} is human - waiting")
                            break
                
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
            try:
                await self._bot_declare(player_obj, i)
            except Exception as e:
                print(f"❌ BOT_AI_ERROR: Bot AI declaration failed for {player_name}: {e}")
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
                    verbose=False
                )
            except Exception as e:
                print(f"❌ BOT_AI_ERROR: ai.choose_declare failed for {bot.name}: {e}")
                raise
            
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
        try:
            from backend.socket_manager import broadcast
        except ImportError:
            # Handle test environment
            def broadcast(*args, **kwargs):
                pass
        
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
            
        # 🔧 RACE_CONDITION_FIX: Additional deduplication check before bot play
        if self.state_machine:
            phase_data = self.state_machine.get_phase_data()
            context = {
                'phase': 'turn',
                'turn_number': phase_data.get('current_turn_number', 0),
                'current_player': next_player_name,
                'required_count': required_piece_count,
                'trigger_source': 'player_played'
            }
            
            if self._is_duplicate_action(next_player_name, 'play_pieces', context):
                print(f"🚫 RACE_CONDITION_FIX: Skipping duplicate bot play for {next_player_name} in _handle_play_phase")
                return
        
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
        
        if not game_over:
            # 🚀 ENTERPRISE: State machine handles round preparation automatically
            # No manual round preparation needed - transition to PREPARATION phase handles everything
            # The state machine's SCORING -> PREPARATION transition handles all round setup
            pass
    async def _handle_turn_start(self, starter_name: str):
        """Handle start of a new turn"""
        
        # 🔧 TURN_START_FIX: Check for duplicate turn_started events
        game_state = self._get_game_state()
        current_turn = getattr(game_state, 'turn_number', 0)
        current_time = time.time()
        
        if self._last_turn_start:
            last_turn = self._last_turn_start.get('turn_number', -1)
            last_starter = self._last_turn_start.get('starter', '')
            last_time = self._last_turn_start.get('timestamp', 0)
            
            # If same turn and starter within 2 seconds, it's a duplicate
            if last_turn == current_turn and last_starter == starter_name and (current_time - last_time) < 2.0:
                print(f"🚫 TURN_START_FIX: Skipping duplicate turn_started event for {starter_name} turn {current_turn}")
                return
        
        # Record this turn start
        self._last_turn_start = {
            'turn_number': current_turn,
            'starter': starter_name,
            'timestamp': current_time
        }
        
        starter = game_state.get_player(starter_name) if hasattr(game_state, 'get_player') else None
        if not starter:
            # Fallback: find player in players list
            starter = next((p for p in game_state.players if p.name == starter_name), None)
        if not starter:
            print(f"❌ Starter {starter_name} not found")
            return
            
        if starter.is_bot and len(starter.hand) > 0:
            print(f"🤖 Bot {starter_name} will play first")
            
            # Add realistic delay for bot decision if the starter is a bot
            import random
            delay = random.uniform(1.0, 2.0)
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
                # Use consolidated method with small delay for sequential decisions
                await self._delayed_bot_redeal_decision(current_weak_player, 0.5)


    async def _handle_simultaneous_redeal_decisions(self, data: dict):
        """Handle multiple bot redeal decisions with realistic timing"""
        bot_weak_players = data.get("bot_weak_players", [])
        
        if not bot_weak_players:
            print(f"👤 No bot weak players to handle")
            return
        
        print(f"🤖 SIMULTANEOUS_REDEAL: Handling {len(bot_weak_players)} bot decisions: {bot_weak_players}")
        
        # Create staggered delays for natural feel
        bot_tasks = []
        for i, bot_name in enumerate(bot_weak_players):
            # Vary delay: 1-3 seconds base + 0.5s per position
            delay = random.uniform(1.0, 3.0) + (i * 0.5)
            
            task = asyncio.create_task(
                self._delayed_bot_redeal_decision(bot_name, delay)
            )
            bot_tasks.append(task)
        
        # Don't wait - let them decide asynchronously
        asyncio.gather(*bot_tasks, return_exceptions=True)

    async def _delayed_bot_redeal_decision(self, bot_name: str, delay: float):
        """Make bot redeal decision after realistic delay"""
        await asyncio.sleep(delay)
        
        # Bots always accept redeals for testing purposes
        should_decline = False
        
        print(f"🤖 Bot {bot_name} deciding after {delay:.1f}s delay: {'DECLINE' if should_decline else 'ACCEPT'}")
        
        # Send decision
        action = GameAction(
            player_name=bot_name,
            action_type=ActionType.REDEAL_RESPONSE if should_decline else ActionType.REDEAL_REQUEST,
            payload={"accept": not should_decline},
            is_bot=True
        )
        
        try:
            await self.state_machine.handle_action(action)
            print(f"✅ Bot {bot_name} {'DECLINED' if should_decline else 'ACCEPTED'} redeal")
        except Exception as e:
            print(f"❌ Bot {bot_name} redeal decision error: {e}")

    
    # 🔧 FIX: Validation Feedback Event Handlers
    
    async def _handle_action_rejected(self, data: dict):
        """Handle notification that a bot action was rejected by state machine"""
        player_name = data.get("player_name")
        action_type = data.get("action_type")
        reason = data.get("reason", "Unknown reason")
        is_bot = data.get("is_bot", False)
        
        print(f"🚫 BOT_VALIDATION_FIX: Action {action_type} from {player_name} was REJECTED: {reason}")
        
        if is_bot:
            # For rejected bot actions, we need to:
            # 1. NOT process any turn completion logic
            # 2. NOT remove pieces from hands
            # 3. Clear tracking to allow retry with valid state
            print(f"🚫 BOT_VALIDATION_FIX: Bot {player_name} action rejected - preventing downstream processing")
            
            # 🔧 RACE_CONDITION_FIX: Clear tracking for rejected actions to allow retry
            if player_name in self._bot_action_cache:
                # Clear recent action cache for this bot to allow legitimate retry
                self._bot_action_cache[player_name].clear()
                print(f"🔧 RACE_CONDITION_FIX: Cleared action cache for {player_name} after rejection")
            
            if player_name in self._turn_sequence_tracking:
                # Don't clear turn tracking - bot should not retry same turn
                pass
            
            if player_name in self._phase_sequence_tracking:
                # Clear phase tracking if it was an invalid attempt
                del self._phase_sequence_tracking[player_name]
                print(f"🔧 RACE_CONDITION_FIX: Cleared phase tracking for {player_name} after rejection")
            
            # Log the rejection for debugging
            game_state = self._get_game_state()
            if hasattr(game_state, 'players'):
                for player in game_state.players:
                    if player.name == player_name:
                        print(f"🚫 BOT_VALIDATION_FIX: Bot {player_name} hand size after rejection: {len(player.hand)}")
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
            print(f"✅ BOT_VALIDATION_FIX: Bot {player_name} play accepted - state machine handling all updates")
    
    async def _handle_action_failed(self, data: dict):
        """Handle notification that a bot action failed during processing"""
        player_name = data.get("player_name")
        action_type = data.get("action_type")
        error = data.get("error", "Unknown error")
        is_bot = data.get("is_bot", False)
        
        print(f"💥 BOT_VALIDATION_FIX: Action {action_type} from {player_name} FAILED: {error}")
        
        if is_bot:
            # For failed bot actions, similar to rejection - prevent downstream processing
            print(f"💥 BOT_VALIDATION_FIX: Bot {player_name} action failed - preventing inconsistent state")