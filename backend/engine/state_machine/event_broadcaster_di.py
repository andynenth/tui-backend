# backend/engine/state_machine/event_broadcaster_di.py

import asyncio
import logging
from typing import Dict, Optional, Any, TYPE_CHECKING

from ..dependency_injection.interfaces import IBroadcaster, IBotNotifier
from .core import GamePhase

if TYPE_CHECKING:
    from .game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """
    🎯 **EventBroadcaster with Dependency Injection** - Phase 3 Circular Dependency Resolution
    
    Handles all WebSocket broadcasting and event distribution using dependency injection
    instead of direct imports to eliminate circular dependencies.
    
    Dependencies injected:
    - IBroadcaster: For WebSocket communication (replaces direct socket_manager import)
    - IBotNotifier: For bot data synchronization (replaces direct bot_manager import)
    """
    
    def __init__(
        self, 
        state_machine: 'GameStateMachine',
        broadcaster: IBroadcaster,
        bot_notifier: IBotNotifier
    ):
        self.state_machine = state_machine
        self.broadcaster = broadcaster
        self.bot_notifier = bot_notifier
        
    async def broadcast_event(self, event_type: str, event_data: Dict):
        """
        Main event broadcasting method.
        
        Sends events to all connected clients via WebSocket using injected broadcaster.
        """
        try:
            logger.debug(f"📡 BROADCASTING: {event_type} with data keys: {list(event_data.keys())}")
            
            # Add common metadata to all broadcasts
            enhanced_data = {
                **event_data,
                "timestamp": asyncio.get_event_loop().time(),
                "game_round": getattr(self.state_machine.game, 'round_number', 0) if self.state_machine.game else 0
            }
            
            # Use injected broadcaster instead of direct callback
            await self.broadcaster.broadcast_event(event_type, enhanced_data)
            logger.debug(f"✅ BROADCAST_SUCCESS: {event_type} sent successfully")
            
        except Exception as e:
            logger.error(f"❌ BROADCAST_ERROR: Failed to broadcast {event_type}: {str(e)}")
    
    async def broadcast_phase_change_with_hands(self, phase: GamePhase):
        """
        Broadcasts phase change with player hand information.
        
        This is the main phase change broadcast used throughout the game.
        """
        logger.info(f"📡 PHASE_BROADCAST: Broadcasting phase change to {phase.name}")
        
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if not room_id:
                logger.warning(f"⚠️ PHASE_BROADCAST: No room_id available")
                return
            
            # Get base phase data from current state
            phase_data = self._get_phase_data()
            
            # Add player hand information
            if self.state_machine.game and self.state_machine.game.players:
                players_data = []
                for player in self.state_machine.game.players:
                    if player:
                        player_data = {
                            "name": player.name,
                            "is_bot": getattr(player, 'is_bot', False),
                            "hand_size": len(player.hand) if hasattr(player, 'hand') and player.hand else 0
                        }
                        
                        # Add hand details for human players (bots don't need to see others' cards)
                        if hasattr(player, 'hand') and player.hand:
                            player_data["hand"] = [
                                {
                                    "suit": piece.suit,
                                    "value": piece.value,
                                    "points": piece.points
                                }
                                for piece in player.hand
                            ]
                        
                        players_data.append(player_data)
                
                phase_data["players_with_hands"] = players_data
            
            # Broadcast using injected broadcaster
            await self.broadcaster.broadcast_phase_change(room_id, phase.name, phase_data)
            
            # Notify bot manager of data changes using injected bot notifier
            await self._notify_bot_manager_data_change(phase_data, f"Phase change to {phase.name}")
            
        except Exception as e:
            logger.error(f"❌ PHASE_BROADCAST: Error broadcasting phase change: {str(e)}")
    
    async def broadcast_phase_change_with_display_metadata(self, phase: GamePhase, reason: str):
        """
        Broadcasts phase change with enhanced display metadata for frontend timing.
        
        Used for phases that need specific display timing or animations.
        """
        logger.info(f"📡 DISPLAY_BROADCAST: Broadcasting {phase.name} with display metadata - {reason}")
        
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if not room_id:
                logger.warning(f"⚠️ DISPLAY_BROADCAST: No room_id available")
                return
            
            # Get phase data
            phase_data = self._get_phase_data()
            
            # Add display configuration
            display_config = self._get_display_config_for_phase(phase)
            if display_config:
                phase_data["display_metadata"] = {
                    **display_config,
                    "reason": reason,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
            # Enhanced broadcast with display timing
            enhanced_data = {
                "phase": phase.name,
                "phase_data": phase_data,
                "display_enhanced": True,
                "reason": reason
            }
            
            await self.broadcaster.broadcast_to_room(room_id, "phase_change", enhanced_data)
            
        except Exception as e:
            logger.error(f"❌ DISPLAY_BROADCAST: Error broadcasting enhanced phase change: {str(e)}")
    
    def _get_display_config_for_phase(self, phase: GamePhase) -> Optional[Dict]:
        """
        Returns display configuration for each phase.
        
        Configures frontend timing, animations, and auto-advancement.
        """
        configs = {
            GamePhase.PREPARATION: {
                "auto_advance": False,
                "display_duration": None,
                "show_cards": True,
                "allow_actions": True
            },
            GamePhase.DECLARATION: {
                "auto_advance": False,
                "display_duration": None,
                "show_declarations": True,
                "allow_actions": True
            },
            GamePhase.TURN: {
                "auto_advance": False,
                "display_duration": None,
                "show_plays": True,
                "allow_actions": True
            },
            GamePhase.SCORING: {
                "auto_advance": True,
                "display_duration": 5000,  # 5 seconds
                "show_scores": True,
                "allow_actions": False
            }
        }
        
        return configs.get(phase)
    
    async def broadcast_turn_completion(self, turn_data: Dict):
        """
        Broadcasts turn completion with winner and pile information.
        """
        logger.info(f"🏆 TURN_BROADCAST: Broadcasting turn completion")
        
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if not room_id:
                logger.warning(f"⚠️ TURN_BROADCAST: No room_id available")
                return
            
            # Enhanced turn data with player information
            enhanced_turn_data = {
                **turn_data,
                "timestamp": asyncio.get_event_loop().time(),
                "phase": "turn_results",
                "display_metadata": {
                    "auto_advance": True,
                    "display_duration": 3000,  # 3 seconds
                    "show_winner": True,
                    "show_piles": True
                }
            }
            
            # Add current game state context
            if self.state_machine.game:
                enhanced_turn_data["game_context"] = {
                    "round_number": self.state_machine.game.round_number,
                    "turn_number": getattr(self.state_machine.game, 'turn_number', 0)
                }
            
            await self.broadcaster.broadcast_to_room(room_id, "turn_complete", enhanced_turn_data)
            
            # Update bot manager with turn results
            await self._notify_bot_manager_data_change(enhanced_turn_data, "Turn completion")
            
        except Exception as e:
            logger.error(f"❌ TURN_BROADCAST: Error broadcasting turn completion: {str(e)}")
    
    async def broadcast_scoring_completion(self, scores: Dict):
        """
        Broadcasts scoring completion with final scores and game status.
        """
        logger.info(f"📊 SCORING_BROADCAST: Broadcasting scoring completion")
        
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if not room_id:
                logger.warning(f"⚠️ SCORING_BROADCAST: No room_id available")
                return
            
            # Enhanced scoring data
            scoring_data = {
                "scores": scores,
                "timestamp": asyncio.get_event_loop().time(),
                "phase": "scoring",
                "display_metadata": {
                    "auto_advance": True,
                    "display_duration": 5000,  # 5 seconds
                    "show_final_scores": True,
                    "allow_next_round": True
                }
            }
            
            # Add game completion status
            if self.state_machine.game:
                scoring_data["game_status"] = {
                    "round_number": self.state_machine.game.round_number,
                    "is_game_complete": getattr(self.state_machine.game, 'is_complete', False),
                    "winner": getattr(self.state_machine.game, 'winner', None)
                }
            
            await self.broadcaster.broadcast_to_room(room_id, "scoring_complete", scoring_data)
            
            # Notify bot manager of scoring completion
            await self._notify_bot_manager_data_change(scoring_data, "Scoring completion")
            
        except Exception as e:
            logger.error(f"❌ SCORING_BROADCAST: Error broadcasting scoring completion: {str(e)}")
    
    async def _notify_bot_manager_data_change(self, phase_data: dict, reason: str):
        """
        Notifies bot manager when phase data changes using injected bot notifier.
        
        Keeps bot AI synchronized with current game state.
        """
        try:
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                # Filter sensitive data for bot manager
                filtered_data = self._filter_data_for_bots(phase_data)
                
                await self.bot_notifier.notify_data_change(
                    room_id=room_id,
                    data=filtered_data,
                    reason=reason
                )
                
                logger.debug(f"🤖 BOT_DATA_SYNC: Synchronized bot manager - {reason}")
            else:
                logger.warning(f"⚠️ BOT_DATA_SYNC: No room_id available for bot synchronization")
                
        except Exception as e:
            logger.error(f"❌ BOT_DATA_SYNC: Error syncing bot manager: {str(e)}")
    
    def _filter_data_for_bots(self, data: dict) -> dict:
        """
        Filters phase data to remove information that bots shouldn't see.
        
        Removes other players' private hand information while keeping
        game state information that bots need for decision making.
        """
        filtered = data.copy()
        
        # Remove detailed hand information for other players
        if "players_with_hands" in filtered:
            filtered_players = []
            for player_data in filtered["players_with_hands"]:
                # Keep hand size but remove actual cards for other players
                filtered_player = {
                    "name": player_data.get("name"),
                    "is_bot": player_data.get("is_bot", False),
                    "hand_size": player_data.get("hand_size", 0)
                }
                # Bots can see their own hands
                if player_data.get("is_bot", False):
                    filtered_player["hand"] = player_data.get("hand", [])
                
                filtered_players.append(filtered_player)
            
            filtered["players_with_hands"] = filtered_players
        
        return filtered
    
    def _get_phase_data(self) -> Dict:
        """Get current phase data from state machine."""
        if not self.state_machine.current_state:
            return {}
        
        try:
            # Try different method names for compatibility
            if hasattr(self.state_machine.current_state, 'get_state_data'):
                return self.state_machine.current_state.get_state_data()
            elif hasattr(self.state_machine.current_state, 'get_phase_data'):
                return self.state_machine.current_state.get_phase_data()
            else:
                # Fallback to basic state info
                return {
                    "phase": self.state_machine.current_phase.name if self.state_machine.current_phase else None,
                    "game_round": getattr(self.state_machine.game, 'round_number', 0) if self.state_machine.game else 0
                }
        except Exception as e:
            logger.error(f"❌ PHASE_DATA: Error getting phase data: {str(e)}")
            return {}