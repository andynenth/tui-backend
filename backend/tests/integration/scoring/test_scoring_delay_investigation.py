#!/usr/bin/env python3
"""
🔍 Scoring Delay Investigation

This test specifically investigates why the 7-second delay in scoring state
isn't working and the phase transitions immediately to preparation.

We'll examine:
1. How the asyncio.create_task() behaves with the delay
2. When check_transition_conditions() is called
3. The flag setting mechanism
4. Any race conditions
"""

import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


async def test_scoring_delay_mechanism():
    """Test the scoring delay mechanism in isolation"""
    print("🔍 Testing Scoring Delay Mechanism")
    print("=" * 50)

    # Create a simple game setup
    players = [Player("TestPlayer"), Player("Bot1"), Player("Bot2"), Player("Bot3")]
    game = Game(players)
    game.room_id = "delay_test"

    # Set up game state for scoring
    game.round_number = 1
    game.player_declarations = {"TestPlayer": 2, "Bot1": 1, "Bot2": 3, "Bot3": 2}

    # Set up captured piles
    for i, player in enumerate(players):
        player.captured_piles = i + 1  # Different actual piles
        player.declared = game.player_declarations[player.name]
        player.score = 0

    # Create state machine
    state_machine = GameStateMachine(game)

    # Manually navigate to scoring phase
    await state_machine.start(GamePhase.SCORING)

    scoring_state = state_machine.current_state

    print(f"✅ Started in scoring phase: {state_machine.current_phase}")
    print(f"🕐 Initial display_delay_complete: {scoring_state.display_delay_complete}")
    print(f"📊 Scores calculated: {scoring_state.scores_calculated}")

    # Wait a moment for setup to complete
    await asyncio.sleep(0.5)

    print(
        f"🕐 After setup - display_delay_complete: {scoring_state.display_delay_complete}"
    )

    # Test the transition conditions immediately
    transition_phase = await scoring_state.check_transition_conditions()
    print(f"🔄 Immediate transition check result: {transition_phase}")

    # Check the state machine's process loop behavior
    print("\n🔄 Testing State Machine Process Loop Behavior")

    # Monitor for 8 seconds to see when the flag changes
    start_time = time.time()
    delay_completed_time = None

    for i in range(80):  # Check every 0.1 seconds for 8 seconds
        current_time = time.time()
        elapsed = current_time - start_time

        if scoring_state.display_delay_complete and delay_completed_time is None:
            delay_completed_time = elapsed
            print(f"🕐 display_delay_complete became True at {elapsed:.2f}s")

        # Check if phase changed
        if state_machine.current_phase != GamePhase.SCORING:
            print(
                f"🔄 Phase changed to {state_machine.current_phase} at {elapsed:.2f}s"
            )
            break

        # Check transition conditions
        if i % 10 == 0:  # Every second
            transition_phase = await scoring_state.check_transition_conditions()
            print(
                f"🕐 {elapsed:.1f}s - delay_complete: {scoring_state.display_delay_complete}, transition: {transition_phase}"
            )

        await asyncio.sleep(0.1)

    final_time = time.time() - start_time
    print(f"\n📊 Final Results after {final_time:.2f}s:")
    print(f"   Current phase: {state_machine.current_phase}")
    print(f"   Display delay completed: {scoring_state.display_delay_complete}")
    print(
        f"   Delay completed at: {delay_completed_time:.2f}s"
        if delay_completed_time
        else "   Delay never completed!"
    )

    return delay_completed_time is not None and delay_completed_time >= 6.5


async def test_async_task_behavior():
    """Test asyncio.create_task behavior vs await behavior"""
    print("\n🔍 Testing Asyncio Task Behavior")
    print("=" * 50)

    # Test 1: Using create_task (like in scoring_state.py)
    print("Test 1: Using asyncio.create_task() (current implementation)")

    flag_1 = False

    async def delay_task_1():
        nonlocal flag_1
        await asyncio.sleep(2.0)
        flag_1 = True
        print("   ✅ Task 1 completed - flag set to True")

    start_time = time.time()
    asyncio.create_task(delay_task_1())  # Don't await

    # Check flag immediately
    print(f"   🕐 Immediately after create_task: flag = {flag_1}")

    # Check flag after delay
    await asyncio.sleep(2.5)
    elapsed_1 = time.time() - start_time
    print(f"   🕐 After {elapsed_1:.2f}s: flag = {flag_1}")

    # Test 2: Using await (alternative implementation)
    print("\nTest 2: Using await (alternative implementation)")

    flag_2 = False

    async def delay_task_2():
        nonlocal flag_2
        await asyncio.sleep(2.0)
        flag_2 = True
        print("   ✅ Task 2 completed - flag set to True")

    start_time = time.time()
    await delay_task_2()  # This will block

    elapsed_2 = time.time() - start_time
    print(f"   🕐 After {elapsed_2:.2f}s: flag = {flag_2}")

    # Test 3: Checking race conditions
    print("\nTest 3: Race condition simulation")

    flag_3 = False

    async def delay_task_3():
        nonlocal flag_3
        await asyncio.sleep(1.0)
        flag_3 = True
        print("   ✅ Task 3 completed - flag set to True")

    # Start task
    asyncio.create_task(delay_task_3())

    # Simulate rapid checking (like state machine process loop)
    for i in range(15):  # Check every 0.1s for 1.5s
        elapsed = i * 0.1
        print(f"   🕐 {elapsed:.1f}s: flag = {flag_3}")
        if flag_3:
            print(f"   🎯 Flag became True at {elapsed:.1f}s")
            break
        await asyncio.sleep(0.1)

    return True


async def test_process_loop_frequency():
    """Test how frequently the state machine process loop runs"""
    print("\n🔍 Testing Process Loop Frequency")
    print("=" * 50)

    # Create a minimal state machine
    players = [Player("Test")]
    game = Game(players)
    game.room_id = "frequency_test"

    state_machine = GameStateMachine(game)

    # Monitor process loop calls
    original_process_loop = state_machine._process_loop
    call_count = 0
    call_times = []

    async def monitored_process_loop():
        nonlocal call_count, call_times
        call_count += 1
        call_times.append(time.time())
        if call_count <= 10:  # Only log first 10 calls
            print(f"   📊 Process loop call #{call_count}")
        return await original_process_loop()

    # Replace the process loop
    state_machine._process_loop = monitored_process_loop

    # Start and monitor for 2 seconds
    await state_machine.start(GamePhase.SCORING)
    start_time = time.time()

    await asyncio.sleep(2.0)

    # Stop monitoring
    await state_machine.stop()

    # Analyze frequency
    if len(call_times) > 1:
        intervals = [
            call_times[i] - call_times[i - 1]
            for i in range(1, min(len(call_times), 11))
        ]
        avg_interval = sum(intervals) / len(intervals)
        frequency = 1.0 / avg_interval

        print(f"   📊 Process loop statistics:")
        print(f"      Total calls in 2s: {call_count}")
        print(f"      Average interval: {avg_interval:.3f}s")
        print(f"      Frequency: {frequency:.1f} Hz")
        print(f"      Expected: ~10 Hz (0.1s intervals)")

    return True


async def main():
    """Main investigation runner"""
    print("🔍 SCORING DELAY INVESTIGATION")
    print("=" * 60)

    try:
        # Test 1: Core delay mechanism
        print("Phase 1: Core delay mechanism")
        delay_works = await test_scoring_delay_mechanism()

        # Test 2: Async task behavior
        print("\nPhase 2: Async task behavior")
        await test_async_task_behavior()

        # Test 3: Process loop frequency
        print("\nPhase 3: Process loop frequency")
        await test_process_loop_frequency()

        # Summary
        print("\n" + "=" * 60)
        print("🔍 INVESTIGATION SUMMARY")
        print("=" * 60)

        if delay_works:
            print("✅ Delay mechanism works correctly")
            print("🤔 Issue may be elsewhere in the system")
        else:
            print("❌ Delay mechanism is not working")
            print("🔧 The 7-second delay is not being respected")

        print("\n🎯 LIKELY CAUSES:")
        print("1. Race condition between task creation and transition checking")
        print("2. Process loop calling check_transition_conditions() too early")
        print("3. Task not being properly awaited or monitored")
        print("4. Flag not being set correctly by the background task")
        print("5. State machine transitioning before setup is complete")

        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Use await instead of create_task for the delay")
        print("2. Add proper synchronization between setup and transition checking")
        print("3. Add debugging logs to track when the flag is set")
        print("4. Consider using a different approach for the delay mechanism")

        return delay_works

    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
