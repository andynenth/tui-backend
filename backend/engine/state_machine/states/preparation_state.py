# backend/engine/state_machine/states/preparation_state.py

from typing import Dict, Any, Optional, List, Set
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState
import random


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
            ActionType.PLAYER_RECONNECT
        }
        
        # Phase-specific state
        self.weak_players: Set[str] = set()
        self.redeal_decisions: Dict[str, bool] = {}  # player -> accept/decline
        self.pending_weak_players: List[str] = []  # Queue of players to ask
        self.current_weak_player: Optional[str] = None  # Currently being asked
        self.redeal_requester: Optional[str] = None
        self.initial_deal_complete: bool = False
    
    async def _setup_phase(self) -> None:
        """Initialize preparation phase by dealing cards"""
        self.logger.info("🎴 Preparation phase starting - dealing cards")
        print(f"🎴 PREP_STATE_DEBUG: Setup phase starting for room {getattr(self.state_machine, 'room_id', 'unknown')}")
        await self._deal_cards()
    
    async def _cleanup_phase(self) -> None:
        """Finalize preparation results before transition"""
        game = self.state_machine.game
        
        # Ensure starter is set
        if not hasattr(game, 'current_player') or not game.current_player:
            starter = self._determine_starter()
            game.current_player = starter
            self.logger.info(f"🎯 Round starter set to: {starter}")
        
        # Ensure round_starter is also set (some code uses this)
        if game.current_player and (not hasattr(game, 'round_starter') or not game.round_starter):
            game.round_starter = game.current_player
        
        print(f"🎯 PREP_STATE_DEBUG: Cleanup phase - current_player: {getattr(game, 'current_player', 'None')}")
        print(f"🎯 PREP_STATE_DEBUG: Cleanup phase - round_starter: {getattr(game, 'round_starter', 'None')}")
        
        # Log final state
        multiplier = getattr(game, 'redeal_multiplier', 1)
        self.logger.info(f"📋 Preparation complete - Starter: {game.current_player}, "
                   f"Multiplier: {multiplier}x")
    
    async def _deal_cards(self) -> None:
        """Deal cards and check for weak hands"""
        game = self.state_machine.game
        
        # Use guaranteed no redeal for testing (no weak hands)
        if hasattr(game, '_deal_guaranteed_no_redeal'):
            print(f"🎴 PREP_STATE_DEBUG: Using guaranteed no redeal dealing")
            # For testing: uncomment the line below to force player 1 (Bot 2) to get RED_GENERAL
            game._deal_guaranteed_no_redeal(red_general_player_index=1)
            # game._deal_guaranteed_no_redeal()
        elif hasattr(game, 'deal_pieces'):
            print(f"🎴 PREP_STATE_DEBUG: Using normal dealing")
            game.deal_pieces()
        else:
            # Fallback for testing
            self.logger.info("Using fallback dealing method")
        
        self.initial_deal_complete = True
        
        # Check for weak hands
        if hasattr(game, 'get_weak_hand_players'):
            weak_players = game.get_weak_hand_players()
            self.weak_players = set(weak_players) if weak_players else set()
        else:
            # Fallback for testing
            self.weak_players = set()
        
        self.logger.info(f"🔍 Weak hand check - Found {len(self.weak_players)} "
                   f"weak players: {self.weak_players}")
        
        if self.weak_players:
            print(f"🃏 PREP_STATE_DEBUG: Found weak players: {self.weak_players}")
            # Get current play order (might have changed due to redeal)
            if hasattr(game, 'get_player_order_from'):
                # Determine current starter
                if game.current_player:
                    current_starter = game.current_player
                else:
                    # Get first player name properly
                    first_player = game.players[0]
                    current_starter = first_player if isinstance(first_player, str) else getattr(first_player, 'name', str(first_player))
                
                play_order = game.get_player_order_from(current_starter)
            else:
                # Extract player names from objects if needed
                play_order = []
                for p in game.players:
                    if isinstance(p, str):
                        play_order.append(p)
                    else:
                        play_order.append(getattr(p, 'name', str(p)))
            
            # Set up redeal decision queue based on play order
            # Only include players who are actually weak
            self.pending_weak_players = []
            print(f"🔍 PREP_STATE_DEBUG: Play order: {play_order}")
            print(f"🔍 PREP_STATE_DEBUG: Play order types: {[type(p) for p in play_order]}")
            for player in play_order:
                # Handle both string names and weak_players that might be strings
                player_name = player if isinstance(player, str) else getattr(player, 'name', str(player))
                print(f"🔍 PREP_STATE_DEBUG: Checking player {player_name} against weak players {self.weak_players}")
                if player_name in self.weak_players:
                    self.pending_weak_players.append(player_name)
                    print(f"✅ PREP_STATE_DEBUG: Added {player_name} to pending weak players")
                else:
                    print(f"❌ PREP_STATE_DEBUG: {player_name} not in weak players")
            
            self.current_weak_player = self.pending_weak_players[0] if self.pending_weak_players else None
            
            print(f"🎯 PREP_STATE_DEBUG: Current weak player to ask: {self.current_weak_player}")
            print(f"📋 PREP_STATE_DEBUG: Pending weak players queue: {self.pending_weak_players}")
            
            # Notify about weak hands (frontend will prompt players)
            await self._notify_weak_hands()
            
            # Trigger bot manager to handle bot decisions
            print(f"🤖 PREP_STATE_DEBUG: Triggering bot manager for redeal decisions...")
            await self._trigger_bot_redeal_decisions()
            
            # Fallback: If no current weak player but we have weak players, trigger for all
            if not self.current_weak_player and self.weak_players:
                print(f"🔧 PREP_STATE_DEBUG: No current weak player but have weak players, triggering for all")
                for weak_player in self.weak_players:
                    await self._trigger_bot_redeal_for_player(weak_player)
        else:
            # No weak hands, determine starter
            starter = self._determine_starter()
            game.current_player = starter
            game.round_starter = starter  # Always set both
            print(f"✅ PREP_STATE_DEBUG: No weak hands - starter set to: {starter}")
            self.logger.info(f"✅ No weak hands - starter: {starter}")
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action is allowed in current state"""
        # Basic validation from parent
        if action.action_type not in self.allowed_actions:
            self.logger.warning(f"Action {action.action_type} not allowed in {self.phase_name}")
            return False
        
        player_name = action.player_name
        
        if action.action_type == ActionType.REDEAL_REQUEST:
            # Must be from current weak player being asked
            if player_name != self.current_weak_player:
                self.logger.warning(f"❌ Redeal request from wrong player: "
                              f"{player_name} (expected: {self.current_weak_player})")
                return False
            
            # Must be in weak players set
            if player_name not in self.weak_players:
                self.logger.warning(f"❌ Redeal request from non-weak player: {player_name}")
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
                sequence_id=action.sequence_id
            )
            return await self._validate_action(temp_action)
        
        return True
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid preparation actions"""
        if action.action_type == ActionType.REDEAL_REQUEST:
            return await self._handle_redeal_accept(action)
        
        elif action.action_type == ActionType.REDEAL_RESPONSE:
            return await self._handle_redeal_decline(action)
        
        elif action.action_type == ActionType.PLAYER_DISCONNECT:
            return await self._handle_player_disconnect(action)
        
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            return await self._handle_player_reconnect(action)
        
        return {"success": False, "error": "Unknown action"}
    
    async def _handle_redeal_accept(self, action: GameAction) -> Dict[str, Any]:
        """Handle player accepting redeal"""
        player_name = action.player_name
        game = self.state_machine.game
        
        self.logger.info(f"♻️ {player_name} ACCEPTS redeal")
        
        # Record decision
        self.redeal_decisions[player_name] = True
        self.redeal_requester = player_name
        
        # Increase multiplier
        old_multiplier = getattr(game, 'redeal_multiplier', 1)
        game.redeal_multiplier = old_multiplier + 1
        
        self.logger.info(f"📈 Redeal multiplier: {old_multiplier}x → {game.redeal_multiplier}x")
        
        # Update starter to redeal requester (changes play order)
        game.current_player = player_name
        game.round_starter = player_name  # Always set both
        
        # Reset state for new deal
        self.weak_players.clear()
        self.redeal_decisions.clear()
        self.pending_weak_players.clear()
        self.current_weak_player = None
        
        # Execute redeal
        await self._deal_cards()
        
        return {
            "success": True,
            "redeal": True,
            "requester": player_name,
            "multiplier": game.redeal_multiplier
        }
    
    async def _handle_redeal_decline(self, action: GameAction) -> Dict[str, Any]:
        """Handle player declining redeal"""
        player_name = action.player_name
        
        self.logger.info(f"🚫 {player_name} DECLINES redeal")
        
        # Record decision
        self.redeal_decisions[player_name] = False
        
        # Move to next weak player
        if player_name in self.pending_weak_players:
            self.pending_weak_players.remove(player_name)
        
        if self.pending_weak_players:
            # Ask next player
            self.current_weak_player = self.pending_weak_players[0]
            self.logger.info(f"➡️ Asking next weak player: {self.current_weak_player}")
            
            # Trigger bot manager for next player
            await self._trigger_bot_redeal_decisions()
            
            return {
                "success": True,
                "next_weak_player": self.current_weak_player
            }
        else:
            # All weak players have declined
            self.logger.info("✅ All weak players declined - proceeding with current hands")
            
            # Determine starter
            starter = self._determine_starter()
            self.state_machine.game.current_player = starter
            self.state_machine.game.round_starter = starter  # Set both
            
            return {
                "success": True,
                "all_declined": True,
                "starter": starter
            }
    
    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during preparation"""
        player_name = action.player_name
        
        # If disconnected player was being asked about redeal, auto-decline
        if player_name == self.current_weak_player:
            self.logger.info(f"🔌 Current weak player {player_name} disconnected - auto-declining")
            # Create decline action
            decline_action = GameAction(
                player_name=player_name,
                action_type=ActionType.REDEAL_RESPONSE,
                payload={"accept": False},
                timestamp=action.timestamp,
                sequence_id=action.sequence_id
            )
            return await self._handle_redeal_decline(decline_action)
        
        return {"success": True}
    
    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during preparation"""
        # Send current state to reconnected player
        return {
            "success": True,
            "weak_players": list(self.weak_players),
            "current_weak_player": self.current_weak_player,
            "redeal_decisions": self.redeal_decisions
        }
    
    def _determine_starter(self) -> str:
        """Determine round starter based on game rules"""
        game = self.state_machine.game
        
        # Priority 1: Redeal requester (overrides all)
        if self.redeal_requester:
            self.logger.info(f"🎯 Starter: {self.redeal_requester} (requested redeal)")
            return self.redeal_requester
        
        # Priority 2: Round 1 - player with GENERAL_RED
        round_num = getattr(game, 'round', 1)
        if round_num == 1:
            print(f"🔍 STARTER_DEBUG: Looking for GENERAL_RED holder in round {round_num}")
            # Check if game has player objects with hands
            if hasattr(game, 'players') and game.players:
                for player in game.players:
                    player_name = getattr(player, 'name', str(player))
                    print(f"🔍 STARTER_DEBUG: Checking player {player_name}")
                    if hasattr(player, 'hand'):
                        print(f"🔍 STARTER_DEBUG: Player {player_name} hand: {[str(p) for p in player.hand]}")
                        for piece in player.hand:
                            piece_str = str(piece)
                            print(f"🔍 STARTER_DEBUG: Checking piece '{piece_str}' for GENERAL_RED")
                            if "GENERAL_RED" in piece_str:
                                print(f"✅ STARTER_DEBUG: Found GENERAL_RED in {player_name}'s hand!")
                                self.logger.info(f"🎯 Starter: {player_name} (has GENERAL_RED)")
                                return player_name
                    else:
                        print(f"❌ STARTER_DEBUG: Player {player_name} has no hand attribute")
            print(f"❌ STARTER_DEBUG: No GENERAL_RED found in any player's hand")
        
        # Priority 3: Previous round's last turn winner
        if hasattr(game, 'last_turn_winner') and game.last_turn_winner:
            self.logger.info(f"🎯 Starter: {game.last_turn_winner} (won last turn)")
            return game.last_turn_winner
        
        # Fallback: First player
        if hasattr(game, 'players') and game.players:
            if hasattr(game.players[0], 'name'):
                starter = game.players[0].name
            else:
                starter = game.players[0]
        else:
            starter = "Player1"
            
        self.logger.info(f"🎯 Starter: {starter} (fallback - first player)")
        return starter
    
    async def _notify_weak_hands(self) -> None:
        """Notify about weak hands found"""
        # This would trigger WebSocket notification to frontend
        # Frontend shows redeal prompt to weak players
        pass
    
    async def _trigger_bot_redeal_decisions(self) -> None:
        """Trigger bot manager to handle bot redeal decisions"""
        if self.current_weak_player:
            print(f"🔧 PREP_STATE_DEBUG: Triggering bot manager for player: {self.current_weak_player}")
            # Import here to avoid circular imports
            from backend.engine.bot_manager import BotManager
            
            # Get the singleton bot manager
            bot_manager = BotManager()
            room_id = getattr(self.state_machine, 'room_id', 'unknown')
            
            print(f"🔧 PREP_STATE_DEBUG: Using room_id: {room_id}")
            print(f"🔧 PREP_STATE_DEBUG: Bot manager active games: {list(bot_manager.active_games.keys())}")
            
            # Trigger redeal decision for current weak player
            await bot_manager.handle_game_event(room_id, "redeal_decision_needed", {
                "current_weak_player": self.current_weak_player,
                "weak_players": list(self.weak_players)
            })
        else:
            print(f"⚠️ PREP_STATE_DEBUG: No current weak player to trigger bot manager for")
    
    async def _trigger_bot_redeal_for_player(self, player_name: str) -> None:
        """Trigger bot manager for a specific weak player"""
        print(f"🔧 PREP_STATE_DEBUG: Triggering bot manager for specific player: {player_name}")
        # Import here to avoid circular imports
        from backend.engine.bot_manager import BotManager
        
        # Get the singleton bot manager
        bot_manager = BotManager()
        room_id = getattr(self.state_machine, 'room_id', 'unknown')
        
        # Trigger redeal decision for specific player
        await bot_manager.handle_game_event(room_id, "redeal_decision_needed", {
            "current_weak_player": player_name,
            "weak_players": list(self.weak_players)
        })
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to Declaration phase"""
        # Transition when:
        # 1. Initial deal done AND no weak players, OR
        # 2. All weak players have made redeal decisions
        
        print(f"🔍 PREP_STATE_DEBUG: Checking transition conditions...")
        print(f"   - Initial deal complete: {self.initial_deal_complete}")
        print(f"   - Weak players: {self.weak_players}")
        print(f"   - Redeal decisions: {self.redeal_decisions}")
        print(f"   - Current weak player: {self.current_weak_player}")
        
        if not self.initial_deal_complete:
            print(f"❌ PREP_STATE_DEBUG: Initial deal not complete, staying in preparation")
            return None
        
        if not self.weak_players:
            # No weak hands found
            print(f"✅ PREP_STATE_DEBUG: No weak players, transitioning to DECLARATION")
            return GamePhase.DECLARATION
        
        if len(self.redeal_decisions) == len(self.weak_players):
            # All weak players have decided (all must have declined)
            print(f"✅ PREP_STATE_DEBUG: All weak players decided, transitioning to DECLARATION")
            return GamePhase.DECLARATION
        
        print(f"⏳ PREP_STATE_DEBUG: Waiting for more redeal decisions ({len(self.redeal_decisions)}/{len(self.weak_players)})")
        return None