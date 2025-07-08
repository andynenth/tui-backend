# backend/tests/test_bot_turn_timing.py

import asyncio
import pytest
import time
from unittest.mock import Mock, patch
from engine.bot_manager import GameBotHandler
from engine.player import Player
from engine.game import Game


@pytest.mark.asyncio 
async def test_bot_turn_play_has_sequential_delays():
    """Test that the new _handle_turn_play_phase method provides sequential delays"""
    
    # Create players
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    
    game = Game(players)
    
    # Mock state machine to provide turn order
    mock_state_machine = Mock()
    mock_state_machine.get_phase_data.return_value = {
        'turn_order': ["Human", "Bot1", "Bot2", "Bot3"],
        'required_piece_count': 1
    }
    
    handler = GameBotHandler("test_room", game, mock_state_machine)
    
    # Give all players pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]
    
    # Track bot play calls and timing
    play_calls = []
    
    async def track_bot_play(bot):
        play_calls.append({
            'player': bot.name,
            'time': time.time()
        })
        # Don't actually do anything
    
    handler._bot_play = track_bot_play
    
    # Also mock the _get_game_state to return our game
    handler._get_game_state = Mock(return_value=game)
    
    # Test the sequential handler
    start_time = time.time()
    await handler._handle_turn_play_phase("Human")
    
    # Should have called _bot_play for each bot
    assert len(play_calls) == 3, f"Expected 3 bot plays, got {len(play_calls)}"
    
    # Check timing between calls
    previous_time = start_time
    for i, call in enumerate(play_calls):
        delay = call['time'] - previous_time
        print(f"Bot {call['player']} was called after {delay:.2f}s delay")
        
        # Each bot should have 0.5-1.5s delay (with small tolerance for timing)
        assert 0.4 <= delay <= 1.7, f"Bot {call['player']} delay {delay}s not in expected range"
        
        previous_time = call['time']
    
    # Verify order
    assert [c['player'] for c in play_calls] == ["Bot1", "Bot2", "Bot3"]


@pytest.mark.asyncio
async def test_turn_handler_stops_at_human():
    """Test that sequential handler stops when reaching a human player"""
    
    # Create alternating players
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Human2", is_bot=False),
        Player("Bot2", is_bot=True)
    ]
    
    game = Game(players)
    
    # Mock state machine
    mock_state_machine = Mock()
    mock_state_machine.get_phase_data.return_value = {
        'turn_order': ["Human1", "Bot1", "Human2", "Bot2"]
    }
    
    handler = GameBotHandler("test_room", game, mock_state_machine)
    
    # Give all players pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]
    
    # Track plays
    play_calls = []
    
    async def track_bot_play(bot):
        play_calls.append(bot.name)
    
    handler._bot_play = track_bot_play
    
    # Mock the _get_game_state to return our game
    handler._get_game_state = Mock(return_value=game)
    
    # Test starting after Human1
    await handler._handle_turn_play_phase("Human1")
    
    # Should only play Bot1, stopping at Human2
    assert len(play_calls) == 1
    assert play_calls[0] == "Bot1"


@pytest.mark.asyncio
async def test_declaration_comparison():
    """Test that declaration delays work for comparison"""
    
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    
    game = Game(players)
    
    # For declarations, need declaration order instead
    handler = GameBotHandler("test_room", game)
    
    # Mock getting declaration order
    handler._get_declaration_order = Mock(return_value=["Human", "Bot1", "Bot2", "Bot3"])
    
    # Track declaration calls
    declare_calls = []
    
    async def track_bot_declare(bot, position):
        declare_calls.append({
            'player': bot.name,
            'time': time.time()
        })
    
    handler._bot_declare = track_bot_declare
    
    # Test declaration handler
    start_time = time.time()
    await handler._handle_declaration_phase("Human")
    
    # Should have 3 bot declarations
    assert len(declare_calls) == 3
    
    # Check timing
    previous_time = start_time
    for call in declare_calls:
        delay = call['time'] - previous_time
        print(f"Bot {call['player']} declared after {delay:.2f}s")
        assert 0.4 <= delay <= 1.7
        previous_time = call['time']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])