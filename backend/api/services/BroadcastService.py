# backend/api/services/BroadcastService.py

from typing import Dict, Any, List, Optional
from backend.socket_manager import broadcast
from ..events.GameEvents import GameEvent, GameEventType
import logging
import time

class BroadcastService:
    """
    Service สำหรับ broadcasting events ผ่าน WebSocket
    เตรียมพร้อมสำหรับ event-driven architecture
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def broadcast_to_room(self, room_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast ไปทุกคนใน room"""
        try:
            await broadcast(room_id, event_type, data)
            self.logger.debug(f"Broadcasted {event_type} to room {room_id}")
        except Exception as e:
            self.logger.error(f"Failed to broadcast {event_type} to room {room_id}: {e}")
    
    async def broadcast_to_players(self, room_id: str, player_names: List[str], 
                                 event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast ไปเฉพาะ players ที่ระบุ 
        TODO: Implement per-player broadcasting when socket_manager supports it
        """
        # ตอนนี้ยัง broadcast ไปทุกคน เพราะ socket_manager ยังไม่รองรับ per-player
        await self.broadcast_to_room(room_id, event_type, data)
    
    async def broadcast_game_event(self, event: GameEvent) -> None:
        """Broadcast GameEvent object"""
        await self.broadcast_to_room(
            event.room_id,
            event.event_type.value,
            event.data
        )
    
    # =================================
    # REDEAL SPECIFIC BROADCASTS
    # =================================
    
    async def send_redeal_prompt(self, room_id: str, player_name: str, 
                               hand: List[str], hand_strength: int) -> None:
        """ส่ง redeal prompt ให้ player"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.REDEAL_PROMPT.value,
            {
                'player': player_name,
                'hand': hand,
                'hand_strength': hand_strength,
                'timeout': 30
            }
        )
    
    async def send_redeal_waiting(self, room_id: str, current_player: str, 
                                waiting_players: List[str], completed_players: List[str],
                                decisions: Dict[str, str]) -> None:
        """ส่ง redeal waiting status"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.REDEAL_WAITING.value,
            {
                'current_player': current_player,
                'waiting_players': waiting_players,
                'completed_players': completed_players,
                'decisions_made': decisions,
                'phase': 'redeal',
                'message': f"รอ {current_player} ตัดสินใจ redeal..."
            }
        )
    
    async def send_redeal_decision_made(self, room_id: str, player_name: str, choice: str,
                                      decisions: Dict[str, str], remaining_players: int) -> None:
        """ส่ง redeal decision result"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.REDEAL_DECISION_MADE.value,
            {
                'player': player_name,
                'choice': choice,
                'decisions': decisions,
                'remaining_players': remaining_players
            }
        )
    
    async def send_redeal_new_hand(self, room_id: str, player_name: str, 
                                 new_hand: List[str], multiplier: float) -> None:
        """ส่งไพ่ใหม่ให้ player หลัง redeal"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.REDEAL_NEW_HAND.value,
            {
                'player': player_name,
                'hand': new_hand,
                'multiplier': multiplier
            }
        )
    
    async def send_player_redealt(self, room_id: str, player_name: str, multiplier: float) -> None:
        """ส่งแจ้งให้คนอื่นทราบว่ามีคน redeal (ไม่บอกไพ่)"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.PLAYER_REDEALT.value,
            {
                'player': player_name,
                'multiplier': multiplier
            }
        )
    
    async def send_redeal_phase_complete(self, room_id: str, summary: Dict[str, Any]) -> None:
        """ส่งแจ้ง redeal phase เสร็จสิ้น"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.REDEAL_PHASE_COMPLETE.value,
            summary
        )
    
    # =================================
    # DECLARATION SPECIFIC BROADCASTS
    # =================================
    
    async def send_declaration_prompt(self, room_id: str, player_name: str, 
                                   valid_declarations: List[int]) -> None:
        """ส่ง declaration prompt ให้ player"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.DECLARATION_PROMPT.value,
            {
                'player': player_name,
                'valid_declarations': valid_declarations,
                'timeout': 30
            }
        )
    
    async def send_declaration_made(self, room_id: str, player_name: str, 
                                  declaration: int, all_declarations: Dict[str, int]) -> None:
        """ส่งผล declaration"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.DECLARATION_MADE.value,
            {
                'player': player_name,
                'declaration': declaration,
                'all_declarations': all_declarations,
                'total_declared': sum(all_declarations.values())
            }
        )
    
    # =================================
    # TURN SPECIFIC BROADCASTS  
    # =================================
    
    async def send_turn_prompt(self, room_id: str, player_name: str, 
                             valid_plays: List[Dict]) -> None:
        """ส่ง turn prompt ให้ player"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.TURN_PROMPT.value,
            {
                'player': player_name,
                'valid_plays': valid_plays,
                'timeout': 60
            }
        )
    
    async def send_turn_played(self, room_id: str, player_name: str, 
                             pieces_played: List[str], play_type: str) -> None:
        """ส่งผลการเล่น turn"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.TURN_PLAYED.value,
            {
                'player': player_name,
                'pieces_played': pieces_played,
                'play_type': play_type
            }
        )
    
    # =================================
    # GENERIC BROADCASTS
    # =================================
    
    async def send_phase_transition(self, room_id: str, from_phase: str, to_phase: str) -> None:
        """ส่งแจ้ง phase transition"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.PHASE_TRANSITION.value,
            {
                'from_phase': from_phase,
                'to_phase': to_phase,
                'timestamp': time.time()
            }
        )
    
    async def send_game_state_update(self, room_id: str, game_state: Dict[str, Any]) -> None:
        """ส่ง game state update"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.GAME_STATE_UPDATED.value,
            game_state
        )
    
    async def send_error(self, room_id: str, error_type: str, message: str, 
                        player_name: Optional[str] = None) -> None:
        """ส่ง error message"""
        await self.broadcast_to_room(
            room_id,
            GameEventType.PHASE_ERROR.value,
            {
                'error_type': error_type,
                'message': message,
                'player': player_name,
                'timestamp': time.time()
            }
        )