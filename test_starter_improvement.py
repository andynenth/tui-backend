#!/usr/bin/env python3
"""
Test script to verify starter strategy improvements.
Tests that starters now prioritize combos over random singles.
"""

import sys
sys.path.append('backend')

from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, get_optimal_piece_count_for_starter,
    get_overcapture_constraints, choose_strategic_play
)
from backend.engine.piece import Piece


def create_test_pieces():
    """Create some test pieces for scenarios."""
    return {
        'general_red': Piece('GENERAL_RED'),
        'general_black': Piece('GENERAL_BLACK'),
        'advisor_red': Piece('ADVISOR_RED'),
        'advisor_black': Piece('ADVISOR_BLACK'),
        'elephant_red': Piece('ELEPHANT_RED'),
        'elephant_black': Piece('ELEPHANT_BLACK'),
        'horse_red': Piece('HORSE_RED'),
        'horse_black': Piece('HORSE_BLACK'),
        'chariot_red': Piece('CHARIOT_RED'),
        'chariot_black': Piece('CHARIOT_BLACK'),
        'cannon_red': Piece('CANNON_RED'),
        'cannon_black': Piece('CANNON_BLACK'),
        'soldier_red': Piece('SOLDIER_RED'),
        'soldier_black': Piece('SOLDIER_BLACK'),
    }


def test_scenario_1_combo_available():
    """Test that starter chooses combo when available."""
    print("\n=== Test 1: Starter with Combo Available ===")
    
    pieces = create_test_pieces()
    hand = [
        pieces['general_red'],    # 14 - opener
        pieces['advisor_black'],   # 11 - opener
        pieces['horse_red'],       # 6
        pieces['horse_black'],     # 5  - PAIR combo worth 11
        pieces['cannon_red'],      # 4
        pieces['soldier_black'],   # 1
    ]
    
    # Create context - starter setting piece count
    context = TurnPlayContext(
        my_name="Bot_1",
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more piles
        required_piece_count=None,  # Starter sets this
        turn_number=3,
        pieces_per_player=6,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot_1": {"captured": 1, "declared": 3},
            "Bot_2": {"captured": 0, "declared": 2},
            "Bot_3": {"captured": 1, "declared": 2},
            "Bot_4": {"captured": 0, "declared": 1}
        }
    )
    
    # Create plan with combo
    plan = StrategicPlan(
        target_remaining=2,
        valid_combos=[
            ("PAIR", [pieces['horse_red'], pieces['horse_black']]),
            ("SINGLE", [pieces['general_red']]),
            ("SINGLE", [pieces['advisor_black']]),
        ],
        opener_pieces=[pieces['general_red'], pieces['advisor_black']],
        urgency_level="medium",
        assigned_openers=[pieces['general_red'], pieces['advisor_black']],
        assigned_combos=[("PAIR", [pieces['horse_red'], pieces['horse_black']])],
        reserve_pieces=[pieces['soldier_black']],
        burden_pieces=[pieces['cannon_red']],
        main_plan_size=4,  # 2 openers + 1 combo (2 pieces)
        plan_impossible=False
    )
    
    # Get constraints
    constraints = get_overcapture_constraints(context)
    
    # Test new function
    piece_count, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, hand
    )
    
    print(f"Piece count chosen: {piece_count}")
    if combo_to_play:
        print(f"Combo selected: PAIR of {[p.name for p in combo_to_play]}")
    else:
        print("No combo pre-selected")
    
    # Verify it chose the combo
    assert piece_count == 2, f"Expected 2 pieces for PAIR, got {piece_count}"
    assert combo_to_play is not None, "Expected PAIR combo to be selected"
    assert len(combo_to_play) == 2, "Expected 2-piece combo"
    assert all(p.name == 'HORSE' for p in combo_to_play), "Expected HORSE pair"
    
    print("✅ Test 1 PASSED: Starter correctly chose combo over singles")


def test_scenario_2_critical_urgency():
    """Test that critical urgency finds strongest combo."""
    print("\n=== Test 2: Critical Urgency ===")
    
    pieces = create_test_pieces()
    hand = [
        pieces['elephant_red'],    # 10
        pieces['elephant_black'],  # 9  - PAIR worth 19
        pieces['chariot_red'],     # 8
        pieces['chariot_black'],   # 7  - PAIR worth 15
        pieces['horse_red'],       # 6
        pieces['horse_black'],     # 5  - PAIR worth 11
    ]
    
    context = TurnPlayContext(
        my_name="Bot_2",
        my_hand=hand,
        my_captured=0,
        my_declared=3,  # Need 3 piles
        required_piece_count=None,
        turn_number=6,  # Late game
        pieces_per_player=3,  # Only 3 turns left
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot_1": {"captured": 2, "declared": 2},
            "Bot_2": {"captured": 0, "declared": 3},
            "Bot_3": {"captured": 2, "declared": 2},
            "Bot_4": {"captured": 1, "declared": 1}
        }
    )
    
    plan = StrategicPlan(
        target_remaining=3,
        valid_combos=[
            ("PAIR", [pieces['elephant_red'], pieces['elephant_black']]),
            ("PAIR", [pieces['chariot_red'], pieces['chariot_black']]),
            ("PAIR", [pieces['horse_red'], pieces['horse_black']]),
        ],
        opener_pieces=[],
        urgency_level="critical",  # Must win every turn!
        assigned_openers=[],
        assigned_combos=[
            ("PAIR", [pieces['horse_red'], pieces['horse_black']]),  # Weakest assigned
        ],
        reserve_pieces=[],
        burden_pieces=[],
        main_plan_size=2,
        plan_impossible=False
    )
    
    constraints = get_overcapture_constraints(context)
    piece_count, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, hand
    )
    
    print(f"Piece count chosen: {piece_count}")
    if combo_to_play:
        total_value = sum(p.point for p in combo_to_play)
        print(f"Combo selected: {[f'{p.name}({p.point})' for p in combo_to_play]} = {total_value} pts")
    
    # Should choose strongest combo (ELEPHANT pair = 19)
    assert piece_count == 2, f"Expected 2 pieces for PAIR, got {piece_count}"
    assert combo_to_play is not None, "Expected combo to be selected"
    assert sum(p.point for p in combo_to_play) == 19, "Expected ELEPHANT pair (19 pts)"
    
    print("✅ Test 2 PASSED: Critical urgency chose strongest combo")


def test_scenario_3_no_combos():
    """Test strategic count selection when no combos available."""
    print("\n=== Test 3: No Combos Available ===")
    
    pieces = create_test_pieces()
    hand = [
        pieces['general_red'],     # 14 - opener
        pieces['advisor_black'],   # 12 - opener
        pieces['elephant_red'],    # 9  - opener (borderline)
        pieces['chariot_black'],   # 7
        pieces['cannon_red'],      # 3
        pieces['soldier_black'],   # 1
    ]
    
    context = TurnPlayContext(
        my_name="Bot_3",
        my_hand=hand,
        my_captured=1,
        my_declared=4,  # Need 3 more piles
        required_piece_count=None,
        turn_number=4,
        pieces_per_player=5,  # 5 turns left
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot_1": {"captured": 1, "declared": 2},
            "Bot_2": {"captured": 1, "declared": 2},
            "Bot_3": {"captured": 1, "declared": 4},
            "Bot_4": {"captured": 0, "declared": 2}
        }
    )
    
    plan = StrategicPlan(
        target_remaining=3,
        valid_combos=[],  # No combos!
        opener_pieces=[pieces['general_red'], pieces['advisor_black']],
        urgency_level="high",  # Need to win 60% of turns
        assigned_openers=[pieces['general_red'], pieces['advisor_black']],
        assigned_combos=[],  # No combos available
        reserve_pieces=[pieces['soldier_black']],
        burden_pieces=[pieces['cannon_red'], pieces['chariot_black']],
        main_plan_size=2,  # Just 2 openers
        plan_impossible=False
    )
    
    constraints = get_overcapture_constraints(context)
    piece_count, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, hand
    )
    
    print(f"Piece count chosen: {piece_count}")
    print(f"Combo selected: {combo_to_play}")
    
    # With high urgency and 2 openers, should choose 2
    assert piece_count == 2, f"Expected 2 pieces with high urgency, got {piece_count}"
    assert combo_to_play is None, "Expected no combo (singles play)"
    
    print("✅ Test 3 PASSED: High urgency with openers chose 2 pieces")


def test_scenario_4_at_target():
    """Test that bot at target always plays 1 piece."""
    print("\n=== Test 4: Already At Target ===")
    
    pieces = create_test_pieces()
    hand = [
        pieces['general_red'],
        pieces['advisor_black'],
        pieces['horse_red'],
        pieces['horse_black'],
    ]
    
    context = TurnPlayContext(
        my_name="Bot_4",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # Already at target!
        required_piece_count=None,
        turn_number=5,
        pieces_per_player=4,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot_1": {"captured": 2, "declared": 3},
            "Bot_2": {"captured": 1, "declared": 2},
            "Bot_3": {"captured": 1, "declared": 2},
            "Bot_4": {"captured": 2, "declared": 2}
        }
    )
    
    plan = StrategicPlan(
        target_remaining=0,  # At target
        valid_combos=[("PAIR", [pieces['horse_red'], pieces['horse_black']])],
        opener_pieces=[pieces['general_red'], pieces['advisor_black']],
        urgency_level="none",
        assigned_openers=[],  # No openers needed
        assigned_combos=[],   # No combos needed
        reserve_pieces=[],
        burden_pieces=hand,   # All burden now
        main_plan_size=0,
        plan_impossible=False
    )
    
    constraints = get_overcapture_constraints(context)
    piece_count, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, hand
    )
    
    print(f"Piece count chosen: {piece_count}")
    print(f"Combo selected: {combo_to_play}")
    
    # At target should always play 1
    assert piece_count == 1, f"Expected 1 piece at target, got {piece_count}"
    assert combo_to_play is None, "Expected no combo at target"
    
    print("✅ Test 4 PASSED: At target correctly chose 1 piece")


def main():
    """Run all tests."""
    print("Testing Starter Strategy Improvements...")
    print("=" * 50)
    
    test_scenario_1_combo_available()
    test_scenario_2_critical_urgency()
    test_scenario_3_no_combos()
    test_scenario_4_at_target()
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Starter strategy improvements working correctly.")
    print("\nKey improvements verified:")
    print("- ✅ Starters prioritize combos over random singles")
    print("- ✅ Critical urgency finds strongest combos")
    print("- ✅ Strategic piece count based on urgency")
    print("- ✅ Always minimize at target")


if __name__ == "__main__":
    main()