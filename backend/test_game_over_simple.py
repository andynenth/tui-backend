# backend/test_game_over_simple.py

"""
Simple Game Over Transition Test
Tests that the game properly transitions to GAME_OVER phase after finding a winner
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state_machine.core import GamePhase
from engine.state_machine.game_state_machine import GameStateMachine
from engine.win_conditions import WinConditionType


class MockPlayer:
    """Mock player for testing"""

    def __init__(self, name, score=0, is_bot=False, captured_piles=0):
        self.name = name
        self.score = score
        self.is_bot = is_bot
        self.hand = []
        self.captured_piles = captured_piles

    def __str__(self):
        return self.name


class MockGameWithWinner:
    """Mock game that simulates a completed game with a winner"""

    def __init__(self):
        # Create players where Andy will win after scoring
        self.players = [
            MockPlayer(
                "Andy", 42, False, 4
            ),  # Andy: 42 + 9 (perfect 4-pile declaration) = 51
            MockPlayer("Bot 2", 38, True, 4),  # Bot 2: 38 - 3 (declared 1, got 4) = 35
            MockPlayer("Bot 3", 31, True, 0),  # Bot 3: 31 - 1 (declared 1, got 0) = 30
            MockPlayer("Bot 4", 26, True, 0),  # Bot 4: 26 - 1 (declared 1, got 0) = 25
        ]

        # Game configuration
        self.round_number = 13
        self.max_score = 50
        self.max_rounds = 20
        self.win_condition_type = WinConditionType.FIRST_TO_REACH_50

        # Timing
        self.start_time = 1000000000
        self.end_time = None

        # Round data for scoring
        self.current_order = [p.name for p in self.players]
        self.player_declarations = {
            "Andy": 4,  # Perfect declaration
            "Bot 2": 1,  # Underdeclared
            "Bot 3": 1,  # Exact but no piles
            "Bot 4": 1,  # Exact but no piles
        }

    def get_player_order_from(self, starter):
        """Get player order starting from given player"""
        names = [p.name for p in self.players]
        if starter in names:
            start_idx = names.index(starter)
            return self.players[start_idx:] + self.players[:start_idx]
        return self.players


async def test_game_over_transition():
    """Test that a winning game transitions to GAME_OVER phase"""
    print("🧪 Testing Game Over Transition...")

    # Create mock game with winner
    mock_game = MockGameWithWinner()
    mock_broadcast = AsyncMock()

    # Create state machine
    sm = GameStateMachine(mock_game, mock_broadcast)
    sm.room_id = "TEST_ROOM"

    try:
        # Start in scoring phase (final round)
        print("📋 Starting in SCORING phase...")
        await sm.start(GamePhase.SCORING)

        # Verify we start in scoring
        assert sm.current_phase == GamePhase.SCORING
        print(f"✅ Started in phase: {sm.current_phase}")

        # Wait for scoring delay and transition
        print("⏰ Waiting for scoring delay (7 seconds)...")
        await asyncio.sleep(8)  # Wait for 7-second delay plus buffer

        # Verify transition to GAME_OVER
        print(f"📊 Current phase after delay: {sm.current_phase}")

        if sm.current_phase == GamePhase.GAME_OVER:
            print("🎉 SUCCESS: Game transitioned to GAME_OVER phase!")

            # Verify game over state has correct data
            phase_data = sm.current_state.phase_data

            if "winners" in phase_data and "Andy" in phase_data["winners"]:
                print("🏆 SUCCESS: Andy identified as winner!")
            else:
                print(
                    f"❌ WARNING: Winner data incorrect: {phase_data.get('winners', 'No winners')}"
                )

            if "final_rankings" in phase_data:
                rankings = phase_data["final_rankings"]
                first_place = rankings[0] if rankings else None
                if first_place and first_place["name"] == "Andy":
                    print(
                        f"🥇 SUCCESS: Andy in first place with {first_place['score']} points!"
                    )
                else:
                    print(f"❌ WARNING: Rankings incorrect: {rankings}")

            return True
        else:
            print(f"❌ FAILED: Expected GAME_OVER, got {sm.current_phase}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    finally:
        if sm.is_running:
            await sm.stop()


async def main():
    """Run the test"""
    print("🎮 Game Over Transition Test")
    print("=" * 50)

    success = await test_game_over_transition()

    print("=" * 50)
    if success:
        print("✅ TEST PASSED: Game over transition works correctly!")
    else:
        print("❌ TEST FAILED: Game over transition needs fixing!")

    return success


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
