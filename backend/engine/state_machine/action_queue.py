# backend/engine/state_machine/action_queue.py

import asyncio
import logging
from typing import AsyncGenerator, List
from .core import GameAction

class ActionQueue:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        self.processing_lock = asyncio.Lock()
        self.sequence_counter = 0
        self.logger = logging.getLogger("game.action_queue")
        
    async def add_action(self, action: GameAction) -> None:
        action.sequence_id = self.sequence_counter
        self.sequence_counter += 1
        await self.queue.put(action)
        self.logger.debug(f"Queued action: {action.action_type.value} from {action.player_name}")
        
    async def process_actions(self) -> List[GameAction]:
        """
        FIX: Process all queued actions and return them as a list.
        The previous async generator approach had timing issues.
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
                    self.queue.task_done()
            finally:
                self.processing = False
            
            return processed_actions
    
    def has_pending_actions(self) -> bool:
        """Check if there are actions waiting to be processed"""
        return not self.queue.empty()