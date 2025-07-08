# backend/tests/test_bot_timing_simple.py

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from engine.bot_manager import BotManager, GameBotHandler
from engine.player import Player
from engine.game import Game


@pytest.mark.asyncio
async def test_bot_turn_play_sequential_delays():
    """Test that bot turn plays have sequential delays like declarations"""
    
    # Create game with 1 human and 3 bots
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    
    game = Game(players)
    game.turn_number = 1
    
    # Create bot handler
    handler = GameBotHandler("test_room", game)
    
    # Give all players pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]
    
    # Track bot play timings
    play_times = []
    
    async def mock_bot_play(bot):
        play_times.append({
            'player': bot.name,
            'time': time.time()
        })
    
    # Replace _bot_play with our mock
    handler._bot_play = mock_bot_play
    
    # Test sequential handler
    start_time = time.time()
    await handler._handle_turn_play_phase("Human")
    
    # Should have 3 bot plays
    assert len(play_times) == 3, f"Expected 3 bot plays, got {len(play_times)}"
    
    # Check delays between plays
    previous_time = start_time
    for i, play_record in enumerate(play_times):
        delay = play_record['time'] - previous_time
        print(f"Bot {play_record['player']} played after {delay:.2f}s")
        
        # Verify delay is within expected range (0.5-1.5s)
        assert 0.4 <= delay <= 1.6, f"Bot {play_record['player']} delay {delay}s outside 0.5-1.5s range"
        
        previous_time = play_record['time']
    
    # Verify play order
    assert [p['player'] for p in play_times] == ["Bot1", "Bot2", "Bot3"]


@pytest.mark.asyncio
async def test_bot_declaration_sequential_delays():
    """Test that bot declarations have sequential delays for comparison"""
    
    # Create game with 1 human and 3 bots
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    
    game = Game(players)
    
    # Create bot handler
    handler = GameBotHandler("test_room", game)
    
    # Track declaration timings
    declare_times = []
    
    async def mock_bot_declare(bot, position):
        declare_times.append({
            'player': bot.name,
            'time': time.time()
        })
    
    # Replace _bot_declare with our mock
    handler._bot_declare = mock_bot_declare
    
    # Test sequential handler
    start_time = time.time()
    await handler._handle_declaration_phase("Human")
    
    # Should have 3 bot declarations
    assert len(declare_times) == 3, f"Expected 3 bot declarations, got {len(declare_times)}"
    
    # Check delays between declarations
    previous_time = start_time
    for i, declare_record in enumerate(declare_times):
        delay = declare_record['time'] - previous_time
        print(f"Bot {declare_record['player']} declared after {delay:.2f}s")
        
        # Verify delay is within expected range (0.5-1.5s)
        assert 0.4 <= delay <= 1.6, f"Bot {declare_record['player']} delay {delay}s outside 0.5-1.5s range"
        
        previous_time = declare_record['time']


@pytest.mark.asyncio
async def test_turn_play_stops_at_human():
    """Test that bot sequential play stops when reaching a human player"""
    
    # Create game with alternating humans and bots
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Human2", is_bot=False),
        Player("Bot2", is_bot=True)
    ]
    
    game = Game(players)
    game.turn_number = 1
    
    # Create bot handler
    handler = GameBotHandler("test_room", game)
    
    # Give all players pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]
    
    # Track bot plays
    play_times = []
    
    async def mock_bot_play(bot):
        play_times.append({
            'player': bot.name,
            'time': time.time()
        })
    
    handler._bot_play = mock_bot_play
    
    # Test sequential handler starting after Human1
    await handler._handle_turn_play_phase("Human1")
    
    # Only Bot1 should have played, stopping at Human2
    assert len(play_times) == 1, f"Expected 1 bot play, got {len(play_times)}"
    assert play_times[0]['player'] == "Bot1"


@pytest.mark.asyncio
async def test_bot_delays_match_declaration_pattern():
    """Test that turn play delays match declaration delay pattern"""
    
    # Create game with 3 bots
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    
    game = Game(players)
    handler = GameBotHandler("test_room", game)
    
    # Give all players pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]
    
    # Track both declaration and play timings
    declare_times = []
    play_times = []
    
    async def mock_bot_declare(bot, position):
        declare_times.append({
            'player': bot.name,
            'time': time.time()
        })
    
    async def mock_bot_play(bot):
        play_times.append({
            'player': bot.name,
            'time': time.time()
        })
    
    handler._bot_declare = mock_bot_declare
    handler._bot_play = mock_bot_play
    
    # Test declarations
    declare_start = time.time()
    await handler._handle_declaration_phase("Human")
    
    # Test plays
    await asyncio.sleep(0.1)  # Small gap between tests
    play_start = time.time()
    await handler._handle_turn_play_phase("Human")
    
    # Both should have 3 bot actions
    assert len(declare_times) == 3
    assert len(play_times) == 3
    
    # Compare delay patterns
    declare_delays = []
    prev_time = declare_start
    for record in declare_times:
        delay = record['time'] - prev_time
        declare_delays.append(delay)
        prev_time = record['time']
    
    play_delays = []
    prev_time = play_start
    for record in play_times:
        delay = record['time'] - prev_time
        play_delays.append(delay)
        prev_time = record['time']
    
    # All delays should be in the same range
    for i in range(3):
        print(f"Bot{i+1} - Declaration: {declare_delays[i]:.2f}s, Play: {play_delays[i]:.2f}s")
        assert 0.4 <= declare_delays[i] <= 1.6
        assert 0.4 <= play_delays[i] <= 1.6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])