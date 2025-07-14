#!/usr/bin/env python3
"""
🎮 Complete Turn Phase Flow Test

Tests the entire turn phase flow from start to end round according to TURN_PHASE_DIAGRAM.md

This test validates:
1. Turn Phase Start - Set first turn starter based on round starter
2. New Turn - Start new turn with proper order
3. Starter Play - Starter plays 1-6 pieces and sets piece count
4. Validation - Starter's play must be valid
5. Set Piece Count - Required count set for other players
6. Others Play - Other players must match piece count
7. Collect Plays - All players participate
8. Determine Winner - Correct winner calculation
9. Winner Takes Piles - Pile distribution
10. Update Score - Pile count tracking
11. Check Next Turn - Continue or transition to scoring
12. Next Turn Starter - Winner starts next turn
13. Round Complete - All hands empty triggers scoring phase
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction
from engine.state_machine.game_state_machine import GameStateMachine


class TurnPhaseFlowTester:
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

    def assert_in(self, item, collection, message=""):
        """Assert item is in collection"""
        if item in collection:
            return True
        else:
            self.log_test(
                self.current_test, "FAIL", f"{message} - {item} not in {collection}"
            )
            return False

    async def setup_game_for_testing(self):
        """Set up a game with known pieces for predictable testing"""
        print("🎯 Setting up game for testing...")

        # Create players
        players = [
            Player("TestPlayer", is_bot=False),
            Player("Bot1", is_bot=True),
            Player("Bot2", is_bot=True),
            Player("Bot3", is_bot=True),
        ]

        # Create game
        game = Game(players)
        game.room_id = "test_room"  # Set room_id on game object

        # Set up state machine
        state_machine = GameStateMachine(game)

        # Manually set up controlled hands for testing
        # TestPlayer starts (has RED_GENERAL)
        game.players[0].hand = [
            Piece("GENERAL_RED"),  # Strong starter piece (14 pts)
            Piece("ADVISOR_RED"),  # Medium piece (12 pts)
            Piece("ELEPHANT_RED"),  # Medium piece (10 pts)
            Piece("CHARIOT_RED"),  # Medium piece (8 pts)
            Piece("HORSE_RED"),  # Weak piece (6 pts)
            Piece("CANNON_RED"),  # Weak piece (4 pts)
            Piece("SOLDIER_RED"),  # Weak piece (2 pts)
            Piece("SOLDIER_RED"),  # Weak piece (2 pts)
        ]

        # Bot1 hand
        game.players[1].hand = [
            Piece("GENERAL_BLACK"),  # Strong piece (13 pts)
            Piece("ADVISOR_BLACK"),  # Medium piece (11 pts)
            Piece("ELEPHANT_BLACK"),  # Medium piece (9 pts)
            Piece("CHARIOT_BLACK"),  # Medium piece (7 pts)
            Piece("HORSE_BLACK"),  # Weak piece (5 pts)
            Piece("CANNON_BLACK"),  # Weak piece (3 pts)
            Piece("SOLDIER_BLACK"),  # Weak piece (1 pt)
            Piece("SOLDIER_BLACK"),  # Weak piece (1 pt)
        ]

        # Bot2 hand
        game.players[2].hand = [
            Piece("ADVISOR_RED"),  # Medium piece (12 pts)
            Piece("ADVISOR_BLACK"),  # Medium piece (11 pts)
            Piece("ELEPHANT_RED"),  # Medium piece (10 pts)
            Piece("ELEPHANT_BLACK"),  # Medium piece (9 pts)
            Piece("CHARIOT_RED"),  # Medium piece (8 pts)
            Piece("CHARIOT_BLACK"),  # Medium piece (7 pts)
            Piece("HORSE_RED"),  # Weak piece (6 pts)
            Piece("HORSE_BLACK"),  # Weak piece (5 pts)
        ]

        # Bot3 hand
        game.players[3].hand = [
            Piece("CANNON_RED"),  # Weak piece (4 pts)
            Piece("CANNON_BLACK"),  # Weak piece (3 pts)
            Piece("SOLDIER_RED"),  # Weak piece (2 pts)
            Piece("SOLDIER_BLACK"),  # Weak piece (1 pt)
            Piece("SOLDIER_RED"),  # Weak piece (2 pts)
            Piece("SOLDIER_BLACK"),  # Weak piece (1 pt)
            Piece("SOLDIER_RED"),  # Weak piece (2 pts)
            Piece("SOLDIER_BLACK"),  # Weak piece (1 pt)
        ]

        # Set round starter to TestPlayer (has RED_GENERAL)
        game.round_starter = "TestPlayer"
        game.current_player = "TestPlayer"
        game.turn_number = 0  # Will be incremented to 1 when first turn starts

        # Initialize pile tracking
        game.player_piles = {p.name: 0 for p in players}

        return game, state_machine

    async def test_01_turn_phase_initialization(self, game, state_machine):
        """Test: Turn Phase Start - Set first turn starter based on round starter"""
        self.log_test(
            "01. Turn Phase Start",
            "RUNNING",
            "Setting first turn starter based on round starter",
        )

        # Start state machine in turn phase
        from engine.state_machine.core import GamePhase

        await state_machine.start(GamePhase.TURN)

        # Verify phase
        success = self.assert_equal(
            state_machine.current_phase.value, "turn", "Should be in turn phase"
        )

        # Verify starter is set correctly
        turn_state = state_machine.current_state
        success &= self.assert_equal(
            turn_state.current_turn_starter,
            "TestPlayer",
            "First turn starter should be round starter",
        )

        # Verify turn order starts with starter
        success &= self.assert_equal(
            turn_state.turn_order[0],
            "TestPlayer",
            "Turn order should start with starter",
        )

        # Verify turn number
        success &= self.assert_equal(
            game.turn_number, 1, "Turn number should be 1 for first turn"
        )

        if success:
            self.log_test(
                "01. Turn Phase Start",
                "PASS",
                "Turn phase initialized correctly with proper starter",
            )

        return success

    async def test_02_starter_plays_pieces(self, game, state_machine):
        """Test: Starter Play - Starter plays 1-6 pieces and sets piece count"""
        self.log_test("02. Starter Play", "RUNNING", "Testing starter plays 1-6 pieces")

        turn_state = state_machine.current_state

        # Verify it's starter's turn
        success = self.assert_equal(
            turn_state._get_current_player(), "TestPlayer", "Should be starter's turn"
        )

        # Verify no piece count set yet
        success &= self.assert_equal(
            turn_state.required_piece_count,
            None,
            "Required piece count should not be set yet",
        )

        # Test starter plays 2 pieces (GENERAL + ADVISOR)
        starter_pieces = game.players[0].hand[:2]  # Take first 2 pieces
        action = GameAction(
            player_name="TestPlayer",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": starter_pieces,
                "play_type": "PAIR",
                "play_value": sum(p.point for p in starter_pieces),
                "is_valid": True,
            },
        )

        # Process the action
        result = await state_machine.handle_action(action)

        # Wait for action to be processed
        await asyncio.sleep(0.2)

        # Verify action was accepted
        success &= self.assert_true(
            result.get("success", False), "Starter's play should be accepted"
        )

        # Verify piece count is now set
        success &= self.assert_equal(
            turn_state.required_piece_count,
            2,
            "Required piece count should be set to 2",
        )

        # Verify starter's play is recorded
        success &= self.assert_in(
            "TestPlayer", turn_state.turn_plays, "Starter's play should be recorded"
        )

        # Verify it's now next player's turn
        success &= self.assert_equal(
            turn_state._get_current_player(), "Bot1", "Should be next player's turn"
        )

        if success:
            self.log_test(
                "02. Starter Play",
                "PASS",
                "Starter played 2 pieces and set required count",
            )

        return success

    async def test_03_others_must_match_count(self, game, state_machine):
        """Test: Others Play - Other players must match piece count"""
        self.log_test(
            "03. Others Match Count",
            "RUNNING",
            "Testing other players must match piece count",
        )

        turn_state = state_machine.current_state

        # Bot1 plays exactly 2 pieces (matching required count)
        bot1_pieces = game.players[1].hand[:2]  # Take first 2 pieces
        action1 = GameAction(
            player_name="Bot1",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": bot1_pieces,
                "play_type": "PAIR",
                "play_value": sum(p.point for p in bot1_pieces),
                "is_valid": True,
            },
            is_bot=True,
        )

        result1 = await state_machine.handle_action(action1)
        await asyncio.sleep(0.2)
        success = self.assert_true(
            result1.get("success", False), "Bot1's matching play should be accepted"
        )

        # Bot2 plays exactly 2 pieces
        bot2_pieces = game.players[2].hand[:2]
        action2 = GameAction(
            player_name="Bot2",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": bot2_pieces,
                "play_type": "PAIR",
                "play_value": sum(p.point for p in bot2_pieces),
                "is_valid": True,
            },
            is_bot=True,
        )

        result2 = await state_machine.handle_action(action2)
        await asyncio.sleep(0.2)
        success &= self.assert_true(
            result2.get("success", False), "Bot2's matching play should be accepted"
        )

        # Bot3 plays exactly 2 pieces
        bot3_pieces = game.players[3].hand[:2]
        action3 = GameAction(
            player_name="Bot3",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": bot3_pieces,
                "play_type": "PAIR",
                "play_value": sum(p.point for p in bot3_pieces),
                "is_valid": True,
            },
            is_bot=True,
        )

        result3 = await state_machine.handle_action(action3)
        await asyncio.sleep(0.2)
        success &= self.assert_true(
            result3.get("success", False), "Bot3's matching play should be accepted"
        )

        # Verify all players have played
        success &= self.assert_equal(
            len(turn_state.turn_plays), 4, "All 4 players should have played"
        )

        # Verify turn is complete
        success &= self.assert_true(
            turn_state.turn_complete, "Turn should be complete after all players played"
        )

        if success:
            self.log_test(
                "03. Others Match Count",
                "PASS",
                "All players matched required piece count",
            )

        return success

    async def test_04_determine_winner_and_piles(self, game, state_machine):
        """Test: Determine Winner and Winner Takes Piles"""
        self.log_test(
            "04. Winner & Piles",
            "RUNNING",
            "Testing winner determination and pile distribution",
        )

        turn_state = state_machine.current_state

        # Verify winner was determined
        success = self.assert_true(
            turn_state.winner is not None, "A winner should be determined"
        )

        if turn_state.winner:
            print(f"   🏆 Winner: {turn_state.winner}")

            # Check winner got the correct number of piles
            expected_piles = turn_state.required_piece_count or 1
            actual_piles = game.player_piles.get(turn_state.winner, 0)

            success &= self.assert_equal(
                actual_piles,
                expected_piles,
                f"Winner should get {expected_piles} piles",
            )

            # Verify pieces were removed from hands
            for player in game.players:
                player_name = player.name
                if player_name in turn_state.turn_plays:
                    play_data = turn_state.turn_plays[player_name]
                    pieces_played = play_data["pieces"]

                    # Check that played pieces are no longer in hand
                    for piece in pieces_played:
                        success &= self.assert_true(
                            piece not in player.hand,
                            f"Played piece {piece} should be removed from {player_name}'s hand",
                        )

        if success:
            self.log_test(
                "04. Winner & Piles",
                "PASS",
                f"Winner {turn_state.winner} correctly awarded piles",
            )

        return success

    async def test_05_next_turn_or_round_complete(self, game, state_machine):
        """Test: Check Next Turn - Continue or transition to scoring"""
        self.log_test(
            "05. Next Turn/Round Complete",
            "RUNNING",
            "Testing turn continuation or round completion",
        )

        turn_state = state_machine.current_state

        # Check if any hands are empty
        all_hands_empty = all(len(player.hand) == 0 for player in game.players)

        if all_hands_empty:
            # Should transition to scoring
            next_phase = await turn_state.check_transition_conditions()
            success = self.assert_equal(
                next_phase.value if next_phase else None,
                "scoring",
                "Should transition to scoring when all hands empty",
            )

            if success:
                self.log_test(
                    "05. Next Turn/Round Complete",
                    "PASS",
                    "Round complete - transitioning to scoring",
                )
        else:
            # Should start next turn with winner as starter
            winner = turn_state.winner

            # Wait for automatic next turn start
            await asyncio.sleep(2)  # Wait for 1.5s auto-start + buffer

            # Verify new turn started
            success = self.assert_equal(
                game.turn_number, 2, "Turn number should increment to 2"
            )

            # Verify winner is new starter
            success &= self.assert_equal(
                turn_state.current_turn_starter,
                winner,
                "Winner should be starter of next turn",
            )

            # Verify turn state reset
            success &= self.assert_equal(
                len(turn_state.turn_plays), 0, "Turn plays should be reset for new turn"
            )

            success &= self.assert_equal(
                turn_state.required_piece_count,
                None,
                "Required piece count should be reset",
            )

            success &= self.assert_false(
                turn_state.turn_complete, "Turn complete flag should be reset"
            )

            if success:
                self.log_test(
                    "05. Next Turn/Round Complete",
                    "PASS",
                    f"Next turn started with {winner} as starter",
                )

        return success

    async def test_06_complete_multiple_turns(self, game, state_machine):
        """Test: Complete multiple turns until round ends"""
        self.log_test(
            "06. Multiple Turns", "RUNNING", "Testing complete turns until round ends"
        )

        turn_count = 1  # Already completed 1 turn
        max_turns = 8  # Safety limit (8 pieces per player max)

        while turn_count < max_turns:
            # Check if all hands are empty
            all_hands_empty = all(len(player.hand) == 0 for player in game.players)
            if all_hands_empty:
                break

            turn_count += 1
            print(f"   🔄 Playing turn {turn_count}")

            turn_state = state_machine.current_state
            starter = turn_state.current_turn_starter

            # Play a complete turn with all players
            for i, player in enumerate(game.players):
                if len(player.hand) == 0:
                    continue

                player_name = player.name
                current_player = turn_state._get_current_player()

                if player_name != current_player:
                    continue

                # Determine how many pieces to play
                if turn_state.required_piece_count is None:
                    # Starter sets the count (play 1 piece for simplicity)
                    pieces_to_play = min(1, len(player.hand))
                else:
                    # Match required count
                    pieces_to_play = min(
                        turn_state.required_piece_count, len(player.hand)
                    )

                if pieces_to_play == 0:
                    continue

                # Play pieces
                pieces = player.hand[:pieces_to_play]
                action = GameAction(
                    player_name=player_name,
                    action_type=ActionType.PLAY_PIECES,
                    payload={
                        "pieces": pieces,
                        "play_type": "SINGLE" if pieces_to_play == 1 else "MULTIPLE",
                        "play_value": sum(p.point for p in pieces),
                        "is_valid": True,
                    },
                    is_bot=player.is_bot,
                )

                await state_machine.handle_action(action)

                # Wait for action to be processed
                await asyncio.sleep(0.2)

            # Wait for turn completion and next turn start
            await asyncio.sleep(2)

        # Verify round completed properly
        all_hands_empty = all(len(player.hand) == 0 for player in game.players)
        success = self.assert_true(
            all_hands_empty, f"All hands should be empty after {turn_count} turns"
        )

        # Verify total piles equal total pieces played
        total_piles = sum(game.player_piles.values())
        total_pieces_per_player = 8
        total_expected_piles = len(game.players) * total_pieces_per_player

        success &= self.assert_equal(
            total_piles,
            total_expected_piles,
            f"Total piles ({total_piles}) should equal total pieces ({total_expected_piles})",
        )

        if success:
            self.log_test(
                "06. Multiple Turns",
                "PASS",
                f"Completed {turn_count} turns, all hands empty",
            )

        return success

    def assert_false(self, condition, message=""):
        """Assert condition is false"""
        return self.assert_true(not condition, message)

    async def run_complete_test(self):
        """Run the complete turn phase flow test"""
        print("🎮 Starting Complete Turn Phase Flow Test")
        print("=" * 60)
        print()

        try:
            # Setup
            game, state_machine = await self.setup_game_for_testing()

            # Run tests in sequence
            tests = [
                self.test_01_turn_phase_initialization,
                self.test_02_starter_plays_pieces,
                self.test_03_others_must_match_count,
                self.test_04_determine_winner_and_piles,
                self.test_05_next_turn_or_round_complete,
                self.test_06_complete_multiple_turns,
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
            print("🎯 COMPLETE TURN PHASE FLOW TEST RESULTS")
            print("=" * 60)

            passed = sum(1 for r in self.test_results if r["status"] == "PASS")
            failed = sum(1 for r in self.test_results if r["status"] == "FAIL")

            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
            print()

            if all_passed:
                print(
                    "🎉 ALL TESTS PASSED! Turn phase flow matches TURN_PHASE_DIAGRAM.md"
                )
            else:
                print("⚠️  Some tests failed. Turn phase flow needs fixes.")

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
    tester = TurnPhaseFlowTester()
    success = await tester.run_complete_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
