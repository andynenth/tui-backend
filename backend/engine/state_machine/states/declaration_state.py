# backend/engine/state_machine/states/declaration_state.py

from typing import Dict, List, Optional, Any
from ..base_state import GameState
from ..core import GamePhase, ActionType, GameAction

class DeclarationState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.DECLARATION
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.TURN]
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.DECLARE,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
    
    async def _setup_phase(self) -> None:
        game = self.state_machine.game
        
        # Get round starter, fallback to current_player or first player
        round_starter = getattr(game, 'round_starter', None)
        if not round_starter:
            round_starter = getattr(game, 'current_player', None)
        if not round_starter and game.players:
            # Fallback to first player name
            first_player = game.players[0]
            round_starter = getattr(first_player, 'name', str(first_player))
            print(f"⚠️ DECL_STATE_DEBUG: No round_starter found, using first player: {round_starter}")
        
        print(f"📢 DECL_STATE_DEBUG: Using round_starter: {round_starter}")
        declaration_order = game.get_player_order_from(round_starter)
        
        self.phase_data.update({
            'declaration_order': declaration_order,
            'current_declarer_index': 0,
            'declarations': {},
            'declaration_total': 0
        })
        # Set current_declarer after phase_data is initialized
        self.phase_data['current_declarer'] = self._get_current_declarer()
    
    async def _cleanup_phase(self) -> None:
        # FIX: Copy declarations to game object during cleanup
        game = self.state_machine.game
        game.player_declarations = self.phase_data['declarations'].copy()
        self.logger.info(f"Copied declarations to game: {game.player_declarations}")
    
    async def _validate_action(self, action: GameAction) -> bool:
        if action.action_type == ActionType.DECLARE:
            payload = action.payload
            
            if 'value' not in payload:
                self.logger.warning(f"Declaration missing 'value': {payload}")
                return False
            
            declared_value = payload['value']
            if not isinstance(declared_value, int) or not (0 <= declared_value <= 8):
                self.logger.warning(f"Invalid declaration value: {declared_value}")
                return False
            
            current_player = self._get_current_declarer()
            if action.player_name != current_player:
                self.logger.warning(f"Wrong player turn: {action.player_name}, expected: {current_player}")
                return False
            
            return await self._check_declaration_restrictions(action.player_name, declared_value)
        
        return True
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        if action.action_type == ActionType.DECLARE:
            return await self._handle_declaration(action)
        else:
            return {'status': 'handled', 'action': action.action_type.value}
    
    async def _handle_declaration(self, action: GameAction) -> Dict[str, Any]:
        player_name = action.player_name
        declared_value = action.payload['value']
        
        # Record declaration in phase data
        self.phase_data['declarations'][player_name] = declared_value
        self.phase_data['declaration_total'] += declared_value
        self.phase_data['current_declarer_index'] += 1
        self.phase_data['current_declarer'] = self._get_current_declarer()
        
        # FIX: Also immediately update game object for real-time access
        self.state_machine.game.player_declarations[player_name] = declared_value
        
        # Update the player object's declared attribute
        for player in self.state_machine.game.players:
            if getattr(player, 'name', str(player)) == player_name:
                player.declared = declared_value
                break
        
        self.logger.info(f"Player {player_name} declared {declared_value}")
        
        return {
            'status': 'declaration_recorded',
            'player': player_name,
            'value': declared_value,
            'total': self.phase_data['declaration_total']
        }
    
    def _get_current_declarer(self) -> Optional[str]:
        order = self.phase_data['declaration_order']
        index = self.phase_data['current_declarer_index']
        
        if index < len(order):
            player = order[index]
            # Return player name as string
            if hasattr(player, 'name'):
                return player.name
            else:
                return str(player)
        return None
    
    async def _check_declaration_restrictions(self, player_name: str, value: int) -> bool:
        # Simplified validation - you can add your game-specific rules here
        # For example, check zero streak, last player total != 8, etc.
        return True
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        order = self.phase_data['declaration_order']
        declarations = self.phase_data['declarations']
        
        if len(declarations) >= len(order):
            return GamePhase.TURN
        return None