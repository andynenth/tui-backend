# tests/unit/test_bot_overcapture_unit.py

"""
Unit test for bot overcapture avoidance.
Tests the bot manager's play logic directly.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.bot_manager import GameBotHandler
from backend.engine.rules import get_play_type


class TestBotOvercaptureUnit:
    """Unit tests for bot overcapture avoidance logic."""
    
    @pytest.fixture
    def mock_game(self):
        """Create a mock game with basic attributes."""
        game = MagicMock()
        game.turn_number = 3
        game.pile_counts = {}
        game.players = []
        return game
    
    @pytest.fixture 
    def mock_state_machine(self):
        """Create a mock state machine."""
        state_machine = MagicMock()
        state_machine.handle_action = AsyncMock(return_value={"success": True})
        state_machine.get_phase_data = MagicMock(return_value={})
        return state_machine
    
    @pytest.mark.asyncio
    async def test_bot_at_target_plays_weak_pieces(self, mock_game, mock_state_machine):
        """Test that bot at declared target plays weakest pieces."""
        # Create bot at target (declared 2, captured 2)
        bot = Player("Bot1", is_bot=True)
        bot.declared = 2
        bot.captured_piles = 2
        bot.hand = [
            Piece("GENERAL_RED"),    # 14 points
            Piece("ADVISOR_BLACK"),  # 11 points  
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("SOLDIER_RED"),    # 2 points
            Piece("CANNON_BLACK"),   # 4 points
        ]
        
        # Set up game state
        mock_game.players = [bot, Player("Bot2", is_bot=True), Player("Bot3", is_bot=True), Player("Bot4", is_bot=True)]
        mock_game.pile_counts = {"Bot1": 2, "Bot2": 0, "Bot3": 1, "Bot4": 0}
        
        # Create bot handler
        handler = GameBotHandler("test_room", mock_game, mock_state_machine)
        
        # Mock the import of ai module
        with patch('backend.engine.bot_manager.ai') as mock_ai:
            # Set up the safe wrapper to use our test implementation
            def test_choose_strategic_play_safe(hand, context, verbose=False):
                # Simulate overcapture avoidance
                if context and hasattr(context, 'my_captured') and hasattr(context, 'my_declared'):
                    if context.my_captured == context.my_declared:
                        # At target - play weakest pieces
                        sorted_hand = sorted(hand, key=lambda p: p.point)
                        return sorted_hand[:context.required_piece_count or 1]
                # Not at target - play strongest
                sorted_hand = sorted(hand, key=lambda p: p.point, reverse=True)
                return sorted_hand[:context.required_piece_count or 1]
            
            mock_ai.choose_strategic_play_safe = test_choose_strategic_play_safe
            
            # Capture the action sent to state machine
            played_pieces = None
            
            async def capture_action(action):
                nonlocal played_pieces
                if action.action_type.name == "PLAY_PIECES":
                    played_pieces = action.payload.get("pieces", [])
                return {"success": True}
            
            mock_state_machine.handle_action = AsyncMock(side_effect=capture_action)
            
            # Set up phase data to provide required_piece_count
            mock_state_machine.get_phase_data.return_value = {
                "required_piece_count": 2,
                "current_turn_starter": "Bot2"
            }
            
            # Test bot play
            await handler._bot_play(bot)
            
            # Verify weak pieces were played
            assert played_pieces is not None, "Bot should have played"
            assert len(played_pieces) == 2, f"Bot should play 2 pieces, played {len(played_pieces)}"
            
            # Check the pieces are the weakest
            points = sorted([p.point for p in played_pieces])
            assert points == [1, 2], f"Should play SOLDIER_BLACK(1) and SOLDIER_RED(2), but played {points}"
    
    @pytest.mark.asyncio
    async def test_bot_below_target_plays_strong_pieces(self, mock_game, mock_state_machine):
        """Test that bot below target plays strongest pieces."""
        # Create bot below target (declared 3, captured 1)
        bot = Player("Bot1", is_bot=True)
        bot.declared = 3
        bot.captured_piles = 1
        bot.hand = [
            Piece("GENERAL_RED"),    # 14 points
            Piece("ADVISOR_BLACK"),  # 11 points  
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("SOLDIER_RED"),    # 2 points
            Piece("CANNON_BLACK"),   # 4 points
        ]
        
        # Set up game state
        mock_game.players = [bot, Player("Bot2", is_bot=True), Player("Bot3", is_bot=True), Player("Bot4", is_bot=True)]
        mock_game.pile_counts = {"Bot1": 1, "Bot2": 1, "Bot3": 1, "Bot4": 1}
        
        # Create bot handler
        handler = GameBotHandler("test_room", mock_game, mock_state_machine)
        
        # Mock the import of ai module
        with patch('backend.engine.bot_manager.ai') as mock_ai:
            # Use same test implementation
            def test_choose_strategic_play_safe(hand, context, verbose=False):
                if context and hasattr(context, 'my_captured') and hasattr(context, 'my_declared'):
                    if context.my_captured == context.my_declared:
                        sorted_hand = sorted(hand, key=lambda p: p.point)
                        return sorted_hand[:context.required_piece_count or 1]
                sorted_hand = sorted(hand, key=lambda p: p.point, reverse=True)
                return sorted_hand[:context.required_piece_count or 1]
            
            mock_ai.choose_strategic_play_safe = test_choose_strategic_play_safe
            
            # Capture the action
            played_pieces = None
            
            async def capture_action(action):
                nonlocal played_pieces
                if action.action_type.name == "PLAY_PIECES":
                    played_pieces = action.payload.get("pieces", [])
                return {"success": True}
            
            mock_state_machine.handle_action = AsyncMock(side_effect=capture_action)
            
            # Set up phase data to provide required_piece_count
            mock_state_machine.get_phase_data.return_value = {
                "required_piece_count": 2,
                "current_turn_starter": "Bot2"
            }
            
            # Test bot play
            await handler._bot_play(bot)
            
            # Verify strong pieces were played
            assert played_pieces is not None, "Bot should have played"
            assert len(played_pieces) == 2, f"Bot should play 2 pieces"
            
            # Check the pieces are the strongest
            points = sorted([p.point for p in played_pieces], reverse=True)
            assert points == [14, 11], f"Should play GENERAL_RED(14) and ADVISOR_BLACK(11), but played {points}"
    
    @pytest.mark.asyncio
    async def test_context_building_with_pile_counts(self, mock_game, mock_state_machine):
        """Test that context is built correctly with pile counts."""
        bot = Player("Bot1", is_bot=True)
        bot.declared = 2
        bot.captured_piles = 0  # Player attribute
        bot.hand = [Piece("SOLDIER_BLACK")]
        
        # Game tracks actual pile counts
        mock_game.players = [bot]
        mock_game.pile_counts = {"Bot1": 2}  # Bot1 has actually captured 2
        
        handler = GameBotHandler("test_room", mock_game, mock_state_machine)
        
        # Track context passed to AI
        captured_context = None
        
        with patch('backend.engine.bot_manager.ai') as mock_ai:
            def capture_context(hand, context, verbose=False):
                nonlocal captured_context
                captured_context = context
                return hand[:1]
            
            mock_ai.choose_strategic_play_safe = capture_context
            
            # Set up phase data
            mock_state_machine.get_phase_data.return_value = {
                "required_piece_count": 1
            }
            
            await handler._bot_play(bot)
            
            # Verify context uses game.pile_counts not player.captured_piles
            assert captured_context is not None, "Context should be created"
            assert captured_context.my_captured == 2, f"Should use game.pile_counts (2), not player.captured_piles (0)"
            assert captured_context.my_declared == 2, "Declared should be 2"
            # Bot should be at target (2/2) even though player.captured_piles is 0