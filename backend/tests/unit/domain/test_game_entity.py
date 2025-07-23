# tests/unit/domain/test_game_entity.py
"""
Unit tests for Game entity.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from domain.entities.game import Game
from domain.entities.player import Player
from domain.value_objects.game_state import GamePhase
from domain.events.game_events import (
    GameStartedEvent,
    RoundStartedEvent,
    GameEndedEvent,
    WinnerDeterminedEvent
)
from tests.fixtures.domain_fixtures import (
    create_test_players,
    create_test_game,
    TestEventCapture
)


class TestGameEntity:
    """Test Game entity behavior."""
    
    @pytest.mark.asyncio
    async def test_game_initialization(self):
        """Test game initializes with correct defaults."""
        players = create_test_players(4)
        game = create_test_game(players=players)
        
        assert len(game.players) == 4
        assert game.max_score == 50
        assert game.max_rounds == 20
        assert game.round_number == 1
        assert game.current_phase == GamePhase.WAITING
        assert game.turn_number == 0
        assert not game.is_started
        assert not game.is_ended
    
    @pytest.mark.asyncio
    async def test_game_start_publishes_event(self):
        """Test starting game publishes GameStartedEvent."""
        event_capture = TestEventCapture()
        players = create_test_players(4)
        game = Game(
            players=players,
            event_publisher=event_capture.mock_publisher
        )
        
        await game.start()
        
        # Verify game state
        assert game.is_started
        assert game.current_phase == GamePhase.PREPARATION
        
        # Verify event published
        events = event_capture.get_events_of_type(GameStartedEvent)
        assert len(events) == 1
        
        event = events[0]
        assert event.aggregate_id == game.id
        assert len(event.data["players"]) == 4
        assert event.data["initial_phase"] == "PREPARATION"
    
    @pytest.mark.asyncio
    async def test_cannot_start_already_started_game(self):
        """Test cannot start a game that's already started."""
        game = create_test_game()
        await game.start()
        
        with pytest.raises(ValueError, match="already started"):
            await game.start()
    
    @pytest.mark.asyncio
    async def test_game_requires_minimum_players(self):
        """Test game requires at least 2 players to start."""
        game = create_test_game(players=[create_test_players(1)[0]])
        
        with pytest.raises(ValueError, match="at least 2 players"):
            await game.start()
    
    @pytest.mark.asyncio
    async def test_start_round_publishes_event(self):
        """Test starting round publishes RoundStartedEvent."""
        event_capture = TestEventCapture()
        players = create_test_players(4)
        game = Game(
            players=players,
            event_publisher=event_capture.mock_publisher
        )
        
        await game.start()
        event_capture.clear()
        
        await game.start_round()
        
        # Verify round state
        assert game.current_phase == GamePhase.PREPARATION
        
        # Verify event
        events = event_capture.get_events_of_type(RoundStartedEvent)
        assert len(events) == 1
        
        event = events[0]
        assert event.data["round_number"] == 1
        assert event.data["dealer"] in [p.name for p in players]
    
    @pytest.mark.asyncio
    async def test_add_score_updates_totals(self):
        """Test adding scores updates player totals."""
        game = create_test_game()
        await game.start()
        
        scores = {
            "Player1": 10,
            "Player2": -5,
            "Player3": 0,
            "Player4": 15
        }
        
        game.add_round_scores(scores)
        
        assert game.get_total_score("Player1") == 10
        assert game.get_total_score("Player2") == -5
        assert game.get_total_score("Player3") == 0
        assert game.get_total_score("Player4") == 15
    
    @pytest.mark.asyncio
    async def test_check_win_condition_by_score(self):
        """Test game ends when player reaches max score."""
        event_capture = TestEventCapture()
        game = Game(
            players=create_test_players(4),
            max_score=50,
            event_publisher=event_capture.mock_publisher
        )
        
        await game.start()
        event_capture.clear()
        
        # Add scores to trigger win
        scores = {
            "Player1": 51,
            "Player2": 20,
            "Player3": 30,
            "Player4": 40
        }
        game.add_round_scores(scores)
        
        result = await game.check_win_condition()
        
        assert result is True
        assert game.is_ended
        
        # Verify events
        winner_events = event_capture.get_events_of_type(WinnerDeterminedEvent)
        assert len(winner_events) == 1
        assert winner_events[0].data["winner"] == "Player1"
        assert winner_events[0].data["score"] == 51
        
        ended_events = event_capture.get_events_of_type(GameEndedEvent)
        assert len(ended_events) == 1
        assert ended_events[0].data["winner"] == "Player1"
        assert ended_events[0].data["reason"] == "score_limit"
    
    @pytest.mark.asyncio
    async def test_check_win_condition_by_rounds(self):
        """Test game ends after max rounds."""
        event_capture = TestEventCapture()
        game = Game(
            players=create_test_players(4),
            max_rounds=2,
            event_publisher=event_capture.mock_publisher
        )
        
        await game.start()
        
        # Play rounds without hitting score limit
        for round_num in range(1, 3):
            scores = {"Player1": 10, "Player2": 10, "Player3": 10, "Player4": 10}
            game.add_round_scores(scores)
            game._round_number = round_num + 1
        
        event_capture.clear()
        result = await game.check_win_condition()
        
        assert result is True
        assert game.is_ended
        
        # Verify ended event
        ended_events = event_capture.get_events_of_type(GameEndedEvent)
        assert len(ended_events) == 1
        assert ended_events[0].data["reason"] == "round_limit"
    
    def test_get_player_by_name(self):
        """Test getting player by name."""
        players = create_test_players(4)
        game = create_test_game(players=players)
        
        player = game.get_player("Player2")
        assert player is not None
        assert player.name == "Player2"
        
        # Non-existent player
        assert game.get_player("NonExistent") is None
    
    def test_phase_transitions(self):
        """Test phase transition validation."""
        game = create_test_game()
        
        # Valid transitions
        assert game.can_transition_to(GamePhase.WAITING, GamePhase.PREPARATION)
        assert game.can_transition_to(GamePhase.PREPARATION, GamePhase.DECLARATION)
        assert game.can_transition_to(GamePhase.DECLARATION, GamePhase.TURN)
        assert game.can_transition_to(GamePhase.TURN, GamePhase.SCORING)
        assert game.can_transition_to(GamePhase.SCORING, GamePhase.PREPARATION)
        
        # Invalid transitions
        assert not game.can_transition_to(GamePhase.WAITING, GamePhase.TURN)
        assert not game.can_transition_to(GamePhase.TURN, GamePhase.DECLARATION)
    
    def test_game_state_serialization(self):
        """Test game state can be serialized."""
        game = create_test_game()
        state = game.to_dict()
        
        assert "id" in state
        assert "players" in state
        assert "round_number" in state
        assert "current_phase" in state
        assert "scores" in state
        assert "is_started" in state
        assert "is_ended" in state
        
        # Verify players are serialized
        assert len(state["players"]) == 4
        assert all("name" in p for p in state["players"])