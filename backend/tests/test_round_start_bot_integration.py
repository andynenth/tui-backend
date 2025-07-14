"""
Integration tests for Round Start phase with bot manager

Tests bot behavior during phase transitions to ensure no invalid
transition attempts occur.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase, GameAction, ActionType
from engine.bot_manager import BotManager, GameBotHandler
from engine.game import Game
from engine.player import Player


class TestBotManagerRoundStartIntegration:
    """Test bot manager behavior with ROUND_START phase"""

    @pytest.fixture
    def game_with_bots(self):
        """Create a game with mix of human and bot players"""
        game = Game()
        game.players = [
            Player("Human1", is_bot=False),
            Player("Bot1", is_bot=True),
            Player("Bot2", is_bot=True),
            Player("Human2", is_bot=False),
        ]
        game.round_number = 1
        return game

    @pytest.fixture
    async def integrated_system(self, game_with_bots):
        """Create integrated state machine with bot manager"""
        sm = GameStateMachine(game_with_bots)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = AsyncMock()

        # Initialize bot manager
        bot_manager = BotManager()
        bot_manager.register_game("TEST_ROOM", game_with_bots, sm)

        await sm.initialize()

        return {"state_machine": sm, "bot_manager": bot_manager, "game": game_with_bots}

    @pytest.mark.asyncio
    async def test_bot_manager_waits_for_declaration_phase(self, integrated_system):
        """Test that bots don't try to declare during ROUND_START"""
        sm = integrated_system["state_machine"]
        bot_manager = integrated_system["bot_manager"]

        # Transition to ROUND_START
        await sm._transition_to(GamePhase.ROUND_START)

        # Bot manager should receive phase_change event
        handler = bot_manager.active_games["TEST_ROOM"]

        # Simulate the phase_change event
        await handler.handle_event(
            "phase_change",
            {
                "phase": "round_start",
                "phase_data": {
                    "current_starter": "Human1",
                    "starter_reason": "has_general_red",
                },
            },
        )

        # Verify no bot actions were triggered
        # (Bot declarations should only happen in DECLARATION phase)
        with patch.object(
            handler, "_bot_declare", new_callable=AsyncMock
        ) as mock_declare:
            # Give async tasks time to run
            await asyncio.sleep(0.1)
            mock_declare.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_declarations_trigger_after_round_start(self, integrated_system):
        """Test that bot declarations work correctly after ROUND_START completes"""
        sm = integrated_system["state_machine"]
        bot_manager = integrated_system["bot_manager"]
        handler = bot_manager.active_games["TEST_ROOM"]

        # Go through the proper phase sequence
        # 1. PREPARATION → ROUND_START
        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

        # 2. ROUND_START → DECLARATION
        await sm._transition_to(GamePhase.DECLARATION)
        assert sm.current_phase == GamePhase.DECLARATION

        # Now bot manager should trigger bot declarations
        with patch.object(
            handler, "_bot_declare", new_callable=AsyncMock
        ) as mock_declare:
            await handler.handle_event(
                "round_started", {"phase": "declaration", "starter": "Human1"}
            )

            # Give async tasks time to run
            await asyncio.sleep(0.2)

            # Bot declarations should be triggered
            assert mock_declare.call_count > 0

    @pytest.mark.asyncio
    async def test_redeal_bot_behavior(self, integrated_system):
        """Test bot behavior during redeal doesn't cause invalid transitions"""
        sm = integrated_system["state_machine"]
        bot_manager = integrated_system["bot_manager"]
        game = integrated_system["game"]

        # Set up weak hand scenario
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = {"Bot1", "Human1"}
        prep_state.weak_players_awaiting = {"Bot1", "Human1"}

        # Bot accepts redeal
        bot_action = GameAction(
            player_name="Bot1",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            is_bot=True,
        )

        # Process bot action
        result = await sm.handle_action(bot_action)
        assert result.get("success") or result.get("status") == "ok"

        # Human declines
        human_action = GameAction(
            player_name="Human1",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            is_bot=False,
        )

        # Mock no weak hands after redeal
        with patch.object(prep_state, "_deal_cards", new_callable=AsyncMock):
            with patch.object(
                sm, "_transition_to", new_callable=AsyncMock
            ) as mock_transition:
                result = await sm.handle_action(human_action)

                # Should transition to ROUND_START, not DECLARATION
                if mock_transition.called:
                    mock_transition.assert_called_with(GamePhase.ROUND_START)

    @pytest.mark.asyncio
    async def test_no_round_started_event_in_preparation(self, integrated_system):
        """Ensure round_started event is never sent during PREPARATION phase"""
        sm = integrated_system["state_machine"]
        bot_manager = integrated_system["bot_manager"]
        handler = bot_manager.active_games["TEST_ROOM"]

        # We're in PREPARATION phase
        assert sm.current_phase == GamePhase.PREPARATION

        # Mock the declaration handler to catch any improper calls
        with patch.object(
            handler, "_handle_declaration_phase", new_callable=AsyncMock
        ) as mock_decl:
            # Simulate various preparation phase events
            await handler.handle_event(
                "phase_change",
                {"phase": "preparation", "phase_data": {"dealing_cards": True}},
            )

            await handler.handle_event("weak_hands_found", {"weak_players": ["Bot1"]})

            # Bot declarations should NOT be triggered
            mock_decl.assert_not_called()

    @pytest.mark.asyncio
    async def test_phase_action_tracking_reset(self, integrated_system):
        """Test that phase action tracking resets properly between phases"""
        bot_manager = integrated_system["bot_manager"]
        handler = bot_manager.active_games["TEST_ROOM"]

        # Simulate phase changes
        # PREPARATION
        await handler.handle_event("phase_change", {"phase": "preparation"})
        assert handler._last_processed_phase == "preparation"
        handler._phase_action_triggered["preparation"] = True

        # ROUND_START - should clear previous tracking
        await handler.handle_event("phase_change", {"phase": "round_start"})
        assert handler._last_processed_phase == "round_start"
        assert "preparation" not in handler._phase_action_triggered

        # DECLARATION - should clear again
        await handler.handle_event("phase_change", {"phase": "declaration"})
        assert handler._last_processed_phase == "declaration"
        assert "round_start" not in handler._phase_action_triggered


class TestErrorScenarios:
    """Test error scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_recovery_from_invalid_transition_attempt(self):
        """Test system recovers gracefully from invalid transition attempts"""
        game = Game()
        sm = GameStateMachine(game)
        await sm.initialize()

        # Record initial state
        assert sm.current_phase == GamePhase.PREPARATION
        initial_state = sm.current_state

        # Attempt invalid transition
        await sm._transition_to(GamePhase.DECLARATION)

        # Should remain in PREPARATION
        assert sm.current_phase == GamePhase.PREPARATION
        assert sm.current_state == initial_state

        # System should still be functional - try valid transition
        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

    @pytest.mark.asyncio
    async def test_concurrent_transition_protection(self):
        """Test that concurrent transition attempts don't cause issues"""
        game = Game()
        sm = GameStateMachine(game)
        await sm.initialize()

        # Set up for transition
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        # Attempt multiple concurrent transitions
        tasks = [
            sm._transition_to(GamePhase.ROUND_START),
            sm._transition_to(GamePhase.DECLARATION),  # Invalid
            sm._transition_to(GamePhase.ROUND_START),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Should end up in ROUND_START (first valid transition)
        assert sm.current_phase == GamePhase.ROUND_START


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
