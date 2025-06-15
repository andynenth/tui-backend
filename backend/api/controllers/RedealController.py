# backend/api/controllers/RedealController.py

import asyncio
from typing import List, Dict, Any, Optional
from backend.socket_manager import broadcast

class RedealController:
    """
    Controller for managing the redeal phase of the game.
    Handles player decisions for redeal requests and coordinates the process.
    """
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        
        # Redeal state
        self.weak_hand_players: List[str] = []
        self.redeal_decisions: Dict[str, str] = {}
        self.phase_active: bool = False
        self.pending_players: List[str] = []
        
        # Get room manager
        self.room_manager = None
    
    def _get_room_manager(self):
        """Lazy load room manager to avoid import issues"""
        if self.room_manager is None:
            from backend.shared_instances import shared_room_manager
            self.room_manager = shared_room_manager
        return self.room_manager
    
    def _get_room(self):
        """Get the current room"""
        room_manager = self._get_room_manager()
        return room_manager.get_room(self.room_id)
    
    async def start(self) -> bool:
        """
        Start the redeal phase by identifying players with weak hands
        and prompting them for redeal decisions.
        """
        try:
            room = self._get_room()
            if not room or not room.game:
                print(f"❌ RedealController: Room {self.room_id} or game not found")
                return False
            
            # Get players with weak hands (assuming this method exists in game)
            if hasattr(room.game, 'get_weak_hand_players'):
                weak_players_data = room.game.get_weak_hand_players()
                self.weak_hand_players = [p['name'] for p in weak_players_data]
            else:
                # Fallback: check for players with < 3 pieces
                self.weak_hand_players = [
                    p.name for p in room.game.players 
                    if len(p.hand) < 3 and not p.is_bot
                ]
            
            if not self.weak_hand_players:
                print(f"✅ No players need redeal in room {self.room_id}")
                return True
            
            self.phase_active = True
            self.pending_players = self.weak_hand_players.copy()
            self.redeal_decisions = {}
            
            # Broadcast redeal phase start to all players
            await broadcast(self.room_id, "redeal_phase_started", {
                "weak_players": self.weak_hand_players,
                "message": "Players with weak hands can request a redeal"
            })
            
            # Start prompting players for decisions
            await self._prompt_redeal_decisions()
            
            print(f"✅ Redeal phase started for room {self.room_id}, weak players: {self.weak_hand_players}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting redeal phase: {e}")
            return False
    
    async def _prompt_redeal_decisions(self):
        """Prompt all weak hand players for their redeal decisions"""
        for player_name in self.weak_hand_players:
            await broadcast(self.room_id, "redeal_prompt", {
                "player": player_name,
                "message": f"{player_name}, do you want to redeal your hand?",
                "options": ["accept", "decline"]
            })
        
        # Set a timeout for decisions
        asyncio.create_task(self._handle_timeout())
    
    async def handle_player_decision(self, player_name: str, choice: str):
        """
        Handle a player's redeal decision.
        
        Args:
            player_name: Name of the player making the decision
            choice: "accept" or "decline"
        """
        if not self.phase_active:
            print(f"⚠️ Redeal phase not active for {player_name}'s decision")
            return
        
        if player_name not in self.weak_hand_players:
            print(f"⚠️ Player {player_name} not eligible for redeal")
            return
        
        if player_name in self.redeal_decisions:
            print(f"⚠️ Player {player_name} already made a decision")
            return
        
        # Validate choice
        if choice not in ["accept", "decline"]:
            print(f"❌ Invalid choice '{choice}' from {player_name}")
            return
        
        # Record the decision
        self.redeal_decisions[player_name] = choice
        if player_name in self.pending_players:
            self.pending_players.remove(player_name)
        
        print(f"✅ {player_name} chose to {choice} redeal")
        
        # Broadcast the decision
        await broadcast(self.room_id, "redeal_decision_made", {
            "player": player_name,
            "choice": choice,
            "pending_players": len(self.pending_players)
        })
        
        # Check if all decisions are made
        if len(self.redeal_decisions) == len(self.weak_hand_players):
            await self._process_redeal_decisions()
    
    async def _process_redeal_decisions(self):
        """Process all redeal decisions and apply results"""
        try:
            room = self._get_room()
            if not room or not room.game:
                return
            
            # Count players who want redeal
            redeal_requests = [name for name, choice in self.redeal_decisions.items() if choice == "accept"]
            
            if redeal_requests:
                # Apply redeal for requesting players
                if hasattr(room.game, 'apply_redeal'):
                    result = room.game.apply_redeal(redeal_requests)
                else:
                    # Fallback: redeal entire round
                    result = room.game.prepare_round()
                
                await broadcast(self.room_id, "redeal_applied", {
                    "redeal_players": redeal_requests,
                    "new_hands": result.get("hands", {}),
                    "message": f"Redeal applied for: {', '.join(redeal_requests)}"
                })
            else:
                await broadcast(self.room_id, "redeal_declined", {
                    "message": "All players declined redeal. Game continues."
                })
            
            # End redeal phase
            self.phase_active = False
            self.pending_players = []
            
            print(f"✅ Redeal phase completed for room {self.room_id}")
            
        except Exception as e:
            print(f"❌ Error processing redeal decisions: {e}")
    
    async def _handle_timeout(self, timeout_seconds: int = 30):
        """Handle timeout for redeal decisions"""
        await asyncio.sleep(timeout_seconds)
        
        if not self.phase_active:
            return  # Phase already completed
        
        # Auto-decline for players who didn't respond
        for player_name in self.pending_players.copy():
            self.redeal_decisions[player_name] = "decline"
            print(f"⏰ Auto-declined redeal for {player_name} (timeout)")
        
        self.pending_players = []
        
        # Broadcast timeout
        await broadcast(self.room_id, "redeal_timeout", {
            "message": "Redeal decision timeout. Continuing game."
        })
        
        # Process decisions
        await self._process_redeal_decisions()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current redeal phase status"""
        return {
            "active": self.phase_active,
            "weak_players": self.weak_hand_players,
            "decisions": self.redeal_decisions,
            "pending": self.pending_players
        }