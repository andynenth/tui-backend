"""
Integration between Enterprise Architecture and Event System.

This module connects the state machine's update_phase_data() method
with the domain event system, enabling automatic event publishing
whenever state changes occur.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import domain events
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domain.events.all_events import (
    PhaseChanged, TurnStarted, TurnWinnerDetermined,
    RoundStarted, RoundEnded, ScoresCalculated,
    GameEnded, EventMetadata
)
from infrastructure.events.in_memory_event_bus import get_event_bus
from .core import GamePhase

logger = logging.getLogger(__name__)


class StateChangeEventPublisher:
    """
    Publishes domain events when state machine phase data changes.
    
    This integrates with the enterprise architecture's update_phase_data()
    to automatically publish events without modifying existing code.
    """
    
    def __init__(self):
        """Initialize the event publisher."""
        self.event_bus = get_event_bus()
        self._last_phase = None
        self._enabled = False  # Start disabled, enable via config
    
    async def on_phase_data_update(
        self,
        state_machine,
        phase: GamePhase,
        updates: Dict[str, Any],
        old_data: Dict[str, Any],
        reason: str
    ):
        """
        Called when phase data is updated via update_phase_data().
        
        Args:
            state_machine: The game state machine instance
            phase: Current game phase
            updates: The updates being applied
            old_data: Previous phase data
            reason: Human-readable reason for change
        """
        if not self._enabled:
            return
        
        try:
            room_id = getattr(state_machine, "room_id", None)
            if not room_id:
                return
            
            # Create base metadata
            metadata = EventMetadata(
                user_id="system",  # State changes are system events
                correlation_id=f"state_{state_machine._sequence_number}"
            )
            
            # Detect phase transitions
            if self._last_phase != phase:
                await self._publish_phase_change(room_id, self._last_phase, phase, metadata)
                self._last_phase = phase
            
            # Publish specific events based on updates and phase
            await self._publish_phase_specific_events(
                room_id, phase, updates, old_data, reason, metadata
            )
            
        except Exception as e:
            logger.error(f"Error publishing state change events: {e}", exc_info=True)
    
    async def _publish_phase_change(
        self,
        room_id: str,
        old_phase: Optional[GamePhase],
        new_phase: GamePhase,
        metadata: EventMetadata
    ):
        """Publish phase transition event."""
        event = PhaseChanged(
            room_id=room_id,
            old_phase=old_phase.value if old_phase else None,
            new_phase=new_phase.value,
            metadata=metadata
        )
        await self.event_bus.publish(event)
    
    async def _publish_phase_specific_events(
        self,
        room_id: str,
        phase: GamePhase,
        updates: Dict[str, Any],
        old_data: Dict[str, Any],
        reason: str,
        metadata: EventMetadata
    ):
        """Publish events specific to the current phase and updates."""
        
        # Turn phase events
        if phase == GamePhase.TURN:
            await self._handle_turn_phase_events(room_id, updates, old_data, metadata)
        
        # Scoring phase events
        elif phase == GamePhase.SCORING:
            await self._handle_scoring_phase_events(room_id, updates, old_data, metadata)
        
        # Round transitions
        if "round_number" in updates and updates["round_number"] != old_data.get("round_number"):
            await self._handle_round_transition(room_id, updates, old_data, metadata)
        
        # Game end
        if "game_over" in updates and updates["game_over"]:
            await self._handle_game_end(room_id, updates, metadata)
    
    async def _handle_turn_phase_events(
        self,
        room_id: str,
        updates: Dict[str, Any],
        old_data: Dict[str, Any],
        metadata: EventMetadata
    ):
        """Handle events specific to turn phase."""
        
        # New turn started
        if "current_player" in updates and updates["current_player"] != old_data.get("current_player"):
            turn_number = updates.get("turn_number", old_data.get("turn_number", 1))
            event = TurnStarted(
                room_id=room_id,
                player_name=updates["current_player"],
                turn_number=turn_number,
                metadata=metadata
            )
            await self.event_bus.publish(event)
        
        # Turn winner determined
        if "turn_winner" in updates and updates["turn_winner"]:
            event = TurnWinnerDetermined(
                room_id=room_id,
                winner_name=updates["turn_winner"],
                played_pieces=updates.get("winning_pieces", []),
                metadata=metadata
            )
            await self.event_bus.publish(event)
    
    async def _handle_scoring_phase_events(
        self,
        room_id: str,
        updates: Dict[str, Any],
        old_data: Dict[str, Any],
        metadata: EventMetadata
    ):
        """Handle events specific to scoring phase."""
        
        # Scores calculated
        if "scores" in updates:
            event = ScoresCalculated(
                room_id=room_id,
                scores=updates["scores"],
                round_number=updates.get("round_number", 1),
                metadata=metadata
            )
            await self.event_bus.publish(event)
    
    async def _handle_round_transition(
        self,
        room_id: str,
        updates: Dict[str, Any],
        old_data: Dict[str, Any],
        metadata: EventMetadata
    ):
        """Handle round start/end events."""
        
        old_round = old_data.get("round_number", 0)
        new_round = updates["round_number"]
        
        # Round ended (if not first round)
        if old_round > 0 and old_round < new_round:
            event = RoundEnded(
                room_id=room_id,
                round_number=old_round,
                scores={},  # Would get from game state
                metadata=metadata
            )
            await self.event_bus.publish(event)
        
        # New round started
        if new_round > old_round:
            event = RoundStarted(
                room_id=room_id,
                round_number=new_round,
                starter_player=updates.get("starter_player", "Unknown"),
                metadata=metadata
            )
            await self.event_bus.publish(event)
    
    async def _handle_game_end(
        self,
        room_id: str,
        updates: Dict[str, Any],
        metadata: EventMetadata
    ):
        """Handle game end event."""
        
        event = GameEnded(
            room_id=room_id,
            winner_name=updates.get("winner", "Unknown"),
            final_scores=updates.get("final_scores", {}),
            total_rounds=updates.get("total_rounds", 0),
            metadata=metadata
        )
        await self.event_bus.publish(event)
    
    def enable(self):
        """Enable event publishing."""
        self._enabled = True
        logger.info("State change event publishing enabled")
    
    def disable(self):
        """Disable event publishing."""
        self._enabled = False
        logger.info("State change event publishing disabled")


# Global instance
_state_event_publisher = StateChangeEventPublisher()


def get_state_event_publisher() -> StateChangeEventPublisher:
    """Get the global state event publisher instance."""
    return _state_event_publisher


async def publish_state_change_events(
    state_machine,
    phase: GamePhase,
    updates: Dict[str, Any],
    old_data: Dict[str, Any],
    reason: str
):
    """
    Convenience function to publish state change events.
    
    This should be called from update_phase_data() in the base state.
    """
    await _state_event_publisher.on_phase_data_update(
        state_machine, phase, updates, old_data, reason
    )