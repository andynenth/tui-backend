# backend/engine/state_machine/action_queue.py

import asyncio
import logging
from typing import AsyncGenerator, List, Optional
from .core import GameAction

# Import EventStore for action persistence
try:
    from api.services.event_store import event_store
    EVENT_STORE_AVAILABLE = True
except ImportError:
    EVENT_STORE_AVAILABLE = False
    event_store = None

class ActionQueue:
    def __init__(self, room_id: Optional[str] = None):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        self.processing_lock = asyncio.Lock()
        self.sequence_counter = 0
        self.room_id = room_id
        self.logger = logging.getLogger("game.action_queue")
        
    async def add_action(self, action: GameAction) -> None:
        action.sequence_id = self.sequence_counter
        self.sequence_counter += 1
        await self.queue.put(action)
        print(f"🔍 ACTION_QUEUE_DEBUG: Queued action: {action.action_type.value} from {action.player_name} (queue size: {self.queue.qsize()})")
        self.logger.debug(f"Queued action: {action.action_type.value} from {action.player_name}")
        
    async def process_actions(self) -> List[GameAction]:
        """
        FIX: Process all queued actions and return them as a list.
        The previous async generator approach had timing issues.
        Enhanced: Now persists actions to EventStore for replay capability.
        """
        async with self.processing_lock:
            self.processing = True
            processed_actions = []
            try:
                # Process all currently queued actions
                # print(f"🔍 ACTION_QUEUE_DEBUG: Processing actions, queue size: {self.queue.qsize()}")
                while not self.queue.empty():
                    action = await self.queue.get()
                    processed_actions.append(action)
                    print(f"🔍 ACTION_QUEUE_DEBUG: Dequeued action: {action.action_type.value} from {action.player_name}")
                    self.logger.debug(f"Processing action: {action.action_type.value}")
                    
                    # Store action in EventStore for persistence and replay
                    await self._store_action_event(action)
                    
                    self.queue.task_done()
            finally:
                self.processing = False
            
            return processed_actions
    
    def has_pending_actions(self) -> bool:
        """Check if there are actions waiting to be processed"""
        return not self.queue.empty()
    
    async def _store_action_event(self, action: GameAction) -> None:
        """
        Store action in EventStore for persistence and replay
        
        Args:
            action: The action to store
        """
        if not EVENT_STORE_AVAILABLE or not event_store or not self.room_id:
            return
        
        try:
            # Convert action to event payload with JSON-safe conversion
            safe_payload = self._make_json_safe(action.payload) if hasattr(action, 'payload') else {}
            payload = {
                'action_type': action.action_type.value,
                'player_name': action.player_name,
                'sequence_id': action.sequence_id,
                'payload': safe_payload
            }
            
            # Store event
            await event_store.store_event(
                room_id=self.room_id,
                event_type='action_processed',
                payload=payload,
                player_id=action.player_name
            )
            
            self.logger.debug(f"Stored action event: {action.action_type.value} for room {self.room_id}")
            
        except Exception as e:
            # Don't let event storage failures break the game
            self.logger.error(f"Failed to store action event: {e}")
    
    async def store_state_event(self, event_type: str, payload: dict, player_id: Optional[str] = None) -> None:
        """
        Store a state change event (called by state machine)
        
        Args:
            event_type: Type of state event (e.g., 'phase_change', 'game_started')
            payload: Event data
            player_id: Optional player identifier
        """
        if not EVENT_STORE_AVAILABLE or not event_store or not self.room_id:
            return
        
        try:
            await event_store.store_event(
                room_id=self.room_id,
                event_type=event_type,
                payload=payload,
                player_id=player_id
            )
            
            self.logger.debug(f"Stored state event: {event_type} for room {self.room_id}")
            
        except Exception as e:
            # Don't let event storage failures break the game
            self.logger.error(f"Failed to store state event: {e}")
    
    def _make_json_safe(self, data):
        """
        Convert data to JSON-safe format, handling Piece objects and other non-serializable types
        """
        from datetime import datetime
        
        if isinstance(data, dict):
            return {key: self._make_json_safe(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_json_safe(item) for item in data]
        elif isinstance(data, datetime):
            return data.timestamp()
        elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
            # Convert objects with attributes (like Piece objects) to string representation
            return str(data)
        else:
            # Already JSON-safe
            return data
