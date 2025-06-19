# backend/api/controllers/RedealController.py (แก้ไข method name)

import asyncio
from typing import List, Dict, Any, Optional  # ✅ เพิ่ม Dict, Any
from backend.socket_manager import broadcast
class RedealController:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.weak_hand_players: List[str] = []
        self.current_player_index: int = 0  # ✅ เพิ่ม sequential control
        self.redeal_decisions: Dict[str, str] = {}
        self.phase_active: bool = False
        
        # Get room manager
        self.room_manager = None
    
    def _get_room_manager(self):
        """Lazy load room manager to avoid import issues"""
        if self.room_manager is None:
            from backend.shared_instances import shared_room_manager
            self.room_manager = shared_room_manager
        return self.room_manager
    
    def get_room(self):  # ✅ เปลี่ยนจาก _get_room เป็น get_room
        """Get the current room"""
        room_manager = self._get_room_manager()
        return room_manager.get_room(self.room_id)
    
    async def start(self) -> bool:
        """Start the redeal phase sequentially"""
        try:
            room = self.get_room()  # ✅ เรียก get_room แทน _get_room
            if not room or not room.game:
                print(f"❌ RedealController: Room {self.room_id} or game not found")
                return False
            
            # Get players with weak hands
            weak_players_data = room.game.get_weak_hand_players(include_details=True)
            self.weak_hand_players = [p['name'] for p in weak_players_data]
            
            if not self.weak_hand_players:
                print(f"✅ No players need redeal in room {self.room_id}")
                await self._complete_redeal_phase()
                return True
            
            self.phase_active = True
            self.current_player_index = 0  # ✅ เริ่มจากคนแรก
            self.redeal_decisions = {}
            
            # Broadcast redeal phase start
            await broadcast(self.room_id, "redeal_phase_started", {
                "weak_players": self.weak_hand_players,
                "total_players": len(self.weak_hand_players),
                "message": "Starting redeal decisions..."
            })
            
            # ✅ เริ่มจากผู้เล่นคนแรก
            await self._prompt_current_player()
            
            print(f"✅ Redeal phase started for room {self.room_id}, weak players: {self.weak_hand_players}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting redeal phase: {e}")
            return False
    
    async def _prompt_current_player(self):
        """✅ ใหม่: Prompt ผู้เล่นปัจจุบันเท่านั้น"""
        if self.current_player_index >= len(self.weak_hand_players):
            # ครบทุกคนแล้ว
            await self._process_redeal_decisions()
            return
            
        current_player = self.weak_hand_players[self.current_player_index]
        
        print(f"🎯 Prompting {current_player} for redeal decision ({self.current_player_index + 1}/{len(self.weak_hand_players)})")
        
        # ส่ง prompt เฉพาะคนนี้
        await broadcast(self.room_id, "redeal_prompt", {
            "target_player": current_player,  # ✅ ระบุชัดเจนว่าเป็นตาใคร
            "player": current_player,
            "player_index": self.current_player_index,
            "total_players": len(self.weak_hand_players),
            "message": f"{current_player}, do you want to redeal your hand?",
            "options": ["accept", "decline"]
        })
        
        # ✅ Handle bot automatically
        await self._handle_bot_decision(current_player)
    
    async def _handle_bot_decision(self, player_name: str):
        """✅ ใหม่: จัดการ bot decision อัตโนมัติ"""
        room = self.get_room()
        if not room or not room.game:
            return
            
        player = room.game.get_player(player_name)
        if player and player.is_bot:
            # Bot ตัดสินใจอัตโนมัติ
            await asyncio.sleep(1.5)  # Delay เพื่อให้ดู realistic
            
            # Bot logic: ถ้าไม่มีไพ่แรง ให้ redeal
            has_strong_piece = any(piece.point > 9 for piece in player.hand)
            bot_choice = "decline" if has_strong_piece else "accept"
            
            print(f"🤖 Bot {player_name} auto-deciding: {bot_choice}")
            await self.handle_player_decision(player_name, bot_choice)
    
    async def handle_player_decision(self, player_name: str, choice: str):
        """Handle player decision and move to next player"""
        if not self.phase_active:
            print(f"⚠️ Redeal phase not active for {player_name}'s decision")
            return
        
        # ✅ ตรวจสอบว่าเป็นตาของเขาไหม
        current_player = self.weak_hand_players[self.current_player_index]
        if player_name != current_player:
            print(f"⚠️ Not {player_name}'s turn (expecting {current_player})")
            return
        
        if player_name in self.redeal_decisions:
            print(f"⚠️ Player {player_name} already made a decision")
            return
        
        # Validate choice
        if choice not in ["accept", "decline"]:
            print(f"❌ Invalid choice '{choice}' from {player_name}")
            return
        
        # ✅ บันทึกการตัดสินใจ
        self.redeal_decisions[player_name] = choice
        print(f"✅ {player_name} chose to {choice} redeal")
        
        # ✅ Broadcast decision
        await broadcast(self.room_id, "redeal_decision_made", {
            "player": player_name,
            "choice": choice,
            "player_index": self.current_player_index,
            "remaining_players": len(self.weak_hand_players) - self.current_player_index - 1,
            "is_bot": player_name.startswith("Bot")
        })
        
        # ✅ ไปคนถัดไป
        self.current_player_index += 1
        
        # Small delay before next prompt
        await asyncio.sleep(0.5)
        await self._prompt_current_player()
    
    async def _process_redeal_decisions(self):
        """Process all redeal decisions and apply results"""
        try:
            room = self.get_room()
            if not room or not room.game:
                return
            
            # Count players who want redeal
            redeal_requests = [name for name, choice in self.redeal_decisions.items() if choice == "accept"]
            
            print(f"📊 Redeal summary: {len(redeal_requests)}/{len(self.weak_hand_players)} players want redeal")
            
            if redeal_requests:
                # Apply redeal - pass is_redeal=True to prepare_round
                result = room.game.prepare_round(is_redeal=True)  # ← KEY CHANGE
                
                # Broadcast new hands
                await broadcast(self.room_id, "redeal_applied", {
                    "redeal_players": redeal_requests,
                    "new_hands": result.get("hands", {}),
                    "multiplier": room.game.redeal_multiplier,
                    "round": room.game.round_number,  # Should stay the same
                    "message": f"Redeal applied for: {', '.join(redeal_requests)}"
                })
                
                # ✅ CHECK IF NEW HANDS STILL HAVE WEAK HANDS
                if result.get("need_redeal", False):
                    print(f"⚠️ New hands still have weak players: {result.get('weak_players')}")
                    
                    # Reset controller state for another redeal phase
                    self.weak_hand_players = result.get("weak_players", [])
                    self.redeal_decisions = {}
                    self.current_player_index = 0
                    
                    # Notify frontend to reset state
                    await broadcast(self.room_id, "redeal_phase_restarting", {
                        "reason": "New weak hands detected after redeal",
                        "weak_players": self.weak_hand_players,
                        "multiplier": room.game.redeal_multiplier
                    })
                    
                    # Start another redeal phase
                    await self.start()  # This will prompt weak players again
                    return  # Don't complete phase yet!
            else:
                # No one wants redeal
                await broadcast(self.room_id, "redeal_declined", {
                    "message": "All players declined redeal. Game continues."
                })
            
            # Only complete phase if no weak hands remain
            await self._complete_redeal_phase()
                
        except Exception as e:
            print(f"❌ Error processing redeal decisions: {e}")
    
    async def _complete_redeal_phase(self):
        """✅ ใหม่: จบ redeal phase และไป declaration"""
        self.phase_active = False
        self.current_player_index = 0
        
        await broadcast(self.room_id, "redeal_phase_complete", {
            "next_phase": "declaration",
            "message": "Redeal phase complete. Starting declarations..."
        })
        
        print(f"✅ Redeal phase completed for room {self.room_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current redeal phase status"""
        return {
            "active": self.phase_active,
            "weak_players": self.weak_hand_players,
            "current_player_index": self.current_player_index,
            "decisions": self.redeal_decisions,
            "pending": len(self.weak_hand_players) - self.current_player_index - 1
        }
        
    async def handle_redeal_decision(self, player: str, choice: str) -> bool:
        """Handle redeal decision with phase validation"""
        
        # Validate phase first
        from backend.api.routes.routes import get_game_controller
        controller = get_game_controller(self.room_id)
        
        if controller:
            validation = controller.phase_manager.validate_action("redeal_decision", {
                "player": player,
                "choice": choice
            })
            
            if not validation["valid"]:
                print(f"❌ Redeal decision rejected: {validation['error']}")
                return False