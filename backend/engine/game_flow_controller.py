# backend/engine/game_flow_controller.py

from backend.engine.phase_manager import PhaseManager, GamePhase
import logging

logger = logging.getLogger(__name__)

class GameFlowController:
    """
    Main game flow controller that integrates phase management,
    bot management, and game logic
    """
    
    def __init__(self, room_id: str, game_instance):
        self.room_id = room_id
        self.game = game_instance
        self.phase_manager = PhaseManager(room_id)
        self.ws_connections = {}  # player -> websocket
        
        # Track game state
        self.is_active = True
        self.current_round = 0
        
    async def start_game(self):
        """Start the game with proper phase management"""
        logger.info(f"Starting game in room {self.room_id}")
        
        # Register bots
        bot_players = [p for p in self.game.players if p.startswith("Bot")]
        await bot_manager.register_room(self.room_id, bot_players)
        
        # Transition from waiting to first phase
        await self.phase_manager.transition_to(GamePhase.REDEAL)
        
        # Notify all clients
        await self.broadcast_phase_transition(GamePhase.REDEAL)
        
        # Start game loop
        await self.game_loop()
    
    async def game_loop(self):
        """Main game loop that manages phase transitions"""
        while self.is_active:
            current_phase = self.phase_manager.current_phase
            
            try:
                if current_phase == GamePhase.REDEAL:
                    await self.handle_redeal_phase()
                
                elif current_phase == GamePhase.DECLARATION:
                    await self.handle_declaration_phase()
                
                elif current_phase == GamePhase.TURN:
                    await self.handle_turn_phase()
                
                elif current_phase == GamePhase.SCORING:
                    await self.handle_scoring_phase()
                
                elif current_phase == GamePhase.WAITING:
                    # Game ended or waiting for restart
                    break
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                await self.handle_error(e)
    
    # ==================== PHASE HANDLERS ====================
    
    async def handle_redeal_phase(self):
        """Handle redeal phase flow"""
        logger.info(f"Room {self.room_id}: Handling redeal phase")
        
        # Check for weak hands
        weak_players = self.game.get_weak_players()
        
        if not weak_players:
            # No redeal needed, move to declaration
            await self.phase_manager.transition_to(GamePhase.DECLARATION)
            await self.broadcast_phase_transition(GamePhase.DECLARATION)
            return
        
        # Notify about redeal phase
        await self.broadcast_event("redeal_phase_started", {
            "weak_players": weak_players,
            "total_players": len(weak_players)
        })
        
        # Process redeal decisions sequentially
        for idx, player in enumerate(weak_players):
            await self.process_redeal_decision(player, idx, len(weak_players))
        
        # Complete redeal phase
        await self.complete_redeal_phase()
    
    async def handle_declaration_phase(self):
        """Handle declaration phase flow"""
        logger.info(f"Room {self.room_id}: Handling declaration phase")
        
        # Notify bots about phase change
        declaration_order = self.game.get_declaration_order()
        await bot_manager.handle_phase_change(
            self.room_id, 
            "declaration",
            {"declaration_order": declaration_order}
        )
        
        # Wait for all declarations
        await self.process_declarations(declaration_order)
        
        # Move to turn phase
        await self.phase_manager.transition_to(GamePhase.TURN)
        await self.broadcast_phase_transition(GamePhase.TURN)
    
    async def handle_turn_phase(self):
        """Handle turn phase flow"""
        logger.info(f"Room {self.room_id}: Handling turn phase")
        
        # Notify bots
        await bot_manager.handle_phase_change(self.room_id, "turn")
        
        # Process turns until round ends
        while not self.game.is_round_complete():
            await self.process_single_turn()
        
        # Move to scoring
        await self.phase_manager.transition_to(GamePhase.SCORING)
        await self.broadcast_phase_transition(GamePhase.SCORING)
    
    async def handle_scoring_phase(self):
        """Handle scoring phase flow"""
        logger.info(f"Room {self.room_id}: Handling scoring phase")
        
        # Calculate scores
        scores = self.game.calculate_round_scores()
        
        # Broadcast scores
        await self.broadcast_event("round_scores", scores)
        
        # Check game end
        if self.game.is_game_over():
            await self.end_game()
        else:
            # Start next round
            self.current_round += 1
            await self.phase_manager.transition_to(GamePhase.REDEAL)
            await self.broadcast_phase_transition(GamePhase.REDEAL)
    
    # ==================== ACTION HANDLERS ====================
    
    async def handle_player_action(self, player: str, action: str, data: Dict):
        """Handle any player action with phase validation"""
        
        # Validate action against current phase
        validation = self.phase_manager.validate_action(action, {
            "player": player,
            "data": data
        })
        
        if not validation["valid"]:
            logger.warning(
                f"Player {player} attempted invalid action '{action}': {validation['error']}"
            )
            
            # Send error to player
            await self.send_to_player(player, {
                "type": "error",
                "error": validation["error"],
                "current_phase": validation["current_phase"],
                "allowed_actions": validation.get("allowed_actions", [])
            })
            return False
        
        # Process valid action
        return await self.process_action(player, action, data)
    
    async def process_action(self, player: str, action: str, data: Dict):
        """Process a validated action"""
        
        if action == "redeal_decision":
            return await self.handle_redeal_decision(player, data["choice"])
        
        elif action == "declare":
            return await self.handle_declaration(player, data["value"])
        
        elif action == "play_pieces":
            return await self.handle_play(player, data["pieces"])
        
        else:
            logger.warning(f"Unhandled action: {action}")
            return False
    
    # ==================== UTILITIES ====================
    
    async def broadcast_event(self, event_type: str, data: Dict):
        """Broadcast event to all players"""
        message = {
            "type": event_type,
            "room_id": self.room_id,
            **data
        }
        
        # Send to all connected clients
        for player, ws in self.ws_connections.items():
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {player}: {e}")
    
    async def broadcast_phase_transition(self, new_phase: GamePhase):
        """Broadcast phase transition to all clients"""
        await self.broadcast_event("phase_transition", {
            "new_phase": new_phase.value,
            "phase_info": self.phase_manager.get_phase_info()
        })
        
        # Notify bot manager
        await bot_manager.handle_phase_change(
            self.room_id,
            new_phase.value,
            self.phase_manager.phase_data
        )
    
    async def send_to_player(self, player: str, message: Dict):
        """Send message to specific player"""
        ws = self.ws_connections.get(player)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {player}: {e}")
    
    async def handle_error(self, error: Exception):
        """Handle game errors"""
        logger.error(f"Game error in room {self.room_id}: {error}")
        
        # Broadcast error
        await self.broadcast_event("game_error", {
            "error": str(error),
            "phase": self.phase_manager.current_phase.value
        })
        
        # Try to recover or end game
        if isinstance(error, RecoverableError):
            # Reset to waiting
            await self.phase_manager.transition_to(GamePhase.WAITING, force=True)
        else:
            # End game
            await self.end_game(error=True)
    
    async def end_game(self, error: bool = False):
        """End the game"""
        self.is_active = False
        
        # Transition to waiting
        await self.phase_manager.transition_to(GamePhase.WAITING)
        
        # Clean up bots
        bot_manager.cleanup_room(self.room_id)
        
        # Notify clients
        await self.broadcast_event("game_ended", {
            "reason": "error" if error else "complete",
            "final_scores": self.game.get_final_scores() if not error else {}
        })

# Example integration with your websocket handler
async def handle_websocket_message(room_id: str, player: str, message: Dict):
    """Handle incoming websocket message with phase validation"""
    
    game_controller = get_game_controller(room_id)
    if not game_controller:
        return {"error": "Game not found"}
    
    action = message.get("action")
    data = message.get("data", {})
    
    # Process through phase-aware controller
    success = await game_controller.handle_player_action(player, action, data)
    
    return {"success": success}