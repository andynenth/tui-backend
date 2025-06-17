# backend/api/controllers/PreparationController.py
from .BaseController import BaseController
from ..events.GameEvents import GameEventType, GameEvent
from backend.socket_manager import broadcast
import asyncio

class PreparationController(BaseController):
    """Controls the entire preparation phase"""
    
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.weak_players = []
        self.redeal_decisions = {}
        self.redeal_multiplier = 1
        
    async def _initialize_state(self):
        """Initialize preparation phase state"""
        room = self.get_room()
        game = room.game
        
        # Deal initial hands
        game.deal_hands()
        
        # Check for weak hands
        self.weak_players = game.get_weak_hand_players()
        
        # Broadcast initial state
        await self._broadcast_game_state()
        
    async def _on_started(self):
        """Start preparation phase flow"""
        if self.weak_players:
            await self._start_redeal_sequence()
        else:
            await self._complete_preparation()
            
    async def _start_redeal_sequence(self):
        """Start redeal check sequence"""
        await broadcast(self.room_id, {
            'type': GameEventType.REDEAL_PHASE_STARTED.value,
            'data': {
                'weak_players': [p.name for p in self.weak_players],
                'total_players': len(self.weak_players)
            }
        })
        
        # Process each weak player sequentially
        for player in self.weak_players:
            await self._prompt_redeal_decision(player)
            
    async def _prompt_redeal_decision(self, player):
        """Prompt a specific player for redeal decision"""
        # Send prompt
        await broadcast(self.room_id, {
            'type': GameEventType.REDEAL_PROMPT.value,
            'data': {
                'target_player': player.name,
                'hand_strength': self._calculate_hand_strength(player.hand)
            }
        })
        
        # Wait for decision (with timeout)
        try:
            decision = await self._wait_for_decision(player, timeout=30)
            await self._process_redeal_decision(player, decision)
        except asyncio.TimeoutError:
            # Auto-decline on timeout
            await self._process_redeal_decision(player, 'decline')