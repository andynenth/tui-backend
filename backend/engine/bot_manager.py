# backend/engine/bot_manager.py

import asyncio
import time
import hashlib
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
        
        # 🔧 RACE_CONDITION_FIX: Bot action deduplication system
        self._bot_action_cache: Dict[str, Dict[str, float]] = {}  # bot_name -> {action_hash: timestamp}
        self._cache_timeout = 5.0  # Actions expire after 5 seconds
        self._turn_sequence_tracking: Dict[str, int] = {}  # bot_name -> last_turn_number
        self._phase_sequence_tracking: Dict[str, str] = {}  # bot_name -> last_phase_context
    
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
        
        # 🔧 HAND_SIZE_FIX: Allow legitimate bot flow while preventing excessive duplicates
        # Current player needs phase_change (to record) + player_played (to execute) triggers
        if bot_name == current_player:
            # Allow the first two triggers (phase_change + player_played), but block excessive duplicates
            recent_action_count = 0
            for existing_hash, timestamp in bot_cache.items():
                age = current_time - timestamp
                if age < 3.0:  # Count recent actions within 3 seconds
                    recent_action_count += 1
            
            if recent_action_count >= 2:  # Already had both triggers
                print(f"🚫 HAND_SIZE_FIX: Blocking excessive action for current player {bot_name} from {trigger_source} (already has {recent_action_count} recent actions)")
                return True
            else:
                print(f"✅ HAND_SIZE_FIX: Allowing action {recent_action_count + 1}/2 for current player {bot_name} from {trigger_source}")
                # Allow this action
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
        print(f"🎮 BOT_HANDLER_DEBUG: Room {self.room_id} handling event '{event}' with data: {data}")
        async with self._lock:  # Prevent concurrent bot actions
            if event == "player_declared":
                print(f"📢 BOT_HANDLER_DEBUG: Handling declaration phase")
                await self._handle_declaration_phase(data["player_name"])
            elif event == "phase_change":
                print(f"🚀 BOT_HANDLER_DEBUG: Handling enterprise phase change")
                await self._handle_enterprise_phase_change(data)
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
            # 🔧 FIX: Add validation feedback events
            elif event == "action_rejected":
                print(f"🚫 BOT_HANDLER_DEBUG: Handling action rejection")
                await self._handle_action_rejected(data)
            elif event == "action_accepted":
                print(f"✅ BOT_HANDLER_DEBUG: Handling action acceptance")
                await self._handle_action_accepted(data)
            elif event == "action_failed":
                print(f"💥 BOT_HANDLER_DEBUG: Handling action failure")
                await self._handle_action_failed(data)
            else:
                print(f"⚠️ BOT_HANDLER_DEBUG: Unknown event '{event}' - ignoring")
    
    async def _handle_enterprise_phase_change(self, data: dict):
        """
        🚀 ENTERPRISE: Handle automatic phase change events from enterprise broadcasting
        
        This implements the proper enterprise architecture where bot manager automatically
        reacts to phase data changes without manual calls from state machine.
        """
        phase = data.get("phase")
        phase_data = data.get("phase_data", {})
        reason = data.get("reason", "")
        
        print(f"🚀 ENTERPRISE_BOT_DEBUG: Processing phase change - phase: {phase}, reason: {reason}")
        
        if phase == "declaration":
            current_declarer = data.get("current_declarer") or phase_data.get("current_declarer")
            if current_declarer:
                print(f"🚀 ENTERPRISE_BOT_DEBUG: Declaration phase - checking if {current_declarer} is a bot")
                
                # Check if current declarer is a bot
                game_state = self._get_game_state()
                if hasattr(game_state, 'players'):
                    for player in game_state.players:
                        if getattr(player, 'name', str(player)) == current_declarer:
                            if getattr(player, 'is_bot', False):
                                print(f"🤖 ENTERPRISE_BOT_DEBUG: Current declarer {current_declarer} is a bot - triggering declaration")
                                # Get last declarer to continue sequence
                                declarations = phase_data.get('declarations', {})
                                declared_players = list(declarations.keys())
                                last_declarer = declared_players[-1] if declared_players else ""
                                await self._handle_declaration_phase(last_declarer)
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
                                
                                print(f"✅ RACE_CONDITION_FIX: Triggering bot play for {current_player} - no duplicates detected")
                                
                                # Get last player to continue sequence
                                turn_plays = phase_data.get('turn_plays', {})
                                if isinstance(turn_plays, dict) and turn_plays:
                                    # Get the last player from the dictionary (most recent timestamp)
                                    last_play_time = 0
                                    last_player = ""
                                    for player_name, play_data in turn_plays.items():
                                        timestamp = play_data.get('timestamp', 0)
                                        if timestamp > last_play_time:
                                            last_play_time = timestamp
                                            last_player = player_name
                                else:
                                    last_player = ""
                                await self._handle_play_phase(last_player)
                            else:
                                print(f"👤 ENTERPRISE_BOT_DEBUG: Current player {current_player} is human - waiting")
                            break
                
    async def _handle_declaration_phase(self, last_declarer: str):
        """Handle bot declarations in order - SINGLE EXECUTION ONLY"""
        # 🔧 CRITICAL FIX: Prevent duplicate/cascade declaration processing
        if hasattr(self, '_declaration_phase_processing') and self._declaration_phase_processing:
            print(f"🚫 DECL_PHASE_FIX: Declaration phase already processing, skipping duplicate call")
            return
        
        self._declaration_phase_processing = True
        
        try:
            print(f"🔍 DECL_PHASE_DEBUG: _handle_declaration_phase called with last_declarer: '{last_declarer}'")
            
            # Get declaration order
            declaration_order = self._get_declaration_order()
            print(f"🔍 DECL_PHASE_DEBUG: Declaration order: {[getattr(p, 'name', str(p)) for p in declaration_order] if declaration_order else 'None'}")
            
            # Find next bot to declare
            last_index = self._get_player_index(last_declarer, declaration_order)
            print(f"🔍 DECL_PHASE_DEBUG: Last declarer '{last_declarer}' index: {last_index}")
            
            # Get current phase data to check who needs to declare
            phase_declarations = self.state_machine.get_phase_data().get('declarations', {}) if self.state_machine else {}
            current_declarer = self.state_machine.get_phase_data().get('current_declarer') if self.state_machine else None
            
            print(f"🔍 DECL_PHASE_DEBUG: Current declarer from state: {current_declarer}")
            print(f"🔍 DECL_PHASE_DEBUG: Current declarations: {phase_declarations}")
            
            # Only process the CURRENT declarer if they're a bot and haven't declared
            if current_declarer and current_declarer not in phase_declarations:
                # Get actual Player objects from game state
                game_state = self._get_game_state()
                
                # Find the current declarer
                player_obj = None
                for p in game_state.players:
                    if getattr(p, 'name', str(p)) == current_declarer:
                        player_obj = p
                        break
                
                if player_obj and getattr(player_obj, 'is_bot', False):
                    print(f"🤖 DECL_PHASE_DEBUG: Current declarer {current_declarer} is a bot and needs to declare")
                    
                    # Bot declares with random delay (500-1500ms for realism)
                    import random
                    delay = random.uniform(0.5, 1.5)
                    print(f"🤖 DECL_PHASE_DEBUG: Bot {current_declarer} will declare in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    
                    print(f"🤖 DECL_PHASE_DEBUG: Bot {current_declarer} will now declare!")
                    position = self._get_player_index(current_declarer, declaration_order)
                    await self._bot_declare(player_obj, position)
                else:
                    print(f"👤 DECL_PHASE_DEBUG: Current declarer {current_declarer} is human or already declared, waiting")
            else:
                print(f"🔍 DECL_PHASE_DEBUG: No bot declaration needed - current_declarer: {current_declarer}, already declared: {current_declarer in phase_declarations if current_declarer else 'N/A'}")
        
        finally:
            # Always clear the processing flag
            self._declaration_phase_processing = False
            
    async def _bot_declare(self, bot: Player, position: int):
        """Make a bot declaration"""
        try:
            from backend.socket_manager import broadcast
        except ImportError:
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
        
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
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
        
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
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
        
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
        try:
            from backend.socket_manager import broadcast
        except ImportError:
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
        
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
        try:
            from backend.socket_manager import broadcast
        except ImportError:
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
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
            # 🚀 ENTERPRISE: State machine handles round preparation automatically
            # No manual round preparation needed - transition to PREPARATION phase handles everything
            print(f"🚀 ENTERPRISE: State machine will handle next round preparation automatically")
            # The state machine's SCORING -> PREPARATION transition handles all round setup
            
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
        try:
            from backend.socket_manager import broadcast
        except ImportError:
            # Handle different import paths
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from socket_manager import broadcast
        
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
                action = GameAction(
                    player_name=bot.name,
                    action_type=ActionType.REDEAL_RESPONSE,
                    payload={"accept": False},
                    is_bot=True
                )
                await self.state_machine.handle_action(action)
                print(f"🔧 Bot {bot.name} auto-declined as fallback")
    
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
        
        print(f"✅ BOT_VALIDATION_FIX: Action {action_type} from {player_name} was ACCEPTED")
        
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