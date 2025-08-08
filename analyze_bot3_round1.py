#!/usr/bin/env python3
"""
Analyze Bot 3's behavior in Round 1 from the actual game logs.

This script examines the game events to understand why Bot 3
didn't avoid overcapture when it should have.
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def analyze_bot3_behavior():
    """Analyze Bot 3's plays in Round 1 from game_play_history_rounds_1_8.md"""
    
    print("\n" + "="*60)
    print("ANALYSIS: Bot 3 Round 1 Overcapture Issue")
    print("="*60)
    
    # Based on the play history, let's trace Bot 3's decisions
    print("\nBot 3 declared: 1 pile")
    print("\nTurn-by-turn analysis:")
    
    # Turn 1
    print("\n--- TURN 1 ---")
    print("Bot 3 hand at start: Unknown (not in logs)")
    print("Bot 3 plays: SOLDIER_BLACK(1), HORSE_BLACK(5), HORSE_BLACK(5)")
    print("Result: Bot 2 wins")
    print("Bot 3 captured so far: 0")
    
    # Turn 2
    print("\n--- TURN 2 ---")
    print("Bot 3 should be at: captured=0, declared=1")
    print("Bot 3 plays: GENERAL_BLACK(13)")
    print("Result: Bot 3 WINS! Gets 1 pile")
    print("Bot 3 captured so far: 1")
    print("✅ Now Bot 3 is AT TARGET (1/1)")
    
    # Turn 3 - CRITICAL
    print("\n--- TURN 3 (CRITICAL) ---")
    print("Bot 3 should be at: captured=1, declared=1")
    print("⚠️ EXPECTED: Bot 3 should play weakest piece to avoid winning")
    print("ACTUAL: Bot 3 plays HORSE_RED(6)")
    print("Result: Bot 3 WINS AGAIN! Gets 1 more pile")
    print("Bot 3 captured so far: 2 (OVERCAPTURED!)")
    
    print("\n🚨 BUG CONFIRMED: Bot 3 didn't avoid overcapture when at target!")
    
    # Turn 4
    print("\n--- TURN 4 ---")
    print("Bot 3 at: captured=2, declared=1 (already overcaptured)")
    print("Bot 3 plays: CHARIOT_BLACK(7)")
    print("Result: Alexanderium wins")
    
    # Turn 5
    print("\n--- TURN 5 ---")
    print("Bot 3 plays: ELEPHANT_BLACK(9)")
    print("Result: Bot 3 WINS AGAIN! (3rd win)")
    print("Bot 3 captured so far: 3")
    
    # Turn 6
    print("\n--- TURN 6 ---")
    print("Bot 3 plays: ELEPHANT_RED(10)")
    print("Result: Bot 3 WINS AGAIN! (4th win)")
    print("Final: Bot 3 captured 4 piles (declared 1)")
    
    print("\n" + "="*60)
    print("HYPOTHESIS")
    print("="*60)
    
    print("\nPossible reasons for the bug:")
    print("1. The strategic AI isn't being used (falling back to basic AI)")
    print("2. The pile_counts data is stale or incorrect")
    print("3. The overcapture condition (captured >= declared) needs to be fixed")
    print("4. There's an error in the strategic AI that causes fallback")
    
    print("\nThe debug logs we added should reveal which case it is!")


def check_hand_possibilities():
    """Check what pieces Bot 3 might have had in Turn 3"""
    print("\n" + "="*60)
    print("HAND ANALYSIS")
    print("="*60)
    
    print("\nBot 3's known plays:")
    print("Turn 1: SOLDIER_BLACK(1), HORSE_BLACK(5), HORSE_BLACK(5) - 3 pieces")
    print("Turn 2: GENERAL_BLACK(13) - 1 piece")
    print("Turn 3: HORSE_RED(6) - 1 piece")
    print("Turn 4: CHARIOT_BLACK(7) - 1 piece")  
    print("Turn 5: ELEPHANT_BLACK(9) - 1 piece")
    print("Turn 6: ELEPHANT_RED(10) - 1 piece")
    print("Total: 8 pieces (full starting hand)")
    
    print("\nAt Turn 3, Bot 3 had played 4 pieces, so had 4 left:")
    print("- HORSE_RED(6) - played")
    print("- CHARIOT_BLACK(7)")
    print("- ELEPHANT_BLACK(9)")
    print("- ELEPHANT_RED(10)")
    
    print("\n⚠️ Bot 3 had NO pieces weaker than HORSE_RED(6)!")
    print("All remaining pieces were 6+ points")
    print("This might explain why it couldn't play weaker!")


if __name__ == "__main__":
    analyze_bot3_behavior()
    check_hand_possibilities()
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("\nBot 3 may have had no weak pieces left by Turn 3!")
    print("But the strategic AI should still TRY to play the weakest available.")
    print("The debug logs will show if it's trying to avoid overcapture.")