# backend/engine/state_machine/states/turn_state.py

from typing import Dict, Any, Optional, List, Set
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState


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
    
    async def _setup_phase(self) -> None:
        """Initialize turn phase"""
        game = self.state_machine.game
        
        # Set initial turn starter (should be the round starter)
        self.current_turn_starter = getattr(game, 'round_starter', None) or getattr(game, 'current_player', None)
        if not self.current_turn_starter:
            # Fallback to first player
            self.current_turn_starter = game.players[0] if hasattr(game, 'players') and game.players else None
        
        self.logger.info(f"🎯 Turn phase starting - {self.current_turn_starter} starts first turn")
        await self._start_new_turn()
    
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
        if action.action_type == ActionType.PLAY_PIECES:
            return await self._handle_play_pieces(action)
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
        
        # Only transition when a turn is complete AND all hands are empty
        if not self.turn_complete:
            return None
        
        # Check if all players have empty hands
        if hasattr(game, 'player_hands') and game.player_hands:
            all_hands_empty = all(len(hand) == 0 for hand in game.player_hands.values())
            if all_hands_empty:
                self.logger.info("🏁 All hands empty and turn complete - transitioning to scoring")
                return GamePhase.SCORING
        
        return None
    
    async def start_next_turn_if_needed(self) -> bool:
        """
        Start a new turn if the current turn is complete and hands are not empty.
        Returns True if a new turn was started, False if no action taken.
        """
        if not self.turn_complete:
            return False
        
        game = self.state_machine.game
        
        # Check if any hands are empty
        if hasattr(game, 'player_hands') and game.player_hands:
            all_hands_empty = all(len(hand) == 0 for hand in game.player_hands.values())
            if all_hands_empty:
                # Don't start new turn - should transition to scoring
                return False
        
        # Start new turn
        await self._start_new_turn()
        return True
    
    async def _start_new_turn(self) -> None:
        """Start a new turn with current starter"""
        game = self.state_machine.game
        
        # Get turn order starting from current starter
        if hasattr(game, 'get_player_order_from'):
            self.turn_order = game.get_player_order_from(self.current_turn_starter)
        else:
            # Fallback: create order from players list
            players = getattr(game, 'players', [])
            if self.current_turn_starter in players:
                start_idx = players.index(self.current_turn_starter)
                self.turn_order = players[start_idx:] + players[:start_idx]
            else:
                self.turn_order = players
        
        # Reset turn state
        self.turn_plays.clear()
        self.required_piece_count = None
        self.current_player_index = 0
        self.turn_complete = False
        self.winner = None
        
        self.logger.info(f"🔄 New turn started - order: {self.turn_order}")
        
        # Update phase data for external access
        self.phase_data.update({
            'current_turn_starter': self.current_turn_starter,
            'turn_order': self.turn_order.copy(),
            'current_player': self._get_current_player(),
            'required_piece_count': self.required_piece_count,
            'turn_plays': self.turn_plays.copy(),
            'turn_complete': self.turn_complete
        })
    
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
        payload = action.payload
        pieces = payload['pieces']
        piece_count = len(pieces)
        
        # If this is the starter, set the required piece count
        if self.required_piece_count is None:
            self.required_piece_count = piece_count
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
        
        # Move to next player
        self.current_player_index += 1
        
        # Check if turn is complete
        if self.current_player_index >= len(self.turn_order):
            await self._complete_turn()
        
        # Update phase data
        self.phase_data.update({
            'current_player': self._get_current_player(),
            'required_piece_count': self.required_piece_count,
            'turn_plays': self.turn_plays.copy(),
            'turn_complete': self.turn_complete
        })
        
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
        self.turn_complete = True
        
        # Determine winner
        self.winner = self._determine_turn_winner()
        
        if self.winner:
            # Award piles to winner
            piles_won = self.required_piece_count or 1
            await self._award_piles(self.winner, piles_won)
            
            self.logger.info(f"🏆 {self.winner} wins turn and gets {piles_won} piles")
            
            # Winner starts next turn
            self.current_turn_starter = self.winner
        else:
            self.logger.info("🤝 No winner this turn")
        
        # Update phase data with final results
        self.phase_data.update({
            'turn_complete': True,
            'winner': self.winner,
            'piles_won': self.required_piece_count if self.winner else 0,
            'turn_plays': self.turn_plays.copy(),  # Preserve the completed turn data
            'next_turn_starter': self.winner or self.current_turn_starter
        })
        
        await self._process_turn_completion()
    
    def _determine_turn_winner(self) -> Optional[str]:
        """Determine the winner of the current turn"""
        if not self.turn_plays:
            return None
        
        # Get the starter's play type to determine what we're comparing
        starter_play = self.turn_plays.get(self.current_turn_starter)
        if not starter_play:
            return None
        
        target_play_type = starter_play.get('play_type', 'unknown')
        
        # Find all players who played the same type as starter
        valid_plays = []
        for player, play_data in self.turn_plays.items():
            # Only consider plays of the same type and that are valid
            if (play_data.get('play_type') == target_play_type and 
                play_data.get('is_valid', True)):
                valid_plays.append((player, play_data))
        
        if not valid_plays:
            # No valid plays of the correct type
            return None
        
        # Sort by play value (descending), then by play order (ascending for ties)
        def sort_key(play_tuple):
            player, play_data = play_tuple
            play_value = play_data.get('play_value', 0)
            # Earlier players have lower index in turn_order
            play_order = self.turn_order.index(player) if player in self.turn_order else 999
            return (-play_value, play_order)  # Negative value for descending sort
        
        valid_plays.sort(key=sort_key)
        
        # Winner is the first after sorting
        winner, winner_play = valid_plays[0]
        
        self.logger.info(f"🎯 Turn winner: {winner} with {winner_play.get('play_type')} value {winner_play.get('play_value')}")
        
        return winner
    
    async def _award_piles(self, winner: str, pile_count: int) -> None:
        """Award piles to the winner"""
        game = self.state_machine.game
        
        # Initialize player piles if not exists
        if not hasattr(game, 'player_piles'):
            game.player_piles = {}
        
        if winner not in game.player_piles:
            game.player_piles[winner] = 0
        
        game.player_piles[winner] += pile_count
        
        self.logger.info(f"💰 {winner} now has {game.player_piles[winner]} piles total")
    
    async def _process_turn_completion(self) -> None:
        """Process the completion of a turn"""
        game = self.state_machine.game
        
        # Remove played pieces from player hands
        if hasattr(game, 'player_hands') and game.player_hands:
            for player, play_data in self.turn_plays.items():
                if player in game.player_hands:
                    pieces_to_remove = play_data['pieces']
                    # Remove each piece from player's hand
                    for piece in pieces_to_remove:
                        if piece in game.player_hands[player]:
                            game.player_hands[player].remove(piece)
        
        # Check if any hands are empty - this affects transition conditions
        all_hands_empty = True
        if hasattr(game, 'player_hands') and game.player_hands:
            for player, hand in game.player_hands.items():
                if len(hand) > 0:
                    all_hands_empty = False
                    break
        
        if all_hands_empty:
            self.logger.info("🏁 All hands are now empty - round complete")
        else:
            # DO NOT automatically start next turn!
            # The winner becomes the next turn starter for when a new turn is started
            if self.winner:
                self.current_turn_starter = self.winner
                self.logger.info(f"🎯 Next turn starter will be: {self.winner}")
            else:
                self.logger.info("🤝 No winner - starter remains: {self.current_turn_starter}")
        
        # Turn is complete - external logic decides whether to start another turn
    
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