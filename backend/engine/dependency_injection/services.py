# backend/engine/dependency_injection/services.py

import asyncio
import logging
from typing import Dict, Set, Optional, Any, List

from .interfaces import IBroadcaster, IBotNotifier, IEventStore, IGameRepository

logger = logging.getLogger(__name__)


class WebSocketBroadcaster(IBroadcaster):
    """
    🎯 **WebSocket Broadcaster Implementation** - Replaces direct socket_manager imports
    
    Provides broadcasting functionality through dependency injection,
    eliminating circular dependencies with socket_manager.
    """
    
    def __init__(self, broadcast_callback: Optional[callable] = None):
        self.broadcast_callback = broadcast_callback
        
    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        if not self.broadcast_callback:
            logger.debug(f"📡 BROADCAST: No callback available for {event_type}")
            return
            
        try:
            await self.broadcast_callback(event_type, event_data)
            logger.debug(f"✅ BROADCAST: {event_type} sent successfully")
        except Exception as e:
            logger.error(f"❌ BROADCAST: Failed to send {event_type}: {str(e)}")
    
    async def broadcast_to_room(self, room_id: str, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to specific room."""
        # Import socket_manager dynamically to avoid circular dependency
        try:
            from backend.socket_manager import broadcast as socket_broadcast
            await socket_broadcast(room_id, event_type, event_data)
            logger.debug(f"✅ ROOM_BROADCAST: {event_type} sent to room {room_id}")
        except ImportError:
            logger.error(f"❌ ROOM_BROADCAST: socket_manager not available")
        except Exception as e:
            logger.error(f"❌ ROOM_BROADCAST: Failed to send {event_type} to room {room_id}: {str(e)}")
    
    async def broadcast_to_player(self, room_id: str, player_name: str, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to specific player."""
        try:
            from backend.socket_manager import broadcast_to_player
            await broadcast_to_player(room_id, player_name, event_type, event_data)
            logger.debug(f"✅ PLAYER_BROADCAST: {event_type} sent to {player_name} in room {room_id}")
        except ImportError:
            logger.error(f"❌ PLAYER_BROADCAST: socket_manager not available")
        except Exception as e:
            logger.error(f"❌ PLAYER_BROADCAST: Failed to send {event_type} to {player_name}: {str(e)}")
    
    async def broadcast_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """Broadcast phase change with proper formatting."""
        formatted_data = {
            "phase": phase,
            "phase_data": phase_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_to_room(room_id, "phase_change", formatted_data)


class BotNotificationService(IBotNotifier):
    """
    🎯 **Bot Notification Service** - Replaces direct bot_manager imports
    
    Provides bot notification functionality through dependency injection,
    eliminating circular dependencies with bot_manager.
    """
    
    async def notify_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """Notify bots of phase change."""
        try:
            # Dynamic import to avoid circular dependency
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            await bot_manager.notify_phase_change(room_id, phase, phase_data)
            logger.debug(f"🤖 BOT_NOTIFICATION: Phase change {phase} sent to room {room_id}")
        except ImportError:
            logger.error(f"❌ BOT_NOTIFICATION: bot_manager not available")
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Failed to notify phase change: {str(e)}")
    
    async def notify_action_result(self, room_id: str, action_type: str, player_name: str, 
                                 success: bool, result: Optional[Dict[str, Any]] = None, 
                                 reason: Optional[str] = None):
        """Notify bots of action results."""
        try:
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            await bot_manager.notify_action_result(
                room_id=room_id,
                action_type=action_type,
                player_name=player_name,
                success=success,
                result=result,
                reason=reason
            )
            logger.debug(f"🤖 BOT_NOTIFICATION: Action result {action_type} sent to room {room_id}")
        except ImportError:
            logger.error(f"❌ BOT_NOTIFICATION: bot_manager not available")
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Failed to notify action result: {str(e)}")
    
    async def notify_data_change(self, room_id: str, data: Dict[str, Any], reason: str):
        """Notify bots of game data changes."""
        try:
            from backend.engine.bot_manager import BotManager
            bot_manager = BotManager()
            await bot_manager.notify_data_change(
                room_id=room_id,
                data=data,
                reason=reason
            )
            logger.debug(f"🤖 BOT_NOTIFICATION: Data change notification sent to room {room_id}")
        except ImportError:
            logger.error(f"❌ BOT_NOTIFICATION: bot_manager not available")
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Failed to notify data change: {str(e)}")


class InMemoryEventStore(IEventStore):
    """
    🎯 **In-Memory Event Store** - Replaces direct event storage dependencies
    
    Provides event storage functionality for game events and debugging.
    Can be easily replaced with persistent storage implementation.
    """
    
    def __init__(self):
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
    
    async def store_event(self, room_id: str, event_data: Dict[str, Any]):
        """Store game event."""
        async with self._lock:
            if room_id not in self._events:
                self._events[room_id] = []
            
            # Add timestamp if not present
            if 'timestamp' not in event_data:
                event_data['timestamp'] = asyncio.get_event_loop().time()
            
            self._events[room_id].append(event_data)
            
            # Keep only last 1000 events per room to prevent memory leaks
            if len(self._events[room_id]) > 1000:
                self._events[room_id] = self._events[room_id][-1000:]
            
            logger.debug(f"📊 EVENT_STORED: {event_data.get('event_type', 'unknown')} for room {room_id}")
    
    async def get_events(self, room_id: str, event_type: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve game events."""
        async with self._lock:
            if room_id not in self._events:
                return []
            
            events = self._events[room_id]
            
            # Filter by event type if specified
            if event_type:
                events = [e for e in events if e.get('event_type') == event_type]
            
            # Apply limit if specified
            if limit:
                events = events[-limit:]
            
            return events.copy()
    
    async def clear_events(self, room_id: str):
        """Clear events for a room."""
        async with self._lock:
            if room_id in self._events:
                del self._events[room_id]
                logger.debug(f"🗑️ EVENTS_CLEARED: Room {room_id}")


class InMemoryGameRepository(IGameRepository):
    """
    🎯 **In-Memory Game Repository** - Replaces direct game state storage dependencies
    
    Provides game state persistence functionality.
    Can be easily replaced with database implementation.
    """
    
    def __init__(self):
        self._game_states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def save_game_state(self, room_id: str, game_state: Dict[str, Any]):
        """Save game state."""
        async with self._lock:
            # Add timestamp
            game_state['saved_at'] = asyncio.get_event_loop().time()
            self._game_states[room_id] = game_state.copy()
            logger.debug(f"💾 GAME_STATE_SAVED: Room {room_id}")
    
    async def load_game_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Load game state."""
        async with self._lock:
            game_state = self._game_states.get(room_id)
            if game_state:
                logger.debug(f"📂 GAME_STATE_LOADED: Room {room_id}")
                return game_state.copy()
            return None
    
    async def delete_game_state(self, room_id: str):
        """Delete game state."""
        async with self._lock:
            if room_id in self._game_states:
                del self._game_states[room_id]
                logger.debug(f"🗑️ GAME_STATE_DELETED: Room {room_id}")


class NullBotNotifier(IBotNotifier):
    """
    🎯 **Null Bot Notifier** - For environments without bot manager
    
    Provides no-op bot notification for testing or environments
    where bot functionality is not needed.
    """
    
    async def notify_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """No-op phase change notification."""
        logger.debug(f"🤖 NULL_BOT: Phase change {phase} ignored for room {room_id}")
    
    async def notify_action_result(self, room_id: str, action_type: str, player_name: str, 
                                 success: bool, result: Optional[Dict[str, Any]] = None, 
                                 reason: Optional[str] = None):
        """No-op action result notification."""
        logger.debug(f"🤖 NULL_BOT: Action result {action_type} ignored for room {room_id}")
    
    async def notify_data_change(self, room_id: str, data: Dict[str, Any], reason: str):
        """No-op data change notification."""
        logger.debug(f"🤖 NULL_BOT: Data change ignored for room {room_id}")


class NullBroadcaster(IBroadcaster):
    """
    🎯 **Null Broadcaster** - For testing or offline environments
    
    Provides no-op broadcasting for testing environments.
    """
    
    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]):
        """No-op event broadcast."""
        logger.debug(f"📡 NULL_BROADCAST: {event_type} ignored")
    
    async def broadcast_to_room(self, room_id: str, event_type: str, event_data: Dict[str, Any]):
        """No-op room broadcast."""
        logger.debug(f"📡 NULL_BROADCAST: {event_type} ignored for room {room_id}")
    
    async def broadcast_to_player(self, room_id: str, player_name: str, event_type: str, event_data: Dict[str, Any]):
        """No-op player broadcast."""
        logger.debug(f"📡 NULL_BROADCAST: {event_type} ignored for player {player_name}")
    
    async def broadcast_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """No-op phase change broadcast."""
        logger.debug(f"📡 NULL_BROADCAST: Phase change {phase} ignored for room {room_id}")