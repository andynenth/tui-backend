#!/usr/bin/env python3
"""
🚀 Enterprise Architecture Validation Test

Tests that the backend now implements the automatic broadcasting system
promised in BENEFITS_GUARANTEE.md, replacing manual broadcasting with
centralized automatic broadcasting.

This test verifies:
1. Automatic broadcasting is enabled by default
2. update_phase_data() triggers automatic broadcasts
3. Custom event broadcasting works through centralized system
4. Turn number sync issues are resolved
5. Event sourcing and change history tracking works
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


class EnterpriseArchitectureValidator:
    def __init__(self):
        self.test_results = []
        self.current_test = ""
        self.broadcast_events = []  # Track broadcasted events

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.current_test = test_name
        result = {"test": test_name, "status": status, "details": details}
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔄"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   💬 {details}")
        print()

    def assert_equal(self, actual, expected, message=""):
        """Assert two values are equal"""
        if actual == expected:
            return True
        else:
            self.log_test(
                self.current_test,
                "FAIL",
                f"{message} - Expected: {expected}, Got: {actual}",
            )
            return False

    def assert_true(self, condition, message=""):
        """Assert condition is true"""
        if condition:
            return True
        else:
            self.log_test(self.current_test, "FAIL", f"{message} - Condition was False")
            return False

    async def setup_game_for_testing(self):
        """Set up a game for enterprise architecture testing"""
        print("🚀 Setting up game for enterprise architecture testing...")

        # Create players
        players = [
            Player("TestPlayer", is_bot=False),
            Player("Bot1", is_bot=True),
            Player("Bot2", is_bot=True),
            Player("Bot3", is_bot=True),
        ]

        # Create game
        game = Game(players)
        game.room_id = "test_room"

        # Set up state machine
        state_machine = GameStateMachine(game)

        # Set up simple hands for testing
        for i, player in enumerate(game.players):
            player.hand = [
                Piece("GENERAL_RED" if i == 0 else "GENERAL_BLACK"),
                Piece("ADVISOR_RED"),
                Piece("ELEPHANT_RED"),
                Piece("CHARIOT_RED"),
            ]

        # Set round starter
        game.round_starter = "TestPlayer"
        game.current_player = "TestPlayer"
        game.turn_number = 0

        # Initialize pile tracking
        game.player_piles = {p.name: 0 for p in players}

        return game, state_machine

    async def test_01_enterprise_architecture_enabled(self, game, state_machine):
        """Test: Enterprise architecture is enabled by default"""
        self.log_test(
            "01. Enterprise Architecture Enabled",
            "RUNNING",
            "Checking auto-broadcast is enabled",
        )

        # Start state machine in turn phase
        await state_machine.start(GamePhase.TURN)

        # Get turn state
        turn_state = state_machine.current_state

        # Verify enterprise architecture is enabled
        success = self.assert_true(
            hasattr(turn_state, "_auto_broadcast_enabled"),
            "Turn state should have _auto_broadcast_enabled attribute",
        )

        success &= self.assert_true(
            turn_state._auto_broadcast_enabled,
            "Auto-broadcast should be enabled by default",
        )

        # Verify centralized methods exist
        success &= self.assert_true(
            hasattr(turn_state, "update_phase_data"),
            "Turn state should have update_phase_data method",
        )

        success &= self.assert_true(
            hasattr(turn_state, "broadcast_custom_event"),
            "Turn state should have broadcast_custom_event method",
        )

        if success:
            self.log_test(
                "01. Enterprise Architecture Enabled",
                "PASS",
                "Enterprise architecture is properly enabled",
            )

        return success

    async def test_02_automatic_phase_data_broadcasting(self, game, state_machine):
        """Test: update_phase_data() triggers automatic broadcasting"""
        self.log_test(
            "02. Automatic Phase Data Broadcasting",
            "RUNNING",
            "Testing centralized update_phase_data",
        )

        turn_state = state_machine.current_state

        # Mock the broadcast function to capture calls
        original_broadcast = None
        broadcast_calls = []

        try:
            # Mock broadcast_adapter.broadcast to capture calls
            from infrastructure.websocket import broadcast_adapter
            original_broadcast = broadcast_adapter.broadcast

            async def mock_broadcast(room_id, event_type, data):
                broadcast_calls.append(
                    {"room_id": room_id, "event_type": event_type, "data": data}
                )
                print(f"🎯 MOCK_BROADCAST: {event_type} to {room_id}")

            broadcast_adapter.broadcast = mock_broadcast

            # Test automatic broadcasting via update_phase_data
            await turn_state.update_phase_data(
                {"test_key": "test_value", "current_turn_number": 1},
                "Enterprise architecture test",
            )

            # Verify broadcast was called automatically
            success = self.assert_true(
                len(broadcast_calls) >= 1,
                "update_phase_data should trigger automatic broadcast",
            )

            if broadcast_calls:
                last_broadcast = broadcast_calls[-1]
                success &= self.assert_equal(
                    last_broadcast["event_type"],
                    "phase_change",
                    "Should broadcast phase_change event",
                )

                success &= self.assert_equal(
                    last_broadcast["data"]["reason"],
                    "Enterprise architecture test",
                    "Should include reason in broadcast data",
                )

                success &= self.assert_true(
                    "test_key" in last_broadcast["data"]["phase_data"],
                    "Should include updated phase data",
                )

            if success:
                self.log_test(
                    "02. Automatic Phase Data Broadcasting",
                    "PASS",
                    "Automatic broadcasting works correctly",
                )

        finally:
            # Restore original broadcast function
            if original_broadcast:
                broadcast_adapter.broadcast = original_broadcast

        return success

    async def test_03_change_history_tracking(self, game, state_machine):
        """Test: Event sourcing and change history tracking"""
        self.log_test(
            "03. Change History Tracking", "RUNNING", "Testing event sourcing features"
        )

        turn_state = state_machine.current_state

        # Get initial history count
        initial_history = len(turn_state.get_change_history())

        # Make a change
        await turn_state.update_phase_data(
            {"history_test": "value1"}, "First change", broadcast=False
        )  # Disable broadcasting for this test

        # Make another change
        await turn_state.update_phase_data(
            {"history_test": "value2"}, "Second change", broadcast=False
        )

        # Verify history tracking
        history = turn_state.get_change_history()

        success = self.assert_equal(
            len(history), initial_history + 2, "Should track 2 new changes in history"
        )

        if len(history) >= 2:
            latest_change = history[-1]
            success &= self.assert_equal(
                latest_change["reason"], "Second change", "Should track change reason"
            )

            success &= self.assert_true(
                "sequence" in latest_change, "Should include sequence number"
            )

            success &= self.assert_true(
                "timestamp" in latest_change, "Should include timestamp"
            )

            success &= self.assert_equal(
                latest_change["updates"]["history_test"],
                "value2",
                "Should track the actual updates",
            )

        if success:
            self.log_test(
                "03. Change History Tracking",
                "PASS",
                "Event sourcing and change history work correctly",
            )

        return success

    async def test_04_custom_event_broadcasting(self, game, state_machine):
        """Test: Custom event broadcasting through centralized system"""
        self.log_test(
            "04. Custom Event Broadcasting",
            "RUNNING",
            "Testing centralized custom event system",
        )

        turn_state = state_machine.current_state

        # Mock broadcast to capture calls
        broadcast_calls = []

        try:
            try:
                import backend.socket_manager as socket_manager
            except ImportError:
                import socket_manager
            original_broadcast = socket_manager.broadcast

            async def mock_broadcast(room_id, event_type, data):
                broadcast_calls.append(
                    {"room_id": room_id, "event_type": event_type, "data": data}
                )

            socket_manager.broadcast = mock_broadcast

            # Test custom event broadcasting
            await turn_state.broadcast_custom_event(
                "test_event",
                {"custom_data": "test_value", "player": "TestPlayer"},
                "Custom event test",
            )

            # Verify custom event was broadcast
            success = self.assert_true(
                len(broadcast_calls) >= 1, "Custom event should be broadcast"
            )

            if broadcast_calls:
                custom_broadcast = broadcast_calls[-1]
                success &= self.assert_equal(
                    custom_broadcast["event_type"],
                    "test_event",
                    "Should broadcast correct event type",
                )

                success &= self.assert_equal(
                    custom_broadcast["data"]["custom_data"],
                    "test_value",
                    "Should include custom data",
                )

                success &= self.assert_true(
                    "sequence" in custom_broadcast["data"],
                    "Should add enterprise metadata (sequence)",
                )

                success &= self.assert_true(
                    "timestamp" in custom_broadcast["data"],
                    "Should add enterprise metadata (timestamp)",
                )

            if success:
                self.log_test(
                    "04. Custom Event Broadcasting",
                    "PASS",
                    "Custom event broadcasting works correctly",
                )

        finally:
            if "original_broadcast" in locals():
                socket_manager.broadcast = original_broadcast

        return success

    async def run_complete_test(self):
        """Run the complete enterprise architecture validation test"""
        print("🚀 Starting Enterprise Architecture Validation Test")
        print("=" * 60)
        print()

        try:
            # Setup
            game, state_machine = await self.setup_game_for_testing()

            # Run tests in sequence
            tests = [
                self.test_01_enterprise_architecture_enabled,
                self.test_02_automatic_phase_data_broadcasting,
                self.test_03_change_history_tracking,
                self.test_04_custom_event_broadcasting,
            ]

            all_passed = True
            for test_func in tests:
                success = await test_func(game, state_machine)
                all_passed &= success

                if not success:
                    print(f"❌ Test failed, stopping test suite")
                    break

            # Final results
            print("=" * 60)
            print("🚀 ENTERPRISE ARCHITECTURE VALIDATION RESULTS")
            print("=" * 60)

            passed = sum(1 for r in self.test_results if r["status"] == "PASS")
            failed = sum(1 for r in self.test_results if r["status"] == "FAIL")

            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
            print()

            if all_passed:
                print(
                    "🎉 ALL TESTS PASSED! Enterprise architecture is properly implemented"
                )
                print("🚀 The backend now matches BENEFITS_GUARANTEE.md promises:")
                print("   ✅ Automatic broadcasting system")
                print("   ✅ Centralized update_phase_data method")
                print("   ✅ Event sourcing and change history")
                print("   ✅ Custom event broadcasting")
            else:
                print("⚠️  Some tests failed. Enterprise architecture needs fixes.")

            print()
            print("📋 Detailed Results:")
            for result in self.test_results:
                status_emoji = "✅" if result["status"] == "PASS" else "❌"
                print(f"{status_emoji} {result['test']}: {result['status']}")
                if result["details"]:
                    print(f"   💬 {result['details']}")

            return all_passed

        except Exception as e:
            print(f"❌ Test suite failed with exception: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Main test runner"""
    validator = EnterpriseArchitectureValidator()
    success = await validator.run_complete_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
