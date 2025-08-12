# backend/engine/state_machine/action_queue.py

import asyncio
import logging
from typing import AsyncGenerator, List, Optional

from .core import GameAction

# Import EventStore for state event persistence
from backend.api.services.event_store import event_store


class ActionQueue:
    def __init__(self, room_id: str):
        """
        Initialize ActionQueue with required room_id for event persistence

        Args:
            room_id: Required room identifier for event storage
        """
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
        self.logger.debug(
            f"Queued action: {action.action_type.value} from {action.player_name}"
        )

    async def process_actions(self) -> List[GameAction]:
        """
        Process all queued actions and return them as a list.
        
        Note: Raw actions are not stored - only validated state changes from 
        state classes are persisted to maintain data integrity.
        """
        async with self.processing_lock:
            self.processing = True
            processed_actions = []
            try:
                # Process all currently queued actions
                while not self.queue.empty():
                    action = await self.queue.get()
                    processed_actions.append(action)
                    self.logger.debug(f"Processing action: {action.action_type.value}")

                    # Note: Action storage removed - state machine stores validated state changes
                    # This prevents duplicate/invalid bot actions from being persisted

                    self.queue.task_done()
            finally:
                self.processing = False

            return processed_actions

    def has_pending_actions(self) -> bool:
        """Check if there are actions waiting to be processed"""
        return not self.queue.empty()


    async def store_state_event(
        self, event_type: str, payload: dict, player_id: Optional[str] = None
    ) -> None:
        """
        Store a state change event (called by state machine)

        Args:
            event_type: Type of state event (e.g., 'phase_change', 'game_started')
            payload: Event data
            player_id: Optional player identifier
        """
        try:
            # Use buffered storage for 90% write reduction
            await event_store.store_event_buffered(
                room_id=self.room_id,
                event_type=event_type,
                payload=payload,
                player_id=player_id,
            )

            self.logger.debug(
                f"Stored state event (buffered): {event_type} for room {self.room_id}"
            )

        except Exception as e:
            # Don't let event storage failures break the game
            self.logger.error(f"Failed to store state event: {e}")
