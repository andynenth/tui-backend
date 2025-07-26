"""
Schedule bot action use case.

This use case ensures bot actions have realistic delays to simulate
human thinking time.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Optional

from application.interfaces.services import MetricsCollector
from application.dto.common import BaseRequest, BaseResponse
from application.exceptions import ApplicationException


@dataclass
class ScheduleBotActionRequest(BaseRequest):
    """Request to schedule a bot action."""
    player_name: str
    action_type: str
    room_id: str
    min_delay: float = 0.5
    max_delay: float = 1.5


@dataclass
class ScheduleBotActionResponse(BaseResponse):
    """Response from scheduling bot action."""
    scheduled: bool = False
    delay_seconds: float = 0.0


class ScheduleBotActionUseCase:
    """
    Schedule a bot action with realistic delay.
    
    This use case:
    1. Calculates a random delay within the specified range
    2. Waits for the delay to simulate thinking
    3. Returns when the bot should act
    
    The delays match the current system:
    - Default: 0.5-1.5 seconds
    - Can be customized per action type
    """
    
    def __init__(self, metrics: Optional[MetricsCollector] = None):
        self._metrics = metrics
    
    async def execute(self, request: ScheduleBotActionRequest) -> ScheduleBotActionResponse:
        """Execute the use case."""
        try:
            # Validate delay range
            if request.min_delay < 0 or request.max_delay < 0:
                raise ValueError("Delays must be non-negative")
            
            if request.min_delay > request.max_delay:
                raise ValueError("Min delay must be less than or equal to max delay")
            
            # Calculate delay (matching current bot_manager.py implementation)
            delay = random.uniform(request.min_delay, request.max_delay)
            
            # Record metrics before delay
            if self._metrics:
                self._metrics.increment(
                    "bot.action.scheduled",
                    tags={
                        "action_type": request.action_type,
                        "player": request.player_name
                    }
                )
                self._metrics.histogram(
                    "bot.action.delay",
                    delay,
                    tags={"action_type": request.action_type}
                )
            
            # Wait for the delay
            await asyncio.sleep(delay)
            
            # Record completion
            if self._metrics:
                self._metrics.increment(
                    "bot.action.ready",
                    tags={
                        "action_type": request.action_type,
                        "player": request.player_name
                    }
                )
            
            return ScheduleBotActionResponse(
                success=True,
                scheduled=True,
                delay_seconds=delay
            )
            
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            if self._metrics:
                self._metrics.increment("bot.action.cancelled")
            raise
            
        except Exception as e:
            if self._metrics:
                self._metrics.increment("bot.action.error")
            
            raise ApplicationException(
                f"Failed to schedule bot action: {str(e)}",
                code="BOT_SCHEDULE_FAILED"
            )