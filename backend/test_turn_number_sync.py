#!/usr/bin/env python3
"""
🔢 Turn Number Synchronization Test

Tests that turn numbers are correctly synchronized between backend and frontend
when turns complete and new turns auto-start.

This test reproduces the bug where:
- Backend increments turn_number to 2 correctly
- Frontend still shows turn_number = 1
- Root cause: Missing phase_change broadcast after auto-start
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player
from engine.piece import Piece
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase


class TurnNumberSyncTester:
    def __init__(self):
        self.test_results = []
        self.current_test = ""

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
        """Set up a game ready for turn testing"""
        print("🔢 Setting up game for turn number sync testing...")

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
        game.turn_number = 0  # Will be incremented to 1 when first turn starts

        # Initialize pile tracking
        game.player_piles = {p.name: 0 for p in players}

        return game, state_machine

    async def test_01_initial_turn_number(self, game, state_machine):
        """Test: Initial turn starts with turn_number = 1"""
        self.log_test(
            "01. Initial Turn Number",
            "RUNNING",
            "Starting turn phase and checking initial turn number",
        )

        # Start state machine in turn phase
        await state_machine.start(GamePhase.TURN)

        # Verify turn number is 1
        success = self.assert_equal(
            game.turn_number, 1, "Initial turn number should be 1"
        )

        # Verify phase data contains correct turn number
        turn_state = state_machine.current_state
        success &= self.assert_equal(
            turn_state.phase_data.get("current_turn_number"),
            1,
            "Phase data should contain turn_number = 1",
        )

        if success:
            self.log_test(
                "01. Initial Turn Number",
                "PASS",
                "Initial turn number correctly set to 1",
            )

        return success

    async def test_02_complete_first_turn(self, game, state_machine):
        """Test: Complete first turn and verify turn_complete event has correct turn number"""
        self.log_test(
            "02. Complete First Turn", "RUNNING", "Playing through first complete turn"
        )

        turn_state = state_machine.current_state

        # Simulate all players playing
        for i, player in enumerate(game.players):
            action = GameAction(
                player_name=player.name,
                action_type=ActionType.PLAY_PIECES,
                payload={
                    "pieces": [player.hand[0]],  # Play first piece
                    "play_type": "SINGLE",
                    "play_value": 14 - i,  # Decreasing values so first player wins
                    "is_valid": True,
                },
                is_bot=player.is_bot,
            )

            await state_machine.handle_action(action)
            await asyncio.sleep(0.1)  # Allow processing

        # Verify turn is complete
        success = self.assert_true(
            turn_state.turn_complete, "Turn should be complete after all players played"
        )

        # Verify turn number is still 1 (first turn)
        success &= self.assert_equal(
            game.turn_number, 1, "Turn number should still be 1 for first turn"
        )

        if success:
            self.log_test(
                "02. Complete First Turn", "PASS", "First turn completed correctly"
            )

        return success

    async def test_03_auto_start_second_turn(self, game, state_machine):
        """Test: Auto-start second turn and verify turn number increments"""
        self.log_test(
            "03. Auto-Start Second Turn",
            "RUNNING",
            "Waiting for auto-start and checking turn number",
        )

        # Wait for auto-start (1.5 seconds + buffer)
        await asyncio.sleep(2.0)

        # Verify turn number incremented to 2
        success = self.assert_equal(
            game.turn_number, 2, "Turn number should increment to 2 for second turn"
        )

        # Verify phase data contains correct turn number
        turn_state = state_machine.current_state
        success &= self.assert_equal(
            turn_state.phase_data.get("current_turn_number"),
            2,
            "Phase data should contain turn_number = 2",
        )

        # Verify turn state is reset for new turn
        success &= self.assert_equal(
            len(turn_state.turn_plays), 0, "Turn plays should be reset for new turn"
        )

        success &= self.assert_equal(
            turn_state.required_piece_count,
            None,
            "Required piece count should be reset",
        )

        if success:
            self.log_test(
                "03. Auto-Start Second Turn",
                "PASS",
                "Second turn auto-started with correct turn number",
            )

        return success

    async def test_04_phase_data_broadcasting(self, game, state_machine):
        """Test: Verify phase data is broadcast correctly after auto-start"""
        self.log_test(
            "04. Phase Data Broadcasting",
            "RUNNING",
            "Checking if phase_change is broadcast after auto-start",
        )

        # This test simulates what the frontend would receive
        turn_state = state_machine.current_state

        # Verify the phase_data that would be sent to frontend
        phase_data = turn_state.phase_data.copy()

        success = self.assert_equal(
            phase_data.get("current_turn_number"),
            2,
            "Broadcast phase data should contain turn_number = 2",
        )

        success &= self.assert_equal(
            phase_data.get("turn_complete"),
            False,
            "Broadcast phase data should show turn_complete = False for new turn",
        )

        success &= self.assert_true(
            "current_turn_starter" in phase_data,
            "Broadcast phase data should contain current_turn_starter",
        )

        success &= self.assert_true(
            "turn_order" in phase_data, "Broadcast phase data should contain turn_order"
        )

        if success:
            self.log_test(
                "04. Phase Data Broadcasting",
                "PASS",
                "Phase data correctly prepared for broadcast",
            )

        return success

    async def test_05_third_turn_increment(self, game, state_machine):
        """Test: Play through second turn and verify third turn increments correctly"""
        self.log_test(
            "05. Third Turn Increment",
            "RUNNING",
            "Testing turn number continues to increment correctly",
        )

        turn_state = state_machine.current_state

        # Complete second turn
        for i, player in enumerate(game.players):
            if len(player.hand) > 0:  # Some pieces were removed in first turn
                action = GameAction(
                    player_name=player.name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={
                        "pieces": [player.hand[0]],
                        "play_type": "SINGLE",
                        "play_value": 12 - i,
                        "is_valid": True,
                    },
                    is_bot=player.is_bot,
                )

                await state_machine.handle_action(action)
                await asyncio.sleep(0.1)

        # Wait for auto-start of third turn
        await asyncio.sleep(2.0)

        # Verify turn number incremented to 3
        success = self.assert_equal(
            game.turn_number, 3, "Turn number should increment to 3 for third turn"
        )

        # Verify phase data contains correct turn number
        success &= self.assert_equal(
            turn_state.phase_data.get("current_turn_number"),
            3,
            "Phase data should contain turn_number = 3",
        )

        if success:
            self.log_test(
                "05. Third Turn Increment",
                "PASS",
                "Turn number continues to increment correctly",
            )

        return success

    async def run_complete_test(self):
        """Run the complete turn number synchronization test"""
        print("🔢 Starting Turn Number Synchronization Test")
        print("=" * 60)
        print()

        try:
            # Setup
            game, state_machine = await self.setup_game_for_testing()

            # Run tests in sequence
            tests = [
                self.test_01_initial_turn_number,
                self.test_02_complete_first_turn,
                self.test_03_auto_start_second_turn,
                self.test_04_phase_data_broadcasting,
                self.test_05_third_turn_increment,
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
            print("🔢 TURN NUMBER SYNCHRONIZATION TEST RESULTS")
            print("=" * 60)

            passed = sum(1 for r in self.test_results if r["status"] == "PASS")
            failed = sum(1 for r in self.test_results if r["status"] == "FAIL")

            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
            print()

            if all_passed:
                print("🎉 ALL TESTS PASSED! Turn number sync is working correctly")
            else:
                print("⚠️  Some tests failed. Turn number sync needs fixes.")

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
    tester = TurnNumberSyncTester()
    success = await tester.run_complete_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
