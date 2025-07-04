# backend/test_game_over_transition.py

"""
Game Over Transition Test
Tests that the game properly transitions to GAME_OVER phase after finding a winner
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.states.scoring_state import ScoringState
from engine.state_machine.states.game_over_state import GameOverState
from engine.win_conditions import WinConditionType


class MockPlayer:
    """Mock player for testing"""
    def __init__(self, name, score=0, is_bot=False, captured_piles=0):
        self.name = name
        self.score = score
        self.is_bot = is_bot
        self.hand = []
        self.captured_piles = captured_piles  # This determines the actual pile count
        
    def __str__(self):
        return self.name


class MockGameForGameOver:
    """Mock game that simulates a completed game with a winner"""
    
    def __init__(self, winner_name="Andy", winner_score=51):
        # Create players with one having winning score
        # Set up captured_piles so that with declarations, the winner will reach the target score
        self.players = [
            MockPlayer("Andy", 42, False, 4),  # Andy: 42 + 9 (perfect 4-pile declaration) = 51
            MockPlayer("Bot 2", 38, True, 4),   # Bot 2: 38 - 3 (declared 1, got 4) = 35  
            MockPlayer("Bot 3", 31, True, 0),   # Bot 3: 31 - 1 (declared 1, got 0) = 30
            MockPlayer("Bot 4", 26, True, 0)    # Bot 4: 26 - 1 (declared 1, got 0) = 25
        ]
        
        # Game state
        self.round_number = 13
        self.max_score = 50
        self.max_rounds = 20
        self.win_condition_type = WinConditionType.FIRST_TO_REACH_50
        
        # Timing
        self.start_time = 1000000000  # Mock timestamp
        self.end_time = None  # Will be set by GameOverState
        
        # Round data
        self.current_order = [p.name for p in self.players]
        self.player_declarations = {
            "Andy": 4,
            "Bot 2": 1, 
            "Bot 3": 1,
            "Bot 4": 1
        }
        
        # Round scores (final round)
        self.round_scores = {
            "Andy": 9,   # Perfect declaration
            "Bot 2": -3, # Missed declaration
            "Bot 3": -1, # Close miss
            "Bot 4": -1  # Close miss
        }
    
    def get_player_order_from(self, starter):
        """Get player order starting from given player"""
        names = [p.name for p in self.players]
        if starter in names:
            start_idx = names.index(starter)
            return self.players[start_idx:] + self.players[:start_idx]
        return self.players


@pytest.fixture
def mock_game_winner():
    """Game with Andy as winner (51 points)"""
    return MockGameForGameOver("Andy", 51)


@pytest.fixture
def mock_game_no_winner():
    """Game without winner (highest score 45)"""
    game = MockGameForGameOver("Andy", 45)
    # Override players to ensure no one reaches 50
    game.players = [
        MockPlayer("Andy", 46, False, 3),  # Andy: 46 - 1 (declared 4, got 3) = 45 (not quite 50)
        MockPlayer("Bot 2", 38, True, 4),   # Bot 2: 38 - 3 (declared 1, got 4) = 35  
        MockPlayer("Bot 3", 31, True, 0),   # Bot 3: 31 - 1 (declared 1, got 0) = 30
        MockPlayer("Bot 4", 26, True, 0)    # Bot 4: 26 - 1 (declared 1, got 0) = 25
    ]
    return game


@pytest.fixture
def mock_broadcast():
    """Mock broadcast callback"""
    return AsyncMock()


@pytest_asyncio.fixture
async def state_machine_with_winner(mock_game_winner, mock_broadcast):
    """State machine with a game that has a winner"""
    sm = GameStateMachine(mock_game_winner, mock_broadcast)
    sm.room_id = "TEST_ROOM"
    yield sm
    if sm.is_running:
        await sm.stop()


@pytest_asyncio.fixture
async def state_machine_no_winner(mock_game_no_winner, mock_broadcast):
    """State machine with a game that has no winner yet"""
    sm = GameStateMachine(mock_game_no_winner, mock_broadcast)
    sm.room_id = "TEST_ROOM"
    yield sm
    if sm.is_running:
        await sm.stop()


class TestGameOverTransition:
    """Test game over phase transitions"""
    
    @pytest.mark.asyncio
    async def test_scoring_transitions_to_game_over_with_winner(self, state_machine_with_winner, mock_broadcast):
        """Test that scoring state transitions to GAME_OVER when there's a winner"""
        sm = state_machine_with_winner
        
        # Start in scoring phase
        await sm.start(GamePhase.SCORING)
        
        # Verify we start in scoring
        assert sm.current_phase == GamePhase.SCORING
        assert isinstance(sm.current_state, ScoringState)
        
        # Wait for the scoring delay to complete and transition
        await asyncio.sleep(8)  # Wait longer than the 7-second delay
        
        # Verify transition to GAME_OVER
        assert sm.current_phase == GamePhase.GAME_OVER
        assert isinstance(sm.current_state, GameOverState)
        
        # Verify broadcast was called for game over
        mock_broadcast.assert_called()
        
        # Check that at least one call was for phase_change
        calls = mock_broadcast.call_args_list
        phase_change_calls = [call for call in calls if len(call[0]) >= 3 and call[0][1] == "phase_change"]
        assert len(phase_change_calls) > 0
        
        print("✅ Successfully transitioned from SCORING to GAME_OVER with winner")
    
    @pytest.mark.asyncio
    async def test_scoring_transitions_to_preparation_without_winner(self, state_machine_no_winner, mock_broadcast):
        """Test that scoring state transitions to PREPARATION when there's no winner"""
        sm = state_machine_no_winner
        
        # Start in scoring phase
        await sm.start(GamePhase.SCORING)
        
        # Verify we start in scoring
        assert sm.current_phase == GamePhase.SCORING
        assert isinstance(sm.current_state, ScoringState)
        
        # Wait for the scoring delay to complete and transition
        await asyncio.sleep(8)  # Wait longer than the 7-second delay
        
        # Verify transition to PREPARATION (next round)
        assert sm.current_phase == GamePhase.PREPARATION
        
        print("✅ Successfully transitioned from SCORING to PREPARATION without winner")
    
    @pytest.mark.asyncio
    async def test_game_over_state_setup(self, state_machine_with_winner):
        """Test that GameOverState properly sets up with winner data"""
        sm = state_machine_with_winner
        
        # Manually transition to game over
        await sm._transition_to(GamePhase.GAME_OVER)
        
        # Verify we're in game over state
        assert sm.current_phase == GamePhase.GAME_OVER
        assert isinstance(sm.current_state, GameOverState)
        
        # Check that phase data was set up correctly
        phase_data = sm.current_state.phase_data
        
        # Verify required fields exist
        assert "final_rankings" in phase_data
        assert "game_stats" in phase_data
        assert "winners" in phase_data
        
        # Verify winners data
        winners = phase_data["winners"]
        assert isinstance(winners, list)
        assert "Andy" in winners  # Andy should be the winner with 51 points
        
        # Verify rankings data
        rankings = phase_data["final_rankings"]
        assert isinstance(rankings, list)
        assert len(rankings) == 4  # Should have all 4 players
        
        # Verify first place is Andy
        first_place = rankings[0]
        assert first_place["name"] == "Andy"
        assert first_place["rank"] == 1
        assert first_place["score"] == 51
        
        # Verify game stats
        stats = phase_data["game_stats"]
        assert "total_rounds" in stats
        assert "game_duration" in stats
        assert stats["total_rounds"] == 13
        
        print("✅ GameOverState setup correctly with all required data")
    
    @pytest.mark.asyncio
    async def test_game_over_is_terminal_state(self, state_machine_with_winner):
        """Test that GAME_OVER state doesn't transition to another state"""
        sm = state_machine_with_winner
        
        # Transition to game over
        await sm._transition_to(GamePhase.GAME_OVER)
        
        # Verify we're in game over
        assert sm.current_phase == GamePhase.GAME_OVER
        
        # Check transition conditions
        game_over_state = sm.current_state
        next_phase = await game_over_state.check_transition_conditions()
        
        # Should return None (no transitions)
        assert next_phase is None
        
        # Verify next_phases property
        assert game_over_state.next_phases == []
        
        print("✅ GAME_OVER is properly configured as terminal state")
    
    @pytest.mark.asyncio
    async def test_end_time_is_set(self, state_machine_with_winner):
        """Test that end_time is set when entering game over state"""
        sm = state_machine_with_winner
        game = sm.game
        
        # Verify end_time is not set initially
        assert game.end_time is None
        
        # Transition to game over
        await sm._transition_to(GamePhase.GAME_OVER)
        
        # Verify end_time is now set
        assert game.end_time is not None
        assert isinstance(game.end_time, (int, float))
        assert game.end_time > game.start_time
        
        print("✅ Game end_time properly set during GAME_OVER transition")


async def run_all_tests():
    """Run all game over transition tests"""
    print("🧪 Starting Game Over Transition Tests...")
    
    # Create test fixtures
    mock_game_winner = MockGameForGameOver("Andy", 51)
    mock_game_no_winner = MockGameForGameOver("Andy", 45)
    mock_broadcast = AsyncMock()
    
    # Test 1: Transition with winner
    print("\n📋 Test 1: Scoring → Game Over with winner")
    sm1 = GameStateMachine(mock_game_winner, mock_broadcast)
    sm1.room_id = "TEST_ROOM"
    try:
        await sm1.start(GamePhase.SCORING)
        await asyncio.sleep(8)
        assert sm1.current_phase == GamePhase.GAME_OVER
        print("✅ PASS: Transitions to GAME_OVER with winner")
    finally:
        if sm1.is_running:
            await sm1.stop()
    
    # Test 2: Transition without winner
    print("\n📋 Test 2: Scoring → Preparation without winner")
    mock_game_no_winner = MockGameForGameOver("Andy", 45)
    mock_game_no_winner.players = [
        MockPlayer("Andy", 46, False, 3),  # Andy: 46 - 1 (declared 4, got 3) = 45 (not quite 50)
        MockPlayer("Bot 2", 38, True, 4),   # Bot 2: 38 - 3 (declared 1, got 4) = 35  
        MockPlayer("Bot 3", 31, True, 0),   # Bot 3: 31 - 1 (declared 1, got 0) = 30
        MockPlayer("Bot 4", 26, True, 0)    # Bot 4: 26 - 1 (declared 1, got 0) = 25
    ]
    sm2 = GameStateMachine(mock_game_no_winner, AsyncMock())
    sm2.room_id = "TEST_ROOM"
    try:
        await sm2.start(GamePhase.SCORING)
        await asyncio.sleep(8)
        assert sm2.current_phase == GamePhase.PREPARATION
        print("✅ PASS: Transitions to PREPARATION without winner")
    finally:
        if sm2.is_running:
            await sm2.stop()
    
    # Test 3: Game over state setup
    print("\n📋 Test 3: Game Over state data setup")
    sm3 = GameStateMachine(mock_game_winner, AsyncMock())
    sm3.room_id = "TEST_ROOM"
    try:
        await sm3._transition_to(GamePhase.GAME_OVER)
        
        phase_data = sm3.current_state.phase_data
        assert "final_rankings" in phase_data
        assert "winners" in phase_data
        assert "Andy" in phase_data["winners"]
        print("✅ PASS: Game over state setup correctly")
    finally:
        if sm3.is_running:
            await sm3.stop()
    
    print("\n🎉 All Game Over Transition Tests PASSED!")


if __name__ == "__main__":
    # Run the tests directly
    asyncio.run(run_all_tests())