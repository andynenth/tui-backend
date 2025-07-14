#!/usr/bin/env python3
"""
Test script to verify the refined deduplication logic allows legitimate sequential triggers
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from engine.bot_manager import BotManager, GameBotHandler
from engine.game import Game
from engine.piece import Piece
from engine.player import Player


async def test_legitimate_sequential_triggers():
    """Test that legitimate sequential triggers are allowed for current player"""
    print("🧪 Testing legitimate sequential triggers...")

    # Create test setup
    players = [Player("Bot 3", is_bot=True)]
    game = Game(players)

    bot_manager = BotManager()
    bot_manager.register_game("test_room", game)
    handler = bot_manager.active_games["test_room"]

    # Test scenario: Bot 3 is current player, gets triggered from different sources
    print("\\n🎯 Step 1: Bot 3 triggered from phase_change (should be allowed)...")

    context1 = {
        "phase": "turn",
        "turn_number": 1,
        "current_player": "Bot 3",
        "required_count": 1,
        "trigger_source": "phase_change",
    }

    is_dup_1 = handler._is_duplicate_action("Bot 3", "play_pieces", context1)
    print(f"   Phase change trigger: duplicate = {is_dup_1}")

    print(
        "\\n🎯 Step 2: Bot 3 triggered from player_played (should be allowed - different source)..."
    )

    context2 = {
        "phase": "turn",
        "turn_number": 1,
        "current_player": "Bot 3",
        "required_count": 1,
        "trigger_source": "player_played",
    }

    is_dup_2 = handler._is_duplicate_action("Bot 3", "play_pieces", context2)
    print(f"   Player played trigger: duplicate = {is_dup_2}")

    print(
        "\\n🎯 Step 3: Bot 3 triggered again from phase_change rapidly (should be blocked - same source)..."
    )

    # Wait a tiny bit but not enough to clear cache
    await asyncio.sleep(0.1)

    context3 = {
        "phase": "turn",
        "turn_number": 1,
        "current_player": "Bot 3",
        "required_count": 1,
        "trigger_source": "phase_change",
    }

    is_dup_3 = handler._is_duplicate_action("Bot 3", "play_pieces", context3)
    print(f"   Rapid phase change trigger: duplicate = {is_dup_3}")

    # Expected results:
    # 1. First phase_change trigger: NOT duplicate (allowed)
    # 2. Player_played trigger: NOT duplicate (different source, allowed)
    # 3. Rapid phase_change trigger: DUPLICATE (same source too soon, blocked)

    if not is_dup_1 and not is_dup_2 and is_dup_3:
        print("\\n✅ SUCCESS: Refined deduplication working correctly!")
        print("   • Different trigger sources allowed for current player")
        print("   • Rapid same-source triggers blocked")
        return True
    else:
        print(f"\\n❌ FAILURE: Refined deduplication not working correctly")
        print(
            f"   Expected: [False, False, True], Got: [{is_dup_1}, {is_dup_2}, {is_dup_3}]"
        )
        return False


async def test_non_current_player_blocking():
    """Test that non-current players are still blocked appropriately"""
    print("\\n🧪 Testing non-current player blocking...")

    # Create test setup
    players = [Player("Bot 4", is_bot=True)]
    game = Game(players)

    bot_manager = BotManager()
    bot_manager.register_game("test_room2", game)
    handler = bot_manager.active_games["test_room2"]

    # Test scenario: Bot 4 is NOT current player
    print(
        "\\n🎯 Step 1: Bot 4 triggered but NOT current player (should be allowed first time)..."
    )

    context1 = {
        "phase": "turn",
        "turn_number": 1,
        "current_player": "Bot 3",  # Different from Bot 4
        "required_count": 1,
        "trigger_source": "phase_change",
    }

    is_dup_1 = handler._is_duplicate_action("Bot 4", "play_pieces", context1)
    print(f"   First trigger: duplicate = {is_dup_1}")

    print(
        "\\n🎯 Step 2: Bot 4 triggered again (should be blocked - not current player)..."
    )

    context2 = {
        "phase": "turn",
        "turn_number": 1,
        "current_player": "Bot 3",  # Still not Bot 4
        "required_count": 1,
        "trigger_source": "player_played",  # Different source but not current player
    }

    is_dup_2 = handler._is_duplicate_action("Bot 4", "play_pieces", context2)
    print(f"   Second trigger: duplicate = {is_dup_2}")

    if not is_dup_1 and is_dup_2:
        print("\\n✅ SUCCESS: Non-current player blocking working correctly!")
        print("   • First trigger allowed")
        print("   • Subsequent triggers blocked for non-current player")
        return True
    else:
        print(f"\\n❌ FAILURE: Non-current player blocking not working")
        print(f"   Expected: [False, True], Got: [{is_dup_1}, {is_dup_2}]")
        return False


async def main():
    """Run refined deduplication tests"""
    try:
        print("🚀 Testing refined deduplication logic...\\n")

        test_results = []

        # Test 1: Legitimate sequential triggers
        result1 = await test_legitimate_sequential_triggers()
        test_results.append(("Legitimate Sequential Triggers", result1))

        # Test 2: Non-current player blocking
        result2 = await test_non_current_player_blocking()
        test_results.append(("Non-Current Player Blocking", result2))

        # Summary
        print("\\n" + "=" * 60)
        print("🏁 REFINED DEDUPLICATION TEST RESULTS:")
        print("=" * 60)

        all_passed = True
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {test_name:<35} {status}")
            if not passed:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print("🎉 ALL TESTS PASSED - Refined deduplication is working correctly!")
            print("\\n📋 IMPROVEMENTS MADE:")
            print("   • Added trigger source to action hash generation")
            print("   • Allow different trigger sources for current player")
            print("   • Block rapid same-source triggers (< 0.5s)")
            print("   • Maintain original blocking for non-current players")
            print("   • Bot 3 should now be able to play after Bot 2!")
            sys.exit(0)
        else:
            print("💥 SOME TESTS FAILED - Refined deduplication needs more work")
            sys.exit(1)

    except Exception as e:
        print(f"\\n💥 Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
