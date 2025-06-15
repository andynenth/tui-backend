# backend/api/controllers/RedealController.py

import asyncio
from typing import List, Dict, Any, Optional
from .BaseController import BaseController
from ..services.BroadcastService import BroadcastService
from ..events.GameEvents import GameEvent, GameEventType, game_event_bus

class RedealController(BaseController):
    """
    Controller สำหรับจัดการ Redeal Phase แบบ sequential event-driven
    ใช้ refactored game.py และ ไม่ depend on GameService
    
    Features:
    - Sequential player prompting
    - Bot auto-decision
    - Event-driven communication
    - Timeout handling
    - State management
    """
    
    def __init__(self, room_id: str):
        super().__init__(room_id)
        
        # Redeal state
        self.weak_hand_players: List[Dict[str, Any]] = []
        self.current_player_index: int = 0
        self.redeal_decisions: Dict[str, str] = {}
        self.phase_complete: bool = False
        
        # Services
        self.broadcast_service = BroadcastService()
        
        # Direct access to room manager (avoid GameService dependency)
        self.room_manager = None
    
    def _get_room_manager(self):
        """Lazy load room manager to avoid import issues"""
        if self.room_manager is None:
            # Import only when needed to avoid circular dependencies
            from backend.shared_instances import shared_room_manager
            self.room_manager = shared_room_manager
        return self.room_manager
    
    async def _validate_prerequisites(self) -> None:
        """ตรวจสอบว่า room และ game พร้อม"""
        room_manager = self._get_room_manager()
        room = room_manager.get_room(self.room_id)
        
        if not room:
            raise ValueError(f"Room {self.room_id} not found")
        
        if not room.game:
            raise ValueError(f"Game not started in room {self.room_id}")
        
        if not room.game.players:
            raise ValueError(f"No players in room {self.room_id}")
    
    async def _initialize_state(self) -> None:
        """เตรียม state สำหรับ redeal phase"""
        room_manager = self._get_room_manager()
        room = room_manager.get_room(self.room_id)
        
        # ✅ ใช้ refactored method จาก game.py
        self.weak_hand_players = room.game.get_weak_hand_players(include_details=True)
        self.current_player_index = 0
        self.redeal_decisions = {}
        self.phase_complete = False
        
        # Set game phase
        room.game.set_current_phase("redeal")
        
        self.logger.info(f"Found {len(self.weak_hand_players)} players with weak hands")
        for player in self.weak_hand_players:
            self.logger.info(f"  - {player['name']}: {player['hand_strength']} points")
    
    async def _setup_event_handlers(self) -> None:
        """ตั้งค่า event handlers"""
        # Subscribe to game events
        game_event_bus.subscribe(GameEventType.PLAYER_ACTION, self._handle_player_action)
    
    async def _on_started(self) -> None:
        """เริ่ม redeal phase"""
        # ถ้าไม่มีคนที่ต้อง redeal - จบทันที
        if not self.weak_hand_players:
            self.logger.info("No weak hands found - completing phase immediately")
            await self._complete_phase()
            return
        
        # เริ่มจาก player แรก
        await self._prompt_current_player()
    
    async def _prompt_current_player(self) -> None:
        """Prompt player ปัจจุบันให้ตัดสินใจ"""
        if self.current_player_index >= len(self.weak_hand_players):
            await self._complete_phase()
            return
        
        current_player = self.weak_hand_players[self.current_player_index]
        self.logger.info(f"Prompting {current_player['name']} for redeal decision")
        
        # ส่ง waiting status ให้คนอื่น
        await self._broadcast_waiting_status(current_player)
        
        if current_player['is_bot']:
            # Bot ตัดสินใจอัตโนมัติ
            await self._handle_bot_decision(current_player)
        else:
            # Human player - ส่ง prompt
            await self.broadcast_service.send_redeal_prompt(
                self.room_id,
                current_player['name'],
                current_player['hand'],
                current_player['hand_strength']
            )
            
            # ตั้ง timeout (30 วินาที)
            asyncio.create_task(self._handle_timeout(current_player['name']))
    
    async def _broadcast_waiting_status(self, current_player: Dict[str, Any]) -> None:
        """ส่งสถานะ waiting ให้ทุกคน"""
        waiting_players = [p['name'] for p in self.weak_hand_players[self.current_player_index + 1:]]
        completed_players = [p['name'] for p in self.weak_hand_players[:self.current_player_index]]
        
        await self.broadcast_service.send_redeal_waiting(
            self.room_id,
            current_player['name'],
            waiting_players,
            completed_players,
            self.redeal_decisions
        )
    
    async def _handle_bot_decision(self, bot_player: Dict[str, Any]) -> None:
        """จัดการการตัดสินใจของ bot"""
        # Simple bot logic: redeal ถ้า hand แรงน้อยกว่า 15 คะแนน
        choice = "Yes" if bot_player['hand_strength'] < 15 else "No"
        
        # Simulate thinking time
        await asyncio.sleep(2)
        
        self.logger.info(f"Bot {bot_player['name']} auto-decided: {choice}")
        await self.handle_player_decision(bot_player['name'], choice)
    
    async def handle_player_decision(self, player_name: str, choice: str) -> bool:
        """จัดการการตัดสินใจของ player"""
        if self.phase_complete or not self.is_active:
            return False
        
        # ตรวจสอบว่าเป็นตาของ player นี้หรือไม่
        if self.current_player_index >= len(self.weak_hand_players):
            return False
            
        current_player = self.weak_hand_players[self.current_player_index]
        if current_player['name'] != player_name:
            self.logger.warning(f"Not {player_name}'s turn (current: {current_player['name']})")
            return False
        
        # Validate choice
        if choice not in ['Yes', 'No']:
            self.logger.warning(f"Invalid choice from {player_name}: {choice}")
            return False
        
        self.logger.info(f"{player_name} decided: {choice}")
        
        # บันทึกการตัดสินใจ
        self.redeal_decisions[player_name] = choice
        
        # แจ้งให้ทุกคนทราบ
        remaining_players = len(self.weak_hand_players) - self.current_player_index - 1
        await self.broadcast_service.send_redeal_decision_made(
            self.room_id,
            player_name,
            choice,
            self.redeal_decisions,
            remaining_players
        )
        
        # ถ้าเลือก redeal - ให้ไพ่ใหม่
        if choice.lower() == 'yes':
            await self._execute_redeal(player_name)
        
        # ไปคนต่อไป
        self.current_player_index += 1
        await asyncio.sleep(1)  # หน่วงเล็กน้อย
        await self._prompt_current_player()
        
        return True
    
    async def _execute_redeal(self, player_name: str) -> None:
        """ให้ไพ่ใหม่กับ player"""
        room_manager = self._get_room_manager()
        room = room_manager.get_room(self.room_id)
        
        # ✅ ใช้ refactored method จาก game.py
        try:
            redeal_result = room.game.execute_redeal_for_player(player_name)
            
            if redeal_result['success']:
                # ส่งไพ่ใหม่ให้ player
                await self.broadcast_service.broadcast_to_room(
                    self.room_id,
                    GameEventType.REDEAL_NEW_HAND.value,
                    {
                        'player': player_name,
                        'hand': redeal_result['new_hand'],
                        'multiplier': redeal_result['multiplier']
                    }
                )
                
                # แจ้งให้คนอื่นทราบ (ไม่บอกไพ่)
                await self.broadcast_service.broadcast_to_room(
                    self.room_id,
                    GameEventType.PLAYER_REDEALT.value,
                    {
                        'player': player_name,
                        'multiplier': redeal_result['multiplier']
                    }
                )
                
                self.logger.info(f"Executed redeal for {player_name}, new multiplier: {redeal_result['multiplier']}")
            else:
                self.logger.error(f"Failed to execute redeal for {player_name}")
                
        except Exception as e:
            self.logger.error(f"Error executing redeal for {player_name}: {e}")
    
    async def _complete_phase(self) -> None:
        """จบ redeal phase"""
        if self.phase_complete:
            return
            
        self.phase_complete = True
        self.logger.info("Redeal phase completed")
        
        room_manager = self._get_room_manager()
        room = room_manager.get_room(self.room_id)
        
        # สรุปผล
        total_redeals = sum(1 for choice in self.redeal_decisions.values() if choice.lower() == 'yes')
        
        summary = {
            'phase': 'redeal_complete',
            'total_players_checked': len(self.weak_hand_players),
            'total_redeals': total_redeals,
            'decisions': self.redeal_decisions,
            'next_phase': 'declaration',
            'current_multiplier': room.game.redeal_multiplier
        }
        
        # Set next phase in game
        room.game.set_current_phase("declaration")
        
        # แจ้งให้ทุกคน
        await self.broadcast_service.broadcast_to_room(
            self.room_id,
            GameEventType.REDEAL_PHASE_COMPLETE.value,
            summary
        )
        
        # Publish internal event
        event = GameEvent(
            event_type=GameEventType.REDEAL_PHASE_COMPLETE,
            room_id=self.room_id,
            data=summary
        )
        await game_event_bus.publish(event)
        
        # หยุด controller
        await self.stop()
    
    async def _handle_timeout(self, player_name: str) -> None:
        """จัดการ timeout"""
        await asyncio.sleep(30)  # รอ 30 วินาที
        
        # ตรวจสอบว่ายังเป็นตาของ player นี้อยู่หรือไม่
        if (not self.phase_complete and 
            self.current_player_index < len(self.weak_hand_players) and
            self.weak_hand_players[self.current_player_index]['name'] == player_name and
            player_name not in self.redeal_decisions):
            
            self.logger.warning(f"{player_name} timeout - auto selecting 'No'")
            await self.handle_player_decision(player_name, 'No')
    
    async def _handle_player_action(self, event: GameEvent) -> None:
        """จัดการ player actions จาก event bus"""
        if event.room_id != self.room_id:
            return
            
        action_type = event.data.get('action_type')
        if action_type == 'redeal_decision':
            player_name = event.data.get('player_name')
            choice = event.data.get('choice')
            
            if player_name and choice:
                await self.handle_player_decision(player_name, choice)
    
    async def _cleanup(self) -> None:
        """Cleanup resources"""
        # Unsubscribe from event bus
        game_event_bus.unsubscribe(GameEventType.PLAYER_ACTION, self._handle_player_action)
        
        # Reset state
        self.weak_hand_players = []
        self.current_player_index = 0
        self.redeal_decisions = {}
        self.phase_complete = True