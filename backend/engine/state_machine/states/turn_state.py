# backend/engine/state_machine/states/turn_state.py

from typing import Dict, Any, Optional, List, Set
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState
from ...turn_resolution import resolve_turn, TurnPlay, TurnResult
from ...player import Player
import asyncio


class TurnState(GameState):
    """
    Turn Phase State
    
    Handles:
    - Turn sequence management (starter plays first, others follow)
    - Piece count validation (others must match starter's count)
    - Winner determination based on play value/type
    - Pile distribution to winner
    - Transition to scoring when all hands are empty
    """
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.TURN
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.SCORING]
    
    async def process_event(self, event) -> "EventResult":
        """Convert TurnState to event-driven architecture"""
        from ..events.event_types import EventResult
        from ..core import GameAction, ActionType
        
        try:
            # Convert event to action for legacy processing
            action_type = ActionType(event.trigger)
            action = GameAction(
                action_type=action_type,
                player_name=event.player_name,
                payload=event.data
            )
            
            # Use legacy handle_action method
            result = await self.handle_action(action)
            
            if result is None:
                return EventResult(success=False, reason="Turn action rejected")
            
            # Check for transition to Scoring phase
            next_phase = await self.check_transition_conditions()
            
            return EventResult(
                success=True,
                reason="Turn action processed successfully",
                triggers_transition=next_phase is not None,
                data=result if isinstance(result, dict) else {}
            )
        except Exception as e:
            return EventResult(success=False, reason=f"Turn processing error: {e}")
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAY_PIECES,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
        
        # Phase-specific state
        self.current_turn_starter: Optional[str] = None
        self.required_piece_count: Optional[int] = None
        self.turn_plays: Dict[str, Dict[str, Any]] = {}  # player -> play data
        self.turn_order: List[str] = []
        self.current_player_index: int = 0
        self.turn_complete: bool = False
        self.winner: Optional[str] = None
        self._turn_resolution_cache: Optional[Dict[str, Any]] = None  # Cache to avoid duplicate resolve_turn calls
    
    async def _setup_phase(self) -> None:
        """Initialize turn phase"""
        print(f"🔧 TURN_STATE_DEBUG: _setup_phase() called")
        
        try:
            game = self.state_machine.game
            print(f"🔧 TURN_STATE_DEBUG: Got game object: {game}")
            
            # Set initial turn starter (should be the round starter)
            self.current_turn_starter = getattr(game, 'round_starter', None) or getattr(game, 'current_player', None)
            print(f"🔧 TURN_STATE_DEBUG: Initial turn starter from game: {self.current_turn_starter}")
            
            if not self.current_turn_starter:
                # Fallback to first player (ensure it's a string)
                if hasattr(game, 'players') and game.players:
                    first_player = game.players[0]
                    self.current_turn_starter = getattr(first_player, 'name', str(first_player))
                    print(f"🔧 TURN_STATE_DEBUG: Using first player as starter: {self.current_turn_starter}")
                else:
                    self.current_turn_starter = None
                    print(f"🔧 TURN_STATE_DEBUG: No players found, starter is None")
            
            print(f"🔧 TURN_STATE_DEBUG: Final turn starter: {self.current_turn_starter}")
            self.logger.info(f"🎯 Turn phase starting - {self.current_turn_starter} starts first turn")
            
            print(f"🔧 TURN_STATE_DEBUG: About to call _start_new_turn()")
            await self._start_new_turn()
            print(f"🔧 TURN_STATE_DEBUG: _start_new_turn() completed successfully")
            
        except Exception as e:
            print(f"❌ TURN_STATE_DEBUG: Exception in _setup_phase: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _cleanup_phase(self) -> None:
        """Finalize turn phase results before transition"""
        game = self.state_machine.game
        
        # Ensure any final turn results are processed
        if self.turn_complete and self.winner:
            await self._process_turn_completion()
        
        self.logger.info("🏁 Turn phase complete - all hands empty")
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate play pieces action"""
        if action.action_type == ActionType.PLAY_PIECES:
            return await self._validate_play_pieces(action)
        
        # Other actions (disconnect, reconnect, timeout) are always valid
        return True
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions"""
        print(f"🎯 TURN_STATE_DEBUG: Processing action {action.action_type.value} from {action.player_name}")
        if action.action_type == ActionType.PLAY_PIECES:
            result = await self._handle_play_pieces(action)
            print(f"🎯 TURN_STATE_DEBUG: Play pieces result: {result}")
            return result
        elif action.action_type == ActionType.PLAYER_DISCONNECT:
            return await self._handle_player_disconnect(action)
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            return await self._handle_player_reconnect(action)
        elif action.action_type == ActionType.TIMEOUT:
            return await self._handle_timeout(action)
        else:
            return {'status': 'handled', 'action': action.action_type.value}
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to scoring phase"""
        game = self.state_machine.game
        
        # Check if all players have empty hands (main condition for scoring)
        if hasattr(game, 'players') and game.players:
            all_hands_empty = all(len(player.hand) == 0 for player in game.players)
            if all_hands_empty:
                self.logger.info("🏁 All hands empty - transitioning to scoring")
                return GamePhase.SCORING
        
        return None
    
    def _update_turn_order_for_new_starter(self, new_starter: str) -> None:
        """Update turn order to put new starter first"""
        if new_starter in self.turn_order:
            # Remove the new starter from current position
            self.turn_order.remove(new_starter)
        
        # Put the new starter at the beginning
        self.turn_order.insert(0, new_starter)
        
        self.logger.info(f"🔄 Updated turn order - new starter first: {self.turn_order}")
    
    async def start_next_turn_if_needed(self) -> bool:
        """
        Start a new turn if the current turn is complete and hands are not empty.
        Returns True if a new turn was started, False if no action taken.
        """
        print(f"🎯 START_NEXT_DEBUG: start_next_turn_if_needed() called")
        print(f"🎯 START_NEXT_DEBUG: turn_complete: {self.turn_complete}")
        
        if not self.turn_complete:
            print(f"🎯 START_NEXT_DEBUG: Turn not complete, returning False")
            return False
        
        game = self.state_machine.game
        
        # Check if any hands are empty (use same logic as check_transition_conditions)
        if hasattr(game, 'players') and game.players:
            all_hands_empty = all(len(player.hand) == 0 for player in game.players)
            print(f"🎯 START_NEXT_DEBUG: all_hands_empty: {all_hands_empty}")
            if all_hands_empty:
                # Don't start new turn - should transition to scoring
                print(f"🎯 START_NEXT_DEBUG: All hands empty, not starting new turn (should transition to scoring)")
                return False
        
        # Start new turn
        print(f"🎯 START_NEXT_DEBUG: Starting new turn with starter: {self.current_turn_starter}")
        await self._start_new_turn()
        print(f"🎯 START_NEXT_DEBUG: _start_new_turn() completed")
        return True
    
    async def _start_new_turn(self) -> None:
        """Start a new turn with current starter"""
        game = self.state_machine.game
        
        # Increment turn number for new turn
        game.turn_number += 1
        current_round = getattr(game, 'round_number', 1)
        print(f"🎯 NEW_TURN_DEBUG: Round {current_round}, Turn {game.turn_number} starting with starter {self.current_turn_starter}")
        
        # Get turn order starting from current starter
        if hasattr(game, 'get_player_order_from'):
            # Convert Player objects to strings
            player_objects = game.get_player_order_from(self.current_turn_starter)
            self.turn_order = [getattr(p, 'name', str(p)) for p in player_objects]
        else:
            # Fallback: create order from players list (ensure strings)
            players = getattr(game, 'players', [])
            player_names = [getattr(p, 'name', str(p)) for p in players]
            if self.current_turn_starter in player_names:
                start_idx = player_names.index(self.current_turn_starter)
                self.turn_order = player_names[start_idx:] + player_names[:start_idx]
            else:
                self.turn_order = player_names
        
        # Reset turn state
        self.turn_plays.clear()
        self.required_piece_count = None
        self.current_player_index = 0
        self.turn_complete = False
        self.winner = None
        self._turn_resolution_cache = None  # Clear cache for new turn
        
        # 🤖 CRITICAL: Notify bot manager with fire-and-forget to prevent async deadlock
        print(f"🔧 NEW_TURN_DEBUG: About to notify bot manager for {self.current_turn_starter}")
        try:
            # 🔧 DEADLOCK_FIX: Use fire-and-forget to prevent circular async dependency
            bot_notification_task = asyncio.create_task(
                self._notify_bot_manager_new_turn(self.current_turn_starter)
            )
            # Don't await - let it run in background to prevent deadlock
            print(f"🔧 NEW_TURN_DEBUG: Bot manager notification task created (fire-and-forget)")
            print(f"🔧 NEW_TURN_DEBUG: Bot manager notification completed (non-blocking)")
        except Exception as e:
            print(f"❌ NEW_TURN_DEBUG: Bot manager notification task creation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # 🚀 ENTERPRISE: Use automatic broadcasting system after bot notification
        print(f"🔧 NEW_TURN_DEBUG: Getting current_turn_number from game.turn_number")
        current_turn_number = game.turn_number
        print(f"🔧 NEW_TURN_DEBUG: Got current_turn_number: {current_turn_number}")
        
        print(f"🔢 TURN_NUMBER_DEBUG: Backend game.turn_number = {current_turn_number}")
        print(f"🔧 NEW_TURN_DEBUG: About to call update_phase_data")
        
        try:
            await self.update_phase_data({
                'current_turn_starter': self.current_turn_starter,
                'current_player': self.turn_order[0] if self.turn_order else None,
                'turn_order': self.turn_order.copy(),
                'required_piece_count': self.required_piece_count,
                'turn_plays': {},
                'turn_complete': False,
                'current_turn_number': current_turn_number
            }, f"New turn {current_turn_number} started with starter {self.current_turn_starter}")
            print(f"🔧 NEW_TURN_DEBUG: update_phase_data completed successfully")
        except Exception as e:
            print(f"❌ NEW_TURN_DEBUG: update_phase_data failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        self.logger.info(f"🎯 New turn started - order: {self.turn_order}")
    
    def _get_current_player(self) -> Optional[str]:
        """Get the player whose turn it is to play"""
        if not self.turn_order or self.current_player_index >= len(self.turn_order):
            return None
        return self.turn_order[self.current_player_index]
    
    async def _validate_play_pieces(self, action: GameAction) -> bool:
        """Validate a play pieces action"""
        payload = action.payload
        
        # Check if it's this player's turn
        current_player = self._get_current_player()
        if action.player_name != current_player:
            self.logger.warning(f"Not {action.player_name}'s turn - expected {current_player}")
            return False
        
        # Check if player already played this turn
        if action.player_name in self.turn_plays:
            self.logger.warning(f"{action.player_name} already played this turn")
            return False
        
        # Validate payload structure
        if 'pieces' not in payload:
            self.logger.warning(f"Play missing 'pieces': {payload}")
            return False
        
        pieces = payload['pieces']
        if not isinstance(pieces, list) or not pieces:
            self.logger.warning(f"Invalid pieces format: {pieces}")
            return False
        
        # Validate piece count
        piece_count = len(pieces)
        
        if self.required_piece_count is None:
            # This is the starter - they set the count (1-6 pieces)
            if not (1 <= piece_count <= 6):
                self.logger.warning(f"Starter must play 1-6 pieces, got {piece_count}")
                return False
        else:
            # Other players must match the required count
            if piece_count != self.required_piece_count:
                self.logger.warning(f"Must play {self.required_piece_count} pieces, got {piece_count}")
                return False
        
        # TODO: Add piece validity checks (valid combinations, player has pieces, etc.)
        # For now, assume pieces are valid
        
        return True
    
    async def _handle_play_pieces(self, action: GameAction) -> Dict[str, Any]:
        """Handle a valid play pieces action"""
        print(f"🎯 TURN_STATE_DEBUG: _handle_play_pieces called for {action.player_name}")
        print(f"🎯 TURN_STATE_DEBUG: Current state - player_index: {self.current_player_index}, turn_order: {self.turn_order}")
        
        payload = action.payload
        pieces = payload['pieces']
        piece_count = len(pieces)
        
        print(f"🎯 TURN_STATE_DEBUG: Player {action.player_name} playing {piece_count} pieces: {[str(p) for p in pieces]}")
        
        # If this is the starter, set the required piece count
        if self.required_piece_count is None:
            self.required_piece_count = piece_count
            print(f"🎯 TURN_STATE_DEBUG: Setting required piece count to {piece_count}")
            print(f"🎯 TURN_STATE_DEBUG: Before setting - required_piece_count was: None")
            print(f"🎯 TURN_STATE_DEBUG: After setting - required_piece_count is: {self.required_piece_count}")
            self.logger.info(f"🎲 {action.player_name} (starter) plays {piece_count} pieces - setting required count")
        
        # Store the play
        play_data = {
            'pieces': pieces.copy(),
            'piece_count': piece_count,
            'play_type': payload.get('play_type', 'unknown'),
            'play_value': payload.get('play_value', 0),
            'is_valid': payload.get('is_valid', True),
            'timestamp': action.timestamp
        }
        
        self.turn_plays[action.player_name] = play_data
        
        self.logger.info(f"🎲 {action.player_name} plays: {pieces} (value: {play_data['play_value']})")
        
        print(f"🎯 TURN_STATE_DEBUG: Before advancing - current_player_index: {self.current_player_index}")
        
        # Move to next player
        self.current_player_index += 1
        
        print(f"🎯 TURN_STATE_DEBUG: After advancing - current_player_index: {self.current_player_index}")
        print(f"🎯 TURN_STATE_DEBUG: Next player: {self._get_current_player()}")
        
        current_round = getattr(self.state_machine.game, 'round_number', 1)
        turn_number = getattr(self.state_machine.game, 'turn_number', 0)
        print(f"🎯 TURN_STATE_DEBUG: Round {current_round}, Turn {turn_number} - {action.player_name} played, next: {self._get_current_player()}")
        
        # Check if turn is complete
        if self.current_player_index >= len(self.turn_order):
            print(f"🎯 TURN_STATE_DEBUG: Turn complete! Calling _complete_turn()")
            await self._complete_turn()
        
        # 🚀 ENTERPRISE: Use automatic broadcasting system
        game = self.state_machine.game
        current_turn_number = game.turn_number
        
        next_player = self._get_current_player()
        print(f"🎯 UPDATE_DEBUG: About to update phase data with current_player: {next_player}, required_piece_count: {self.required_piece_count}")
        
        await self.update_phase_data({
            'current_player': next_player,
            'required_piece_count': self.required_piece_count,
            'turn_plays': self.turn_plays.copy(),
            'turn_complete': self.turn_complete,
            'current_turn_number': current_turn_number
        }, f"Player {action.player_name} played {piece_count} pieces")
        
        print(f"🎯 UPDATE_DEBUG: Phase data updated - next_player should be: {next_player}")
        
        # 🚀 ENTERPRISE: Use centralized custom event broadcasting
        await self._broadcast_play_event_enterprise(action.player_name, pieces, piece_count)
        
        # Notify bot manager about the play to trigger next bot
        await self._notify_bot_manager_play(action.player_name)
        
        return {
            'status': 'play_accepted',
            'player': action.player_name,
            'pieces': pieces,
            'piece_count': piece_count,
            'required_count': self.required_piece_count,
            'next_player': self._get_current_player(),
            'turn_complete': self.turn_complete
        }
    
    async def _complete_turn(self) -> None:
        """Complete the current turn and determine winner"""
        current_round = getattr(self.state_machine.game, 'round_number', 1)
        turn_number = getattr(self.state_machine.game, 'turn_number', 0)
        print(f"🎯 TURN_COMPLETE_DEBUG: Round {current_round}, Turn {turn_number} _complete_turn() called")
        self.turn_complete = True
        
        # Determine winner
        self.winner = self._determine_turn_winner()
        print(f"🎯 TURN_COMPLETE_DEBUG: Round {current_round}, Turn {turn_number} Winner determined: {self.winner}")
        
        if self.winner:
            # Award piles to winner
            piles_won = self.required_piece_count or 1
            await self._award_piles(self.winner, piles_won)
            
            self.logger.info(f"🏆 {self.winner} wins turn and gets {piles_won} piles")
            print(f"🎯 TURN_COMPLETE_DEBUG: Awarded {piles_won} piles to {self.winner}")
            
            # Winner starts next turn
            self.current_turn_starter = self.winner
            print(f"🎯 TURN_COMPLETE_DEBUG: Next turn starter set to: {self.winner}")
        else:
            self.logger.info("🤝 No winner this turn")
            print(f"🎯 TURN_COMPLETE_DEBUG: No winner determined")
        
        # 🚀 ENTERPRISE: Use automatic broadcasting for turn completion
        await self.update_phase_data({
            'turn_complete': True,
            'winner': self.winner,
            'piles_won': self.required_piece_count if self.winner else 0,
            'turn_plays': self.turn_plays.copy(),  # Preserve the completed turn data
            'next_turn_starter': self.winner or self.current_turn_starter
        }, f"Turn completed - winner: {self.winner}")
        print(f"🎯 TURN_COMPLETE_DEBUG: Phase data updated with turn completion")
        
        await self._process_turn_completion()
        print(f"🎯 TURN_COMPLETE_DEBUG: _process_turn_completion() finished")
    
    def _determine_turn_winner(self) -> Optional[str]:
        """Determine the winner of the current turn using turn_resolution.py"""
        # Get turn resolution data (this will call resolve_turn once and cache the result)
        turn_result_data = self._get_turn_resolution_data()
        
        if turn_result_data and turn_result_data.get('winner'):
            winner_name = turn_result_data['winner']
            winner_play_data = self.turn_plays.get(winner_name, {})
            
            current_round = getattr(self.state_machine.game, 'round_number', 1)
            turn_number = getattr(self.state_machine.game, 'turn_number', 0)
            self.logger.info(f"🎯 Round {current_round}, Turn {turn_number} winner: {winner_name} with {winner_play_data.get('play_type', 'unknown')} value {winner_play_data.get('play_value', 0)}")
            return winner_name
        
        self.logger.info("🤝 No valid winner determined by turn resolution")
        return None
    
    def _get_turn_resolution_data(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive turn resolution data for frontend display"""
        if not self.turn_plays:
            return None
        
        # Return cached result if available
        if self._turn_resolution_cache is not None:
            return self._turn_resolution_cache
        
        # Convert turn_plays to TurnPlay objects for turn_resolution
        turn_play_objects = []
        game = self.state_machine.game
        
        # Get player objects
        player_map = {}
        if hasattr(game, 'players') and game.players:
            for player in game.players:
                player_name = getattr(player, 'name', str(player))
                player_map[player_name] = player
        
        # Create TurnPlay objects in turn order
        for player_name in self.turn_order:
            if player_name in self.turn_plays:
                play_data = self.turn_plays[player_name]
                pieces = play_data.get('pieces', [])
                is_valid = play_data.get('is_valid', True)
                
                # Get player object or create minimal one
                player_obj = player_map.get(player_name)
                if not player_obj:
                    player_obj = type('Player', (), {'name': player_name})()
                
                turn_play = TurnPlay(
                    player=player_obj,
                    pieces=pieces,
                    is_valid=is_valid
                )
                turn_play_objects.append(turn_play)
        
        # Use turn_resolution to get complete result
        turn_result = resolve_turn(turn_play_objects)
        
        # Convert to JSON-serializable format
        result_data = {
            'all_plays': [],
            'winner': None,
            'winner_play': None
        }
        
        # Add all plays
        for turn_play in turn_result.plays:
            player_name = getattr(turn_play.player, 'name', str(turn_play.player))
            play_info = {
                'player': player_name,
                'pieces': [str(p) for p in turn_play.pieces],
                'is_valid': turn_play.is_valid,
                'play_type': self.turn_plays.get(player_name, {}).get('play_type', 'unknown'),
                'play_value': self.turn_plays.get(player_name, {}).get('play_value', 0)
            }
            result_data['all_plays'].append(play_info)
        
        # Add winner information
        if turn_result.winner:
            winner_name = getattr(turn_result.winner.player, 'name', str(turn_result.winner.player))
            winner_play_data = self.turn_plays.get(winner_name, {})
            
            result_data['winner'] = winner_name
            result_data['winner_play'] = {
                'pieces': [str(p) for p in turn_result.winner.pieces],
                'value': winner_play_data.get('play_value', 0),
                'type': winner_play_data.get('play_type', 'unknown'),
                'pilesWon': self.required_piece_count or 1
            }
        
        # Cache the result
        self._turn_resolution_cache = result_data
        return result_data
    
    async def _award_piles(self, winner: str, pile_count: int) -> None:
        """Award piles to the winner"""
        game = self.state_machine.game
        
        # Initialize player piles if not exists
        if not hasattr(game, 'player_piles'):
            game.player_piles = {}
        
        if winner not in game.player_piles:
            game.player_piles[winner] = 0
        
        game.player_piles[winner] += pile_count
        
        # 🎯 NEW: Also increment the player's captured_piles for scoring
        for player in game.players:
            if player.name == winner:
                player.captured_piles += pile_count
                print(f"🎯 CAPTURED_PILES_DEBUG: {winner} captured_piles += {pile_count} = {player.captured_piles}")
                break
        
        self.logger.info(f"💰 {winner} now has {game.player_piles[winner]} piles total")
    
    async def _process_turn_completion(self) -> None:
        """Process the completion of a turn"""
        game = self.state_machine.game
        
        print(f"🏁 TURN_COMPLETION_DEBUG: Starting turn completion processing")
        
        # STEP 1: Remove played pieces from player hands FIRST
        if hasattr(game, 'players') and game.players:
            for player in game.players:
                player_name = player.name
                if player_name in self.turn_plays:
                    play_data = self.turn_plays[player_name]
                    pieces_to_remove = play_data['pieces']
                    
                    print(f"🏁 TURN_COMPLETION_DEBUG: Removing {len(pieces_to_remove)} pieces from {player_name}")
                    # Remove each piece from player's hand
                    for piece in pieces_to_remove:
                        if piece in player.hand:
                            player.hand.remove(piece)
        
        # STEP 2: Check if any hands are empty AFTER pieces removed
        all_hands_empty = True
        hand_sizes = {}
        if hasattr(game, 'players') and game.players:
            for player in game.players:
                hand_size = len(player.hand)
                hand_sizes[player.name] = hand_size
                if hand_size > 0:
                    all_hands_empty = False
        
        print(f"🏁 TURN_COMPLETION_DEBUG: After removing pieces, checking if all hands are empty")
        print(f"🏁 TURN_COMPLETION_DEBUG: all_hands_empty = {all_hands_empty}")
        
        # 🔧 FIX: Add defensive consistency check
        self._validate_hand_size_consistency(hand_sizes)
        
        if hasattr(game, 'players') and game.players:
            for player in game.players:
                print(f"🏁 TURN_COMPLETION_DEBUG: {player.name} hand size: {len(player.hand)}")
        
        # STEP 3: Broadcast turn completion using centralized system
        await self._broadcast_turn_completion_enterprise()
        
        # STEP 4: Decide next action based on whether hands are empty
        if all_hands_empty:
            # Store the last turn winner for the next round's starter
            if self.winner:
                game.last_turn_winner = self.winner
                self.logger.info(f"🏁 All hands are now empty - round complete. Last turn winner: {self.winner}")
            else:
                self.logger.info("🏁 All hands are now empty - round complete")
            print(f"🏁 TURN_COMPLETION_DEBUG: Round complete - auto-transitioning to Scoring phase")
            await self.state_machine._immediate_transition_to(GamePhase.SCORING, 
                                                             "All hands empty - round complete")
        else:
            # Update starter for next turn
            if self.winner:
                self.current_turn_starter = self.winner
                # FIX: Also update turn order to put winner first
                self._update_turn_order_for_new_starter(self.winner)
                self.logger.info(f"🎯 Next turn starter: {self.winner}")
                
                print(f"🏁 TURN_COMPLETION_DEBUG: Hands not empty - will start next turn immediately")
                # 🚀 EVENT-DRIVEN: No backend delays - frontend handles display timing
                self.logger.info(f"🎯 Turn complete - starting next turn immediately (frontend controls display)")
                turn_started = await self.start_next_turn_if_needed()
                
                # 🚀 ENTERPRISE: New turn auto-start automatically broadcasts via update_phase_data
                # No manual broadcast needed - the update_phase_data in _start_new_turn handles this
                if turn_started:
                    self.logger.info("🚀 Enterprise: New turn auto-started with automatic broadcasting")
            else:
                self.logger.info(f"🤝 No winner - starter remains: {self.current_turn_starter}")
    
    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during turn"""
        player = action.player_name
        self.logger.warning(f"⚠️ {player} disconnected during turn phase")
        
        # If it's the disconnected player's turn, they forfeit
        current_player = self._get_current_player()
        if player == current_player:
            # Auto-play invalid pieces or skip
            await self._auto_play_for_player(player)
        
        return {'status': 'player_disconnected', 'player': player}
    
    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during turn"""
        player = action.player_name
        self.logger.info(f"✅ {player} reconnected during turn phase")
        
        return {'status': 'player_reconnected', 'player': player}
    
    async def _handle_timeout(self, action: GameAction) -> Dict[str, Any]:
        """Handle action timeout"""
        current_player = self._get_current_player()
        if current_player:
            self.logger.warning(f"⏰ Timeout for {current_player}")
            await self._auto_play_for_player(current_player)
        
        return {'status': 'timeout_handled', 'player': current_player}
    
    async def _auto_play_for_player(self, player: str) -> None:
        """Auto-play for a player (disconnected or timeout)"""
        game = self.state_machine.game
        
        # Determine required piece count
        required_count = self.required_piece_count
        if required_count is None:
            # Player is starter, default to 1 piece
            required_count = 1
        
        # Get player's hand
        player_hand = []
        if hasattr(game, 'player_hands') and player in game.player_hands:
            player_hand = game.player_hands[player]
        
        # Auto-select pieces (just take first N pieces)
        pieces = player_hand[:required_count] if len(player_hand) >= required_count else player_hand
        
        # Create auto-play action
        auto_action = GameAction(
            player_name=player,
            action_type=ActionType.PLAY_PIECES,
            payload={
                'pieces': pieces,
                'play_type': 'auto',
                'play_value': 0,
                'is_valid': False  # Auto-plays are considered invalid
            },
            is_bot=True
        )
        
        self.logger.info(f"🤖 Auto-playing for {player}: {pieces}")
        
        # Process the auto-play
        await self._handle_play_pieces(auto_action)
        
    async def restart_turn_for_testing(self) -> None:
        """
        Public method to restart a new turn - primarily for testing integration.
        In production, this would be called by external game flow logic.
        """
        if not self.turn_complete:
            self.logger.warning("Attempting to restart turn that isn't complete")
            return
        
        # Check if hands are empty (shouldn't restart if empty)
        game = self.state_machine.game
        if hasattr(game, 'player_hands') and game.player_hands:
            all_hands_empty = all(len(hand) == 0 for hand in game.player_hands.values())
            if all_hands_empty:
                self.logger.info("Cannot restart turn - all hands are empty")
                return
        
        # Reset turn state for new turn
        self.turn_complete = False
        self.winner = None
        self.turn_plays.clear()
        self.required_piece_count = None
        self.current_player_index = 0
        
        # Get turn order starting from current starter (winner of last turn)
        if hasattr(game, 'get_player_order_from'):
            # Convert Player objects to strings
            player_objects = game.get_player_order_from(self.current_turn_starter)
            self.turn_order = [p.name for p in player_objects]
        else:
            # Fallback: create order from players list
            players = getattr(game, 'players', [])
            if isinstance(players[0], str):
                # Players are strings
                if self.current_turn_starter in players:
                    start_idx = players.index(self.current_turn_starter)
                    self.turn_order = players[start_idx:] + players[:start_idx]
                else:
                    self.turn_order = players
            else:
                # Players are objects, extract names
                player_names = [p.name for p in players]
                if self.current_turn_starter in player_names:
                    start_idx = player_names.index(self.current_turn_starter)
                    self.turn_order = player_names[start_idx:] + player_names[:start_idx]
                else:
                    self.turn_order = player_names
        
        # 🚀 ENTERPRISE: Use automatic broadcasting system even in testing methods
        await self.update_phase_data({
            'current_turn_starter': self.current_turn_starter,
            'current_player': self._get_current_player(),
            'turn_order': self.turn_order.copy(),
            'required_piece_count': self.required_piece_count,
            'turn_plays': {},
            'turn_complete': False,
            'winner': None
        }, f"Turn restarted for testing - starter: {self.current_turn_starter}")
        
        self.logger.info(f"🔄 Restarted turn - starter: {self.current_turn_starter}, order: {self.turn_order}")
    
    async def _broadcast_play_event_enterprise(self, player_name: str, pieces: List, piece_count: int):
        """🚀 ENTERPRISE: Broadcast play event using centralized system"""
        try:
            from engine.rules import get_play_type
            
            # Get play type
            play_type = get_play_type(pieces) if pieces else "UNKNOWN"
            
            # Use enterprise broadcasting system
            await self.broadcast_custom_event("play", {
                "player": player_name,
                "pieces": [str(p) for p in pieces],
                "valid": True,
                "play_type": play_type,
                "next_player": self._get_current_player(),
                "required_count": self.required_piece_count,
                "turn_complete": self.turn_complete
            }, f"Player {player_name} played {piece_count} pieces")
            
            print(f"🎯 TURN_STATE_DEBUG: Enterprise broadcast play event - next_player: {self._get_current_player()}")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast play event: {e}", exc_info=True)
    
    # Legacy method for backward compatibility - will be removed
    async def _broadcast_play_event(self, player_name: str, pieces: List, piece_count: int):
        """DEPRECATED: Use _broadcast_play_event_enterprise instead"""
        await self._broadcast_play_event_enterprise(player_name, pieces, piece_count)

    async def _notify_bot_manager_play(self, player_name: str):
        """Notify bot manager about a player's play to trigger next bot actions"""
        try:
            from ...bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.state_machine, 'room_id', 'unknown')
            
            print(f"🤖 TURN_STATE_DEBUG: Notifying bot manager about {player_name}'s play for room {room_id}")
            
            # Trigger bot manager to handle the next player's turn
            await bot_manager.handle_game_event(room_id, "player_played", {
                "player_name": player_name
            })
            
        except Exception as e:
            self.logger.error(f"Failed to notify bot manager about play: {e}", exc_info=True)
    
    async def _notify_bot_manager_new_turn(self, starter: str):
        """Notify bot manager about a new turn starting"""
        try:
            from ...bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.state_machine, 'room_id', 'unknown')
            
            print(f"🤖 NEW_TURN_DEBUG: Notifying bot manager about new turn starter {starter} for room {room_id}")
            
            # Trigger bot manager to handle the new turn
            await bot_manager.handle_game_event(room_id, "turn_started", {
                "starter": starter
            })
            
        except Exception as e:
            self.logger.error(f"Failed to notify bot manager about new turn: {e}", exc_info=True)
    
    async def _broadcast_turn_completion_enterprise(self):
        """🚀 ENTERPRISE: Broadcast turn completion using centralized system"""
        try:
            game = self.state_machine.game
            
            # Get full turn resolution data using turn_resolution.py
            turn_result_data = self._get_turn_resolution_data()
            
            # Get winning play details from resolution data
            winning_play = None
            if turn_result_data and turn_result_data.get('winner_play'):
                winning_play = turn_result_data['winner_play']
            
            # Get current turn's pile awards (not accumulated round totals)
            player_piles = {}
            if self.winner and self.required_piece_count:
                # Only show the piles won in THIS turn, not accumulated totals
                player_piles[self.winner] = self.required_piece_count
                
                # Initialize all other players to 0 for this turn
                if hasattr(game, 'players') and game.players:
                    for player in game.players:
                        player_name = getattr(player, 'name', str(player))
                        if player_name != self.winner:
                            player_piles[player_name] = 0
            
            # Get player list
            players = []
            if hasattr(game, 'players') and game.players:
                players = [{'name': player.name} for player in game.players]
            
            # Check if all hands are empty (determines next phase)
            all_hands_empty = True
            if hasattr(game, 'players') and game.players:
                all_hands_empty = all(len(player.hand) == 0 for player in game.players)
            
            # Get actual turn number from game state
            turn_number = game.turn_number
            
            # Use enterprise broadcasting system with full turn resolution data
            await self.broadcast_custom_event("turn_complete", {
                "winner": self.winner,
                "winning_play": winning_play,
                "turn_resolution": turn_result_data,  # Full resolution data for TurnResultsUI
                "player_piles": player_piles,
                "players": players,
                "turn_number": turn_number,
                "next_starter": self.winner or self.current_turn_starter,
                "all_hands_empty": all_hands_empty,
                "will_continue": not all_hands_empty
            }, f"Turn {turn_number} completed - winner: {self.winner}")
            
            self.logger.info(f"🚀 Enterprise broadcast turn completion - winner: {self.winner}, turn piles awarded: {player_piles}")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast turn completion: {e}", exc_info=True)
    
    # Legacy method for backward compatibility
    async def _broadcast_turn_completion(self):
        """DEPRECATED: Use _broadcast_turn_completion_enterprise instead"""
        await self._broadcast_turn_completion_enterprise()

    # REMOVED: _broadcast_new_turn_started() - no longer needed
    # 🚀 ENTERPRISE: New turn broadcasting is handled automatically by update_phase_data() in _start_new_turn()
    
    def _validate_hand_size_consistency(self, hand_sizes: dict) -> None:
        """🔧 FIX: Defensive check for hand size consistency to prevent state desynchronization"""
        if not hand_sizes:
            return
        
        # Check for uneven hand distribution
        hand_values = list(hand_sizes.values())
        min_hand_size = min(hand_values)
        max_hand_size = max(hand_values)
        
        print(f"🔧 CONSISTENCY_CHECK: Hand sizes: {hand_sizes}")
        print(f"🔧 CONSISTENCY_CHECK: Min: {min_hand_size}, Max: {max_hand_size}")
        
        # If there's more than 1 card difference between players, something is wrong
        if max_hand_size - min_hand_size > 1:
            self.logger.error(f"❌ CONSISTENCY ERROR: Uneven hand distribution detected!")
            self.logger.error(f"   Hand sizes: {hand_sizes}")
            self.logger.error(f"   Max difference: {max_hand_size - min_hand_size} cards")
            
            # Log turn plays for debugging
            self.logger.error(f"   Turn plays processed: {list(self.turn_plays.keys())}")
            
            # This indicates a race condition or invalid action processing
            # The game should not continue in this state
            print(f"🚨 CRITICAL: Game state inconsistency detected - investigation needed!")
            
            # For now, continue but log the error for debugging
            return
        
        # Check for mixed hand states (some empty, some with cards > 1)
        non_empty_hands = [size for size in hand_values if size > 0]
        if non_empty_hands and min(hand_values) == 0:
            # Some players have empty hands, others don't
            if max(non_empty_hands) > 1:
                self.logger.warning(f"⚠️ MIXED STATE: Some players empty ({[name for name, size in hand_sizes.items() if size == 0]}), others with multiple cards")
                print(f"⚠️ MIXED STATE WARNING: This may indicate piece removal issues")
        
        print(f"✅ CONSISTENCY_CHECK: Hand size distribution is acceptable")
