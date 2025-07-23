# tests/fixtures/domain_fixtures.py
"""
Test fixtures for domain layer testing.
"""

from typing import List
from unittest.mock import Mock, AsyncMock

from domain.entities.player import Player
from domain.entities.piece import Piece, PieceDeck
from domain.entities.game import Game
from domain.value_objects.game_state import GamePhase
from domain.interfaces.event_publisher import EventPublisher


def create_test_player(
    name: str = "TestPlayer",
    is_bot: bool = False,
    is_ready: bool = True
) -> Player:
    """Create a test player."""
    return Player(name=name, is_bot=is_bot, is_ready=is_ready)


def create_test_players(count: int = 4) -> List[Player]:
    """Create multiple test players."""
    return [create_test_player(f"Player{i+1}") for i in range(count)]


def create_test_piece(face: int, points: int = None) -> Piece:
    """Create a test piece."""
    if points is None:
        points = face
    return Piece(face=face, points=points)


def create_test_game(
    players: List[Player] = None,
    max_score: int = 50,
    max_rounds: int = 20
) -> Game:
    """Create a test game with mock event publisher."""
    if players is None:
        players = create_test_players()
    
    mock_publisher = Mock(spec=EventPublisher)
    mock_publisher.publish = AsyncMock()
    
    return Game(
        players=players,
        max_score=max_score,
        max_rounds=max_rounds,
        event_publisher=mock_publisher
    )


def create_mock_event_publisher() -> Mock:
    """Create a mock event publisher."""
    mock = Mock(spec=EventPublisher)
    mock.publish = AsyncMock()
    return mock


class TestEventCapture:
    """Helper to capture published events for testing."""
    
    def __init__(self):
        self.events = []
        self.mock_publisher = create_mock_event_publisher()
        self.mock_publisher.publish.side_effect = self._capture_event
    
    async def _capture_event(self, event):
        """Capture published event."""
        self.events.append(event)
    
    def get_events_of_type(self, event_type):
        """Get all captured events of a specific type."""
        return [e for e in self.events if isinstance(e, event_type)]
    
    def clear(self):
        """Clear captured events."""
        self.events.clear()