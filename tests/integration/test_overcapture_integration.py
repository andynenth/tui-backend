# tests/integration/test_overcapture_integration.py

"""
Integration test for overcapture avoidance feature.
Tests that bots actually use the strategic AI to avoid winning extra piles.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.bot_manager import BotManager
from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.state_machine.core import GamePhase, ActionType, GameAction


class TestOvercaptureIntegration:
    """Integration tests for overcapture avoidance in real game scenarios."""
    
    @pytest.fixture
    def setup_game_with_bots(self):
        """Set up a game with 4 bot players."""
        players = [
            Player(f"Bot{i+1}", is_bot=True) 
            for i in range(4)
        ]
        game = Game(players)
        state_machine = GameStateMachine(game)
        
        # Register game with bot manager
        bot_manager = BotManager()
        bot_manager.register_game("test_room", game, state_machine)
        
        return game, state_machine, bot_manager
    
    @pytest.mark.asyncio
    async def test_bot_avoids_overcapture_when_at_target(self, setup_game_with_bots):
        """Test that a bot at their declared target plays weak pieces."""
        game, state_machine, bot_manager = setup_game_with_bots
        
        # Set up game state: Bot1 has declared 2 and captured 2 (at target)
        bot1 = game.players[0]
        bot1.declared = 2
        bot1.captured_piles = 2
        
        # Give Bot1 a hand with both strong and weak pieces
        bot1.hand = [
            Piece("GENERAL_RED"),      # 14 points - strongest
            Piece("ADVISOR_BLACK"),    # 11 points - strong
            Piece("SOLDIER_BLACK"),    # 1 point - weakest
            Piece("SOLDIER_RED"),      # 2 points - weak
            Piece("CANNON_RED"),       # 4 points - medium
        ]
        
        # Set up turn state where Bot1 needs to play 2 pieces
        game.turn_number = 3
        game.pile_counts = {"Bot1": 2, "Bot2": 1, "Bot3": 0, "Bot4": 1}
        
        # Initialize state machine properly
        if state_machine.current_phase != GamePhase.TURN:
            # Start from preparation phase
            state_machine.current_phase = GamePhase.PREPARATION
            # Transition through phases properly
            await state_machine._transition_to(GamePhase.ROUND_START)
            await state_machine._transition_to(GamePhase.DECLARATION)
            await state_machine._transition_to(GamePhase.TURN)
        else:
            # Already in TURN phase, just set up the turn state
            pass
        
        # Set required piece count (someone else played 2 pieces)
        turn_state = state_machine.states[GamePhase.TURN]
        turn_state.required_piece_count = 2
        turn_state.current_turn_starter = "Bot2"
        turn_state.turn_order = ["Bot2", "Bot1", "Bot3", "Bot4"]
        turn_state.current_player_index = 1  # Bot1's turn
        
        # Capture Bot1's play
        played_pieces = None
        
        async def capture_play(action):
            nonlocal played_pieces
            if action.player_name == "Bot1" and action.action_type == ActionType.PLAY_PIECES:
                played_pieces = action.payload.get("pieces", [])
            # Return success to continue flow
            return {"status": "play_accepted", "success": True}
        
        # Mock the state machine's handle_action to capture the play
        with patch.object(state_machine, 'handle_action', side_effect=capture_play):
            # Trigger bot play
            await bot_manager.handle_game_event("test_room", "phase_change", {
                "phase": "TURN",
                "current_player": "Bot1"
            })
            
            # Give async operations time to complete
            await asyncio.sleep(0.1)
        
        # Verify Bot1 played the weakest pieces
        assert played_pieces is not None, "Bot1 should have played"
        assert len(played_pieces) == 2, f"Bot1 should play exactly 2 pieces, played {len(played_pieces)}"
        
        # Check that the weakest pieces were played (SOLDIER_BLACK=1, SOLDIER_RED=2)
        played_points = sorted([p.point for p in played_pieces])
        assert played_points == [1, 2], f"Bot1 should play weakest pieces (1,2 points), but played {played_points}"
        
        # Verify specific pieces
        piece_names = sorted([p.name for p in played_pieces])
        assert "SOLDIER" in piece_names[0], "Should play SOLDIER pieces"
        assert "SOLDIER" in piece_names[1], "Should play SOLDIER pieces"
    
    @pytest.mark.asyncio
    async def test_bot_plays_normally_when_below_target(self, setup_game_with_bots):
        """Test that a bot below their declared target plays strong pieces."""
        game, state_machine, bot_manager = setup_game_with_bots
        
        # Set up game state: Bot1 has declared 3 but only captured 1 (below target)
        bot1 = game.players[0]
        bot1.declared = 3
        bot1.captured_piles = 1
        
        # Give Bot1 same hand
        bot1.hand = [
            Piece("GENERAL_RED"),      # 14 points - strongest
            Piece("ADVISOR_BLACK"),    # 11 points - strong
            Piece("SOLDIER_BLACK"),    # 1 point - weakest
            Piece("SOLDIER_RED"),      # 2 points - weak
            Piece("CANNON_RED"),       # 4 points - medium
        ]
        
        # Set up turn state
        game.turn_number = 3
        game.pile_counts = {"Bot1": 1, "Bot2": 1, "Bot3": 1, "Bot4": 1}
        
        # Initialize state machine properly
        if state_machine.current_phase != GamePhase.TURN:
            # Start from preparation phase
            state_machine.current_phase = GamePhase.PREPARATION
            # Transition through phases properly
            await state_machine._transition_to(GamePhase.ROUND_START)
            await state_machine._transition_to(GamePhase.DECLARATION)
            await state_machine._transition_to(GamePhase.TURN)
        else:
            # Already in TURN phase, just set up the turn state
            pass
        
        # Set required piece count
        turn_state = state_machine.states[GamePhase.TURN]
        turn_state.required_piece_count = 2
        turn_state.current_turn_starter = "Bot2"
        turn_state.turn_order = ["Bot2", "Bot1", "Bot3", "Bot4"]
        turn_state.current_player_index = 1  # Bot1's turn
        
        # Capture Bot1's play
        played_pieces = None
        
        async def capture_play(action):
            nonlocal played_pieces
            if action.player_name == "Bot1" and action.action_type == ActionType.PLAY_PIECES:
                played_pieces = action.payload.get("pieces", [])
            return {"status": "play_accepted", "success": True}
        
        with patch.object(state_machine, 'handle_action', side_effect=capture_play):
            await bot_manager.handle_game_event("test_room", "phase_change", {
                "phase": "TURN", 
                "current_player": "Bot1"
            })
            
            await asyncio.sleep(0.1)
        
        # Verify Bot1 played strong pieces (should include GENERAL_RED and ADVISOR_BLACK)
        assert played_pieces is not None, "Bot1 should have played"
        assert len(played_pieces) == 2, f"Bot1 should play exactly 2 pieces"
        
        # Check that strong pieces were played
        played_points = sorted([p.point for p in played_pieces])
        assert played_points == [11, 14], f"Bot1 should play strongest pieces (11,14 points), but played {played_points}"
    
    @pytest.mark.asyncio
    async def test_multiple_bots_at_target(self, setup_game_with_bots):
        """Test that multiple bots at their targets all avoid overcapture."""
        game, state_machine, bot_manager = setup_game_with_bots
        
        # Set up: Bot1 and Bot3 are at their targets
        game.players[0].declared = 2
        game.players[0].captured_piles = 2
        game.players[2].declared = 1  
        game.players[2].captured_piles = 1
        
        # Bot2 and Bot4 are below targets
        game.players[1].declared = 3
        game.players[1].captured_piles = 1
        game.players[3].declared = 2
        game.players[3].captured_piles = 0
        
        # Give all bots similar hands
        for bot in game.players:
            bot.hand = [
                Piece("GENERAL_RED") if bot.name == "Bot1" else Piece("GENERAL_BLACK"),
                Piece("ADVISOR_RED"),
                Piece("ELEPHANT_BLACK"),
                Piece("SOLDIER_BLACK"),
                Piece("SOLDIER_RED"),
            ]
        
        # Track all plays
        bot_plays = {}
        
        async def capture_plays(action):
            if action.action_type == ActionType.PLAY_PIECES:
                bot_plays[action.player_name] = action.payload.get("pieces", [])
            return {"status": "play_accepted", "success": True}
        
        # Set up turn state
        game.turn_number = 5
        state_machine.current_phase = GamePhase.TURN
        await state_machine._transition_to(GamePhase.TURN)
        
        turn_state = state_machine.states[GamePhase.TURN]
        turn_state.required_piece_count = 1
        turn_state.current_turn_starter = "Bot1"
        turn_state.turn_order = ["Bot1", "Bot2", "Bot3", "Bot4"]
        
        # Simulate each bot's turn
        with patch.object(state_machine, 'handle_action', side_effect=capture_plays):
            for i, bot_name in enumerate(turn_state.turn_order):
                turn_state.current_player_index = i
                await bot_manager.handle_game_event("test_room", "phase_change", {
                    "phase": "TURN",
                    "current_player": bot_name
                })
                await asyncio.sleep(0.05)
        
        # Verify bots at target played weak pieces
        assert bot_plays["Bot1"][0].point <= 2, "Bot1 at target should play weak piece"
        assert bot_plays["Bot3"][0].point <= 2, "Bot3 at target should play weak piece"
        
        # Verify bots below target played strong pieces  
        assert bot_plays["Bot2"][0].point >= 10, "Bot2 below target should play strong piece"
        assert bot_plays["Bot4"][0].point >= 10, "Bot4 below target should play strong piece"