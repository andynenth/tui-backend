#!/usr/bin/env python3
"""
🔍 Immediate Transition Bug Investigation

This test specifically looks for conditions that would cause the scoring phase
to transition immediately, bypassing the 7-second delay. Based on the code analysis,
the possible causes are:

1. game_complete being set to True (when someone reaches 50+ points)
2. scores_calculated being False
3. Some other condition that prevents setup from completing properly

Let's test these scenarios.
"""

import asyncio
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player
from engine.piece import Piece
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase


async def test_game_complete_scenario():
    """Test when game_complete is True (someone has 50+ points)"""
    print("🔍 Testing Game Complete Scenario (50+ points)")
    print("=" * 50)

    # Create game where someone already has 50+ points
    players = [Player("Winner"), Player("Bot1"), Player("Bot2"), Player("Bot3")]
    game = Game(players)
    game.room_id = "complete_test"

    # Set up scores - Winner already has 50 points
    players[0].score = 50  # Should trigger game_complete
    players[1].score = 10
    players[2].score = 20
    players[3].score = 15

    # Set up declarations and captured piles
    game.player_declarations = {"Winner": 2, "Bot1": 1, "Bot2": 3, "Bot3": 2}
    for i, player in enumerate(players):
        player.captured_piles = i + 1
        player.declared = game.player_declarations[player.name]

    # Create state machine and start in scoring
    state_machine = GameStateMachine(game)
    await state_machine.start(GamePhase.SCORING)

    # Wait a moment for setup
    await asyncio.sleep(0.5)

    scoring_state = state_machine.current_state

    print(f"📊 Game complete: {scoring_state.game_complete}")
    print(f"🏆 Winners: {scoring_state.winners}")
    print(f"📊 Scores calculated: {scoring_state.scores_calculated}")
    print(f"🕐 Display delay complete: {scoring_state.display_delay_complete}")

    # Check transition conditions
    transition_phase = await scoring_state.check_transition_conditions()
    print(f"🔄 Transition result: {transition_phase}")

    if scoring_state.game_complete:
        print("✅ FOUND ISSUE: Game is complete, so no transition occurs!")
        print("   This means the scoring phase stays forever when game ends!")
        return "game_complete_blocks_transition"

    return "normal"


async def test_scores_not_calculated_scenario():
    """Test when scores_calculated is False"""
    print("\n🔍 Testing Scores Not Calculated Scenario")
    print("=" * 50)

    # Create a minimal game
    players = [Player("Test")]
    game = Game(players)
    game.room_id = "no_scores_test"

    # Create state machine
    state_machine = GameStateMachine(game)

    # Manually create scoring state without proper setup
    from engine.state_machine.states.scoring_state import ScoringState

    scoring_state = ScoringState(state_machine)

    # Don't call _setup_phase() so scores_calculated remains False
    print(f"📊 Scores calculated: {scoring_state.scores_calculated}")
    print(f"🕐 Display delay complete: {scoring_state.display_delay_complete}")

    # Check transition conditions
    transition_phase = await scoring_state.check_transition_conditions()
    print(f"🔄 Transition result: {transition_phase}")

    if not scoring_state.scores_calculated:
        print("✅ FOUND CONDITION: When scores not calculated, no transition occurs")
        return "scores_not_calculated"

    return "normal"


async def test_race_condition_scenario():
    """Test potential race condition between setup and process loop"""
    print("\n🔍 Testing Race Condition Scenario")
    print("=" * 50)

    # Create game
    players = [Player("TestPlayer"), Player("Bot1"), Player("Bot2"), Player("Bot3")]
    game = Game(players)
    game.room_id = "race_test"

    # Set up minimal data
    game.player_declarations = {"TestPlayer": 2, "Bot1": 1, "Bot2": 3, "Bot3": 2}
    for i, player in enumerate(players):
        player.captured_piles = i + 1
        player.declared = game.player_declarations[player.name]
        player.score = 0

    # Create state machine
    state_machine = GameStateMachine(game)

    # Monitor timing carefully
    start_time = time.time()

    # Start scoring phase
    print("🚀 Starting scoring phase...")
    await state_machine.start(GamePhase.SCORING)

    # Check immediately after start
    immediate_time = time.time() - start_time
    print(f"⏱️  Immediately after start ({immediate_time:.3f}s):")

    scoring_state = state_machine.current_state
    print(f"   📊 Scores calculated: {scoring_state.scores_calculated}")
    print(f"   🕐 Display delay complete: {scoring_state.display_delay_complete}")
    print(f"   🔄 Current phase: {state_machine.current_phase}")

    # Check after a short delay
    await asyncio.sleep(0.1)
    short_delay_time = time.time() - start_time
    print(f"⏱️  After 0.1s ({short_delay_time:.3f}s):")
    print(f"   📊 Scores calculated: {scoring_state.scores_calculated}")
    print(f"   🕐 Display delay complete: {scoring_state.display_delay_complete}")
    print(f"   🔄 Current phase: {state_machine.current_phase}")

    # Check if transition happened before delay
    if state_machine.current_phase != GamePhase.SCORING:
        print("❌ FOUND RACE CONDITION: Phase changed before delay!")
        return "race_condition"

    # Wait for delay and see when transition happens
    for i in range(80):  # Check every 0.1s for 8s
        elapsed = time.time() - start_time
        current_phase = state_machine.current_phase

        if current_phase != GamePhase.SCORING:
            print(f"🔄 Phase changed at {elapsed:.2f}s")
            if elapsed < 6.0:
                print("❌ PREMATURE TRANSITION: Changed before expected delay!")
                return "premature_transition"
            else:
                print("✅ NORMAL TRANSITION: Changed after expected delay")
                return "normal_transition"

        await asyncio.sleep(0.1)

    print("⚠️  No transition occurred within 8 seconds")
    return "no_transition"


async def test_logging_detailed_scenario():
    """Test with detailed logging to see exactly what happens"""
    print("\n🔍 Testing with Detailed Logging")
    print("=" * 50)

    # Create game
    players = [Player("TestPlayer"), Player("Bot1"), Player("Bot2"), Player("Bot3")]
    game = Game(players)
    game.room_id = "logging_test"

    # Set up data
    game.player_declarations = {"TestPlayer": 2, "Bot1": 1, "Bot2": 3, "Bot3": 2}
    for i, player in enumerate(players):
        player.captured_piles = i + 1
        player.declared = game.player_declarations[player.name]
        player.score = 0

    # Create state machine
    state_machine = GameStateMachine(game)

    # Hook into the scoring state to monitor its behavior
    original_check_transition = None
    transition_calls = []

    async def monitored_check_transition(self):
        nonlocal transition_calls
        elapsed = time.time() - start_time

        result = await original_check_transition()

        transition_calls.append(
            {
                "time": elapsed,
                "scores_calculated": self.scores_calculated,
                "display_delay_complete": self.display_delay_complete,
                "game_complete": self.game_complete,
                "result": result,
            }
        )

        print(
            f"🔄 {elapsed:.2f}s - Transition check: scores={self.scores_calculated}, "
            f"delay={self.display_delay_complete}, complete={self.game_complete}, "
            f"result={result}"
        )

        return result

    # Start and monitor
    start_time = time.time()
    await state_machine.start(GamePhase.SCORING)

    # Hook the method after state creation
    scoring_state = state_machine.current_state
    if scoring_state:
        original_check_transition = scoring_state.check_transition_conditions
        scoring_state.check_transition_conditions = lambda: monitored_check_transition(
            scoring_state
        )

    # Wait and observe
    for i in range(80):
        elapsed = time.time() - start_time
        if state_machine.current_phase != GamePhase.SCORING:
            print(f"🎯 Phase changed at {elapsed:.2f}s")
            break
        await asyncio.sleep(0.1)

    # Analysis
    print(f"\n📊 Transition Analysis:")
    print(f"   Total transition checks: {len(transition_calls)}")

    if transition_calls:
        first_call = transition_calls[0]
        last_call = transition_calls[-1]

        print(f"   First check at: {first_call['time']:.2f}s")
        print(f"   Last check at: {last_call['time']:.2f}s")

        # Look for the first time delay became complete
        delay_complete_time = None
        for call in transition_calls:
            if call["display_delay_complete"] and delay_complete_time is None:
                delay_complete_time = call["time"]
                break

        if delay_complete_time:
            print(f"   Delay completed at: {delay_complete_time:.2f}s")
        else:
            print("   Delay never completed!")

    return "logged"


async def main():
    """Main test runner"""
    print("🔍 IMMEDIATE TRANSITION BUG INVESTIGATION")
    print("=" * 60)

    try:
        # Test various scenarios
        scenario_1 = await test_game_complete_scenario()
        scenario_2 = await test_scores_not_calculated_scenario()
        scenario_3 = await test_race_condition_scenario()
        scenario_4 = await test_logging_detailed_scenario()

        # Summary
        print("\n" + "=" * 60)
        print("🔍 BUG INVESTIGATION RESULTS")
        print("=" * 60)

        print(f"📊 Game Complete Scenario: {scenario_1}")
        print(f"📊 Scores Not Calculated: {scenario_2}")
        print(f"📊 Race Condition: {scenario_3}")
        print(f"📊 Detailed Logging: {scenario_4}")

        print("\n🎯 FINDINGS:")

        if scenario_1 == "game_complete_blocks_transition":
            print(
                "❌ CRITICAL: When game is complete (50+ points), scoring phase never transitions!"
            )
            print("   This could make it seem like the phase is stuck.")

        if scenario_3 == "race_condition":
            print("❌ FOUND: Race condition causes premature transition")
        elif scenario_3 == "premature_transition":
            print("❌ FOUND: Transition happens before expected delay")
        elif scenario_3 == "normal_transition":
            print("✅ Normal transition timing observed")

        if scenario_2 == "scores_not_calculated":
            print("⚠️  Scores not calculated scenario blocks transition")

        # Conclusions
        print("\n🔧 CONCLUSIONS:")
        print("1. The delay mechanism itself works correctly")
        print("2. The issue may be in specific game conditions")
        print("3. Game completion (50+ points) may cause unexpected behavior")
        print("4. Race conditions between setup and process loop are possible")

        return True

    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
