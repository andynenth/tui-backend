# backend/api/events/GameEvents.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import asyncio
import time
import uuid
import logging

class GameEventType(Enum):

    
    # Game lifecycle
    GAME_STARTED = "game_started"
    GAME_STATE_UPDATE = "game_state_update"
    PHASE_TRANSITION = "phase_transition"
    
    # Preparation phase
    PREPARATION_STARTED = "preparation_started"
    INITIAL_HAND_DEALT = "initial_hand_dealt"
    WEAK_HAND_CHECK = "weak_hand_check"
    
    # Redeal sub-phase
    REDEAL_DECISION_REQUEST = "redeal_decision_request"
    REDEAL_EXECUTED = "redeal_executed"
    
    # Player actions (from frontend)
    PLAYER_READY = "player_ready"
    PLAYER_ACTION = "player_action"
    REDEAL_DECISION = "redeal_decision"
    
    # Redeal events
    REDEAL_PHASE_STARTED = "redeal_phase_started"
    REDEAL_PROMPT = "redeal_prompt"
    REDEAL_WAITING = "redeal_waiting"
    REDEAL_DECISION_MADE = "redeal_decision_made"
    REDEAL_NEW_HAND = "redeal_new_hand"
    PLAYER_REDEALT = "player_redealt"
    REDEAL_PHASE_COMPLETE = "redeal_phase_complete"
    
    # Declaration events
    DECLARATION_PHASE_STARTED = "declaration_phase_started"
    DECLARATION_PROMPT = "declaration_prompt"
    DECLARATION_MADE = "declaration_made"
    DECLARATION_PHASE_COMPLETE = "declaration_phase_complete"
    
    # Turn events
    TURN_PHASE_STARTED = "turn_phase_started"
    TURN_PROMPT = "turn_prompt"
    TURN_PLAYED = "turn_played"
    TURN_COMPLETE = "turn_complete"
    TURN_PHASE_COMPLETE = "turn_phase_complete"
    
    # Scoring events
    SCORING_PHASE_STARTED = "scoring_phase_started"
    ROUND_SCORED = "round_scored"
    SCORING_PHASE_COMPLETE = "scoring_phase_complete"
    
    # Phase transition events
    PHASE_TRANSITION = "phase_transition"
    PHASE_ERROR = "phase_error"
    
    # General game events
    GAME_STATE_UPDATED = "game_state_updated"
    PLAYER_ACTION = "player_action"
    GAME_COMPLETE = "game_complete"

@dataclass
class GameEvent:
    """Standard game event structure"""
    event_type: GameEventType
    room_id: str
    data: Dict[str, Any]
    player_id: Optional[str] = None
    timestamp: Optional[float] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
            
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

class EventBus:
    """Simple event bus สำหรับ internal communication"""
    
    def __init__(self):
        self.handlers = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def subscribe(self, event_type: GameEventType, handler):
        """Subscribe to event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        self.logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: GameEventType, handler):
        """Unsubscribe from event type"""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                self.logger.debug(f"Unsubscribed from {event_type.value}")
            except ValueError:
                pass  # Handler not found
    
    async def publish(self, event: GameEvent):
        """Publish event to subscribers"""
        self.logger.debug(f"Publishing event: {event.event_type.value} for room {event.room_id}")
        
        if event.event_type in self.handlers:
            tasks = []
            for handler in self.handlers[event.event_type]:
                try:
                    tasks.append(handler(event))
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

# Global event bus instance
game_event_bus = EventBus()