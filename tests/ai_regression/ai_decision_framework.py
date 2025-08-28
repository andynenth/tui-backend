#!/usr/bin/env python3
"""Reusable AI decision testing framework"""

import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict

# Add backend to path - go up two directories to project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, form_execution_plan,
    calculate_urgency, get_overcapture_constraints
)
from backend.engine.ai import find_all_valid_combos


class AIDecisionTester:
    """Reusable tester for AI decision-making scenarios"""
    
    def __init__(self):
        self.scenarios = []
    
    def create_hand_from_specs(self, piece_specs: List[Tuple[str, int]]) -> List[Piece]:
        """
        Create a hand from piece specifications.
        
        Args:
            piece_specs: List of (piece_type, count) tuples
                        e.g., [("ADVISOR_RED", 2), ("SOLDIER_BLACK", 3)]
        
        Returns:
            List of Piece objects
        """
        hand = []
        for piece_type, count in piece_specs:
            for _ in range(count):
                hand.append(Piece(piece_type))
        return hand
    
    def create_context(self, bot_name: str, hand: List[Piece], 
                      declared: int, captured: int, required_pieces: int,
                      turn_number: int = 1, is_starter: bool = False,
                      player_states: Dict = None) -> TurnPlayContext:
        """Create a game context for testing"""
        if player_states is None:
            player_states = {
                "Player1": {"captured": 0, "declared": 7},
                "Player2": {"captured": 0, "declared": 0},
                "Player3": {"captured": 0, "declared": 0},
                "Player4": {"captured": 0, "declared": 0}
            }
        
        return TurnPlayContext(
            my_name=bot_name,
            my_hand=hand,
            my_captured=captured,
            my_declared=declared,
            required_piece_count=required_pieces,
            turn_number=turn_number,
            pieces_per_player=len(hand),
            am_i_starter=is_starter,
            current_plays=[],
            revealed_pieces=[],
            player_states=player_states
        )
    
    def analyze_decision(self, context: TurnPlayContext, 
                        show_plan_details: bool = True,
                        show_urgency: bool = True) -> Dict:
        """Analyze AI decision for given context"""
        # Get urgency and constraints
        urgency = calculate_urgency(context)
        constraints = get_overcapture_constraints(context)
        
        # Get valid combos and form plan
        valid_combos = find_all_valid_combos(context.my_hand)
        plan = form_execution_plan(context.my_hand, context, valid_combos)
        
        # Get AI's choice
        chosen_pieces = choose_strategic_play(context.my_hand, context)
        
        # Compile results
        results = {
            "bot_name": context.my_name,
            "hand_size": len(context.my_hand),
            "declared": context.my_declared,
            "captured": context.my_captured,
            "target_remaining": context.my_declared - context.my_captured,
            "urgency": urgency,
            "risk_level": constraints.risk_level,
            "assigned_combos": len(plan['assigned_combos']),
            "burden_pieces": len(plan['burden_pieces']),
            "chosen_play": chosen_pieces,
            "plan": plan
        }
        
        # Display analysis
        print(f"\n{'='*60}")
        print(f"ANALYZING: {context.my_name}")
        print(f"{'='*60}")
        
        print(f"\nGame State:")
        print(f"  - Hand size: {results['hand_size']} pieces")
        print(f"  - Declared: {results['declared']}, Captured: {results['captured']}")
        print(f"  - Target remaining: {results['target_remaining']} piles")
        
        if show_urgency:
            print(f"\nStrategic Assessment:")
            print(f"  - Urgency: {results['urgency']}")
            print(f"  - Risk level: {results['risk_level']}")
        
        if show_plan_details:
            print(f"\nPlan Formation:")
            print(f"  - Assigned combos: {results['assigned_combos']}")
            if plan['assigned_combos']:
                for combo_type, pieces in plan['assigned_combos']:
                    piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
                    print(f"    - {combo_type}: {piece_str}")
            
            print(f"  - Burden pieces: {results['burden_pieces']}")
            if results['burden_pieces'] <= 10:  # Don't spam if too many
                for p in plan['burden_pieces']:
                    print(f"    - {p.kind}: {p.point}")
        
        print(f"\nChosen Play:")
        if chosen_pieces:
            play_str = "+".join([f"{p.kind}({p.point})" for p in chosen_pieces])
            total = sum(p.point for p in chosen_pieces)
            print(f"  {play_str} = {total} points")
        else:
            print(f"  No play chosen!")
        
        return results
    
    def add_scenario(self, name: str, description: str, **kwargs):
        """Add a test scenario"""
        self.scenarios.append({
            "name": name,
            "description": description,
            **kwargs
        })
    
    def run_all_scenarios(self):
        """Run all added scenarios"""
        print(f"\n{'#'*60}")
        print(f"# Running {len(self.scenarios)} Test Scenarios")
        print(f"{'#'*60}")
        
        for scenario in self.scenarios:
            print(f"\n\n{'*'*60}")
            print(f"Scenario: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            print(f"{'*'*60}")
            
            # Create hand and context from scenario
            hand = self.create_hand_from_specs(scenario['hand_specs'])
            context = self.create_context(
                bot_name=scenario.get('bot_name', 'Test Bot'),
                hand=hand,
                declared=scenario['declared'],
                captured=scenario['captured'],
                required_pieces=scenario['required_pieces'],
                turn_number=scenario.get('turn_number', 1),
                is_starter=scenario.get('is_starter', False),
                player_states=scenario.get('player_states', None)
            )
            
            # Analyze decision
            self.analyze_decision(
                context,
                show_plan_details=scenario.get('show_plan_details', True),
                show_urgency=scenario.get('show_urgency', True)
            )


def main():
    """Example usage with various scenarios"""
    tester = AIDecisionTester()
    
    # Scenario 1: Bot declaring 0 with strong combo (original Bot 3 case)
    tester.add_scenario(
        name="Zero Declaration with Combo",
        description="Bot declares 0 but has ADVISOR_RED pair - should dispose them",
        bot_name="Bot 3",
        hand_specs=[
            ("ADVISOR_RED", 2),
            ("ADVISOR_BLACK", 1),
            ("CHARIOT_RED", 1),
            ("CHARIOT_BLACK", 1),
            ("SOLDIER_RED", 1),
            ("SOLDIER_BLACK", 2)
        ],
        declared=0,
        captured=0,
        required_pieces=4,
        turn_number=1
    )
    
    # Scenario 2: Bot at target with singles only
    tester.add_scenario(
        name="At Target Playing Singles",
        description="Bot at target (3/3) needs to play 1 piece - should play weakest",
        bot_name="Lucky Bot",
        hand_specs=[
            ("GENERAL_RED", 1),
            ("ELEPHANT_RED", 1),
            ("SOLDIER_BLACK", 2)
        ],
        declared=3,
        captured=3,
        required_pieces=1,
        turn_number=3
    )
    
    # Scenario 3: Critical urgency needing wins
    tester.add_scenario(
        name="Critical Urgency",
        description="Bot needs 2 wins with only 2 turns left",
        bot_name="Desperate Bot",
        hand_specs=[
            ("ADVISOR_RED", 2),
            ("HORSE_RED", 2),
            ("CANNON_BLACK", 2)
        ],
        declared=4,
        captured=2,
        required_pieces=3,
        turn_number=3
    )
    
    # Scenario 4: Bot with multiple combos
    tester.add_scenario(
        name="Multiple Combo Options",
        description="Bot has both pairs and straights available",
        bot_name="Combo Master",
        hand_specs=[
            ("SOLDIER_BLACK", 2),  # Pair
            ("SOLDIER_RED", 1),
            ("CANNON_BLACK", 1),
            ("CANNON_RED", 1),  # Potential straight 2-3-4
            ("HORSE_BLACK", 2),  # Another pair
            ("ELEPHANT_RED", 1)
        ],
        declared=2,
        captured=0,
        required_pieces=3,
        turn_number=1
    )
    
    # Run all scenarios
    tester.run_all_scenarios()


if __name__ == "__main__":
    main()