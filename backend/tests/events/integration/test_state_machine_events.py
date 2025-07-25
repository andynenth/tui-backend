"""
Integration tests for state machine event publishing.

Tests that the enterprise architecture integration with the event system
works correctly when state changes occur.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from engine.state_machine.base_state import GameState
from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.state_machine.event_integration import (
    StateChangeEventPublisher, get_state_event_publisher
)
from engine.state_machine.event_config import StateEventConfig

from backend.domain.events.base import DomainEvent
from backend.domain.events.all_events import (
    PhaseChanged, TurnStarted, TurnWinnerDetermined,
    RoundStarted, RoundEnded, ScoresCalculated, GameEnded,
    CustomGameEvent
)
from backend.infrastructure.events.in_memory_event_bus import (
    get_event_bus, reset_event_bus
)


class MockStateMachine:
    """Mock state machine for testing."""
    def __init__(self, room_id: str = "room123"):
        self.room_id = room_id
        self._sequence_number = 0
        self.game = Mock()
        self.game.round_number = 1


class TestState(GameState):
    """Concrete test state implementation."""
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.TURN
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.SCORING]
    
    async def _setup_phase(self) -> None:
        self.allowed_actions = {ActionType.PLAY}
    
    async def _cleanup_phase(self) -> None:
        pass
    
    async def _validate_action(self, action: GameAction) -> bool:
        return True
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        return {"success": True}
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        return None


class TestStateChangeEventPublisher:
    """Test the StateChangeEventPublisher."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus and publisher before each test."""
        reset_event_bus()
        publisher = get_state_event_publisher()
        publisher._enabled = False
        publisher._last_phase = None
        self.published_events = []
        
        # Track published events
        async def track_event(event: DomainEvent):
            self.published_events.append(event)
        
        bus = get_event_bus()
        bus.subscribe(DomainEvent, track_event)
    
    @pytest.fixture
    def publisher(self):
        """Get the state event publisher."""
        publisher = get_state_event_publisher()
        publisher.enable()
        return publisher
    
    @pytest.fixture
    def state_machine(self):
        """Create a mock state machine."""
        return MockStateMachine()
    
    async def test_phase_change_event_published(self, publisher, state_machine):
        """Test that phase changes publish PhaseChanged events."""
        # Simulate phase change from None to TURN
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.TURN,
            {"current_player": "Alice"},
            {},
            "Game started"
        )
        
        # Should publish PhaseChanged
        phase_events = [e for e in self.published_events if isinstance(e, PhaseChanged)]
        assert len(phase_events) == 1
        
        event = phase_events[0]
        assert event.room_id == "room123"
        assert event.old_phase is None
        assert event.new_phase == "TURN"
    
    async def test_turn_started_event_published(self, publisher, state_machine):
        """Test that turn changes publish TurnStarted events."""
        publisher._last_phase = GamePhase.TURN
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.TURN,
            {"current_player": "Bob", "turn_number": 2},
            {"current_player": "Alice", "turn_number": 1},
            "Bob's turn"
        )
        
        # Should publish TurnStarted
        turn_events = [e for e in self.published_events if isinstance(e, TurnStarted)]
        assert len(turn_events) == 1
        
        event = turn_events[0]
        assert event.room_id == "room123"
        assert event.player_name == "Bob"
        assert event.turn_number == 2
    
    async def test_turn_winner_event_published(self, publisher, state_machine):
        """Test that turn winner updates publish TurnWinnerDetermined events."""
        publisher._last_phase = GamePhase.TURN
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.TURN,
            {
                "turn_winner": "Alice",
                "winning_pieces": ["K", "K", "K"]
            },
            {},
            "Alice won the turn"
        )
        
        # Should publish TurnWinnerDetermined
        winner_events = [e for e in self.published_events if isinstance(e, TurnWinnerDetermined)]
        assert len(winner_events) == 1
        
        event = winner_events[0]
        assert event.room_id == "room123"
        assert event.winner_name == "Alice"
        assert event.played_pieces == ["K", "K", "K"]
    
    async def test_scoring_event_published(self, publisher, state_machine):
        """Test that score updates publish ScoresCalculated events."""
        publisher._last_phase = GamePhase.SCORING
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.SCORING,
            {
                "scores": {
                    "Alice": 10,
                    "Bob": -5,
                    "Carol": 0
                },
                "round_number": 1
            },
            {},
            "Scores calculated"
        )
        
        # Should publish ScoresCalculated
        score_events = [e for e in self.published_events if isinstance(e, ScoresCalculated)]
        assert len(score_events) == 1
        
        event = score_events[0]
        assert event.room_id == "room123"
        assert event.scores == {"Alice": 10, "Bob": -5, "Carol": 0}
        assert event.round_number == 1
    
    async def test_round_transition_events(self, publisher, state_machine):
        """Test that round transitions publish appropriate events."""
        publisher._last_phase = GamePhase.PREPARATION
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.PREPARATION,
            {
                "round_number": 2,
                "starter_player": "Bob"
            },
            {"round_number": 1},
            "New round started"
        )
        
        # Should publish RoundEnded and RoundStarted
        ended_events = [e for e in self.published_events if isinstance(e, RoundEnded)]
        started_events = [e for e in self.published_events if isinstance(e, RoundStarted)]
        
        assert len(ended_events) == 1
        assert len(started_events) == 1
        
        # Check RoundEnded
        ended = ended_events[0]
        assert ended.room_id == "room123"
        assert ended.round_number == 1
        
        # Check RoundStarted
        started = started_events[0]
        assert started.room_id == "room123"
        assert started.round_number == 2
        assert started.starter_player == "Bob"
    
    async def test_game_ended_event(self, publisher, state_machine):
        """Test that game end publishes GameEnded event."""
        publisher._last_phase = GamePhase.SCORING
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.SCORING,
            {
                "game_over": True,
                "winner": "Alice",
                "final_scores": {
                    "Alice": 55,
                    "Bob": 45,
                    "Carol": 30
                },
                "total_rounds": 10
            },
            {},
            "Game ended"
        )
        
        # Should publish GameEnded
        ended_events = [e for e in self.published_events if isinstance(e, GameEnded)]
        assert len(ended_events) == 1
        
        event = ended_events[0]
        assert event.room_id == "room123"
        assert event.winner_name == "Alice"
        assert event.final_scores == {"Alice": 55, "Bob": 45, "Carol": 30}
        assert event.total_rounds == 10
    
    async def test_disabled_publisher_publishes_nothing(self, state_machine):
        """Test that disabled publisher doesn't publish events."""
        publisher = get_state_event_publisher()
        publisher.disable()
        
        await publisher.on_phase_data_update(
            state_machine,
            GamePhase.TURN,
            {"current_player": "Alice"},
            {},
            "Test update"
        )
        
        # No events should be published
        assert len(self.published_events) == 0


class TestStateMachineIntegration:
    """Test the integration with actual state machine."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus before each test."""
        reset_event_bus()
        self.published_events = []
        
        # Track published events
        async def track_event(event: DomainEvent):
            self.published_events.append(event)
        
        bus = get_event_bus()
        bus.subscribe(DomainEvent, track_event)
    
    @pytest.fixture
    def state_machine(self):
        """Create a mock state machine."""
        return MockStateMachine()
    
    @pytest.fixture
    def test_state(self, state_machine):
        """Create a test state."""
        return TestState(state_machine)
    
    async def test_update_phase_data_publishes_events(self, test_state):
        """Test that update_phase_data() publishes events."""
        # Enable event publishing
        publisher = get_state_event_publisher()
        publisher.enable()
        
        # Mock broadcast to avoid import issues
        with patch('engine.state_machine.base_state.broadcast', new_callable=AsyncMock):
            # Update phase data
            await test_state.update_phase_data(
                {
                    "current_player": "Alice",
                    "turn_number": 1
                },
                "Alice's turn started"
            )
        
        # Should have published TurnStarted event
        turn_events = [e for e in self.published_events if isinstance(e, TurnStarted)]
        assert len(turn_events) == 1
        
        event = turn_events[0]
        assert event.room_id == "room123"
        assert event.player_name == "Alice"
        assert event.turn_number == 1
    
    async def test_broadcast_custom_event_publishes_events(self, test_state):
        """Test that broadcast_custom_event() publishes CustomGameEvent."""
        # Enable event publishing
        publisher = get_state_event_publisher()
        publisher.enable()
        
        # Mock broadcast
        with patch('engine.state_machine.base_state.broadcast', new_callable=AsyncMock):
            # Broadcast custom event
            await test_state.broadcast_custom_event(
                "special_bonus",
                {
                    "player": "Alice",
                    "bonus": 10
                },
                "Special bonus awarded"
            )
        
        # Should have published CustomGameEvent
        custom_events = [e for e in self.published_events if isinstance(e, CustomGameEvent)]
        assert len(custom_events) == 1
        
        event = custom_events[0]
        assert event.room_id == "room123"
        assert event.event_type == "special_bonus"
        assert event.data["player"] == "Alice"
        assert event.data["bonus"] == 10
    
    async def test_event_publishing_error_handling(self, test_state):
        """Test that event publishing errors don't break state updates."""
        # Enable event publishing
        publisher = get_state_event_publisher()
        publisher.enable()
        
        # Make event bus raise error
        bus = get_event_bus()
        original_publish = bus.publish
        
        async def error_publish(event):
            raise ValueError("Event bus error")
        
        bus.publish = error_publish
        
        try:
            # Mock broadcast
            with patch('engine.state_machine.base_state.broadcast', new_callable=AsyncMock):
                # Update should still work despite event error
                await test_state.update_phase_data(
                    {"test": "data"},
                    "Test update"
                )
            
            # Phase data should be updated
            assert test_state.phase_data["test"] == "data"
            
        finally:
            # Restore original publish
            bus.publish = original_publish


class TestEventConfiguration:
    """Test the event configuration system."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = StateEventConfig()
        
        # Default should be disabled
        assert config.events_enabled is False
        assert config.phase_change_events is True
        assert config.turn_events is True
        assert config.scoring_events is True
        assert config.custom_events is True
    
    def test_environment_configuration(self):
        """Test configuration from environment variables."""
        env_vars = {
            "STATE_EVENTS_ENABLED": "true",
            "STATE_PHASE_CHANGE_EVENTS": "false",
            "STATE_TURN_EVENTS": "true",
            "STATE_SCORING_EVENTS": "false",
            "STATE_CUSTOM_EVENTS": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = StateEventConfig()
            
            assert config.events_enabled is True
            assert config.phase_change_events is False
            assert config.turn_events is True
            assert config.scoring_events is False
            assert config.custom_events is True
    
    def test_enable_disable_methods(self):
        """Test enable/disable methods."""
        config = StateEventConfig()
        
        # Start disabled
        assert config.events_enabled is False
        
        # Enable
        config.enable()
        assert config.events_enabled is True
        
        # Disable
        config.disable()
        assert config.events_enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])