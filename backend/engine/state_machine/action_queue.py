# backend/engine/state_machine/action_queue.py

import asyncio
import logging
from typing import AsyncGenerator, List, Optional

from .core import GameAction

# Import EventStore for action persistence
from api.services.event_store import event_store


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
        FIX: Process all queued actions and return them as a list.
        The previous async generator approach had timing issues.
        Enhanced: Now persists actions to EventStore for replay capability.
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
        try:
            # Deep copy payload to avoid modifying original
            serializable_payload = {}
            if hasattr(action, "payload") and action.payload:
                for key, value in action.payload.items():
                    if key == "pieces" and isinstance(value, list):
                        # Convert Piece objects to dictionaries
                        serializable_payload[key] = [
                            piece.to_dict() if hasattr(piece, "to_dict") else str(piece)
                            for piece in value
                        ]
                    else:
                        serializable_payload[key] = value

            # Convert action to event payload
            payload = {
                "action_type": action.action_type.value,
                "player_name": action.player_name,
                "sequence_id": action.sequence_id,
                "payload": serializable_payload,
            }

            # Store event
            await event_store.store_event(
                room_id=self.room_id,
                event_type="action_processed",
                payload=payload,
                player_id=action.player_name,
            )

            self.logger.debug(
                f"Stored action event: {action.action_type.value} for room {self.room_id}"
            )

        except Exception as e:
            # Don't let event storage failures break the game
            self.logger.error(f"Failed to store action event: {e}")

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
            await event_store.store_event(
                room_id=self.room_id,
                event_type=event_type,
                payload=payload,
                player_id=player_id,
            )

            self.logger.debug(
                f"Stored state event: {event_type} for room {self.room_id}"
            )

        except Exception as e:
            # Don't let event storage failures break the game
            self.logger.error(f"Failed to store state event: {e}")
