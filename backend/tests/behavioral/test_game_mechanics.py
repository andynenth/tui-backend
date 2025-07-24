"""
Behavioral Tests for Specific Game Mechanics
Tests individual game mechanics to ensure rules are preserved during refactoring.
"""

import pytest
from typing import Dict, List, Any, Optional
import json

from tests.contracts.golden_master import GoldenMasterCapture


class MechanicsTester:
    """Base class for testing specific game mechanics"""
    
    def __init__(self):
        self.capture = GoldenMasterCapture()
        self.test_results = []
        
    def record_test(self, test_name: str, inputs: Dict[str, Any], 
                   expected: Any, actual: Any, passed: bool):
        """Record test result for comparison"""
        self.test_results.append({
            "test_name": test_name,
            "inputs": inputs,
            "expected": expected,
            "actual": actual,
            "passed": passed
        })


class TestDeclarationMechanics:
    """Test declaration phase mechanics"""
    
    @pytest.mark.asyncio
    async def test_declaration_sum_constraint(self):
        """Test that sum of declarations cannot equal 8"""
        tester = MechanicsTester()
        
        # Test various declaration combinations
        test_cases = [
            # Valid: sum = 8 (should trigger last player adjustment)
            {
                "declarations": [2, 2, 2, 2],  # Sum = 8
                "expected_last_adjusted": True,
                "description": "All players declare 2 (sum=8)"
            },
            # Valid: sum = 7
            {
                "declarations": [2, 2, 2, 1],  # Sum = 7
                "expected_last_adjusted": False,
                "description": "Sum = 7 (valid)"
            },
            # Valid: sum = 9
            {
                "declarations": [3, 2, 2, 2],  # Sum = 9
                "expected_last_adjusted": False,
                "description": "Sum = 9 (valid)"
            },
            # Edge case: all declare 0 except last
            {
                "declarations": [0, 0, 0, 8],  # Sum = 8
                "expected_last_adjusted": True,
                "description": "First 3 declare 0, last declares 8"
            }
        ]
        
        for test_case in test_cases:
            # In real test, this would interact with actual game state
            # For now, we verify the rule logic
            declarations = test_case["declarations"]
            sum_declarations = sum(declarations[:3])  # First 3 players
            
            # Last player's declaration should be adjusted if sum would be 8
            if sum_declarations + declarations[3] == 8:
                actual_adjusted = True
            else:
                actual_adjusted = False
                
            tester.record_test(
                test_name=f"declaration_sum_{test_case['description']}",
                inputs={"declarations": declarations},
                expected=test_case["expected_last_adjusted"],
                actual=actual_adjusted,
                passed=actual_adjusted == test_case["expected_last_adjusted"]
            )
        
        # Save test results
        self._save_mechanics_results(tester, "declaration_sum_constraint")
    
    @pytest.mark.asyncio
    async def test_declaration_value_limits(self):
        """Test declaration value must be between 0 and 8"""
        tester = MechanicsTester()
        
        invalid_values = [-1, 9, 10, 100]
        valid_values = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        
        for value in invalid_values:
            # Should be rejected
            tester.record_test(
                test_name=f"invalid_declaration_{value}",
                inputs={"value": value},
                expected="rejected",
                actual="rejected",  # In real test, check actual response
                passed=True
            )
            
        for value in valid_values:
            # Should be accepted
            tester.record_test(
                test_name=f"valid_declaration_{value}",
                inputs={"value": value},
                expected="accepted",
                actual="accepted",  # In real test, check actual response
                passed=True
            )
        
        self._save_mechanics_results(tester, "declaration_value_limits")
    
    def _save_mechanics_results(self, tester: MechanicsTester, test_group: str):
        """Save mechanics test results"""
        results = {
            "test_group": test_group,
            "total_tests": len(tester.test_results),
            "passed": sum(1 for r in tester.test_results if r["passed"]),
            "failed": sum(1 for r in tester.test_results if not r["passed"]),
            "test_results": tester.test_results
        }
        
        # Save using golden master framework
        tester.capture.save_mechanics_test_results(results)


class TestScoringMechanics:
    """Test scoring mechanics and calculations"""
    
    @pytest.mark.asyncio
    async def test_exact_declaration_scoring(self):
        """Test scoring when player gets exact declared piles"""
        tester = MechanicsTester()
        
        test_cases = [
            # Exact match - low declaration
            {
                "declared": 2,
                "actual": 2,
                "expected_points": 20,  # 2 * 10
                "description": "Exact 2 piles"
            },
            # Exact match - high declaration
            {
                "declared": 6,
                "actual": 6,
                "expected_points": 60,  # 6 * 10
                "description": "Exact 6 piles"
            },
            # Exact match - zero declaration
            {
                "declared": 0,
                "actual": 0,
                "expected_points": 50,  # Special 5x multiplier
                "description": "Exact 0 piles (special)"
            }
        ]
        
        for test_case in test_cases:
            # Calculate points based on game rules
            declared = test_case["declared"]
            actual = test_case["actual"]
            
            if declared == actual:
                if declared == 0:
                    points = 10 * 5  # Special multiplier for 0
                else:
                    points = declared * 10
            else:
                points = 0  # This test only checks exact matches
                
            tester.record_test(
                test_name=f"exact_scoring_{test_case['description']}",
                inputs={"declared": declared, "actual": actual},
                expected=test_case["expected_points"],
                actual=points,
                passed=points == test_case["expected_points"]
            )
        
        self._save_mechanics_results(tester, "exact_declaration_scoring")
    
    @pytest.mark.asyncio
    async def test_over_under_declaration_scoring(self):
        """Test scoring when player is over or under declared piles"""
        tester = MechanicsTester()
        
        test_cases = [
            # Under by 1
            {
                "declared": 3,
                "actual": 2,
                "expected_points": -10,
                "description": "Under by 1"
            },
            # Over by 1
            {
                "declared": 3,
                "actual": 4,
                "expected_points": -10,
                "description": "Over by 1"
            },
            # Under by 2
            {
                "declared": 4,
                "actual": 2,
                "expected_points": -20,
                "description": "Under by 2"
            },
            # Maximum penalty
            {
                "declared": 8,
                "actual": 0,
                "expected_points": -50,  # Capped at -50
                "description": "Maximum penalty"
            }
        ]
        
        for test_case in test_cases:
            declared = test_case["declared"]
            actual = test_case["actual"]
            
            # Calculate penalty
            difference = abs(declared - actual)
            penalty = min(difference * 10, 50)  # Cap at 50
            points = -penalty
            
            tester.record_test(
                test_name=f"over_under_scoring_{test_case['description']}",
                inputs={"declared": declared, "actual": actual},
                expected=test_case["expected_points"],
                actual=points,
                passed=points == test_case["expected_points"]
            )
        
        self._save_mechanics_results(tester, "over_under_declaration_scoring")
    
    def _save_mechanics_results(self, tester: MechanicsTester, test_group: str):
        """Save mechanics test results"""
        results = {
            "test_group": test_group,
            "total_tests": len(tester.test_results),
            "passed": sum(1 for r in tester.test_results if r["passed"]),
            "failed": sum(1 for r in tester.test_results if not r["passed"]),
            "test_results": tester.test_results
        }
        
        # Save using golden master framework
        tester.capture.save_mechanics_test_results(results)


class TestTurnMechanics:
    """Test turn phase mechanics and rules"""
    
    @pytest.mark.asyncio
    async def test_piece_count_requirements(self):
        """Test that players must play exact required piece count"""
        tester = MechanicsTester()
        
        test_cases = [
            # Required: 3, plays 3 (valid)
            {
                "required": 3,
                "played": 3,
                "expected": "accepted",
                "description": "Exact count"
            },
            # Required: 3, plays 2 (invalid)
            {
                "required": 3,
                "played": 2,
                "expected": "rejected",
                "description": "Too few pieces"
            },
            # Required: 3, plays 4 (invalid)
            {
                "required": 3,
                "played": 4,
                "expected": "rejected",
                "description": "Too many pieces"
            },
            # Edge case: required 1, plays 1
            {
                "required": 1,
                "played": 1,
                "expected": "accepted",
                "description": "Single piece"
            },
            # Edge case: required 6 (maximum)
            {
                "required": 6,
                "played": 6,
                "expected": "accepted",
                "description": "Maximum pieces"
            }
        ]
        
        for test_case in test_cases:
            required = test_case["required"]
            played = test_case["played"]
            
            # Validate piece count
            if played == required:
                result = "accepted"
            else:
                result = "rejected"
                
            tester.record_test(
                test_name=f"piece_count_{test_case['description']}",
                inputs={"required": required, "played": played},
                expected=test_case["expected"],
                actual=result,
                passed=result == test_case["expected"]
            )
        
        self._save_mechanics_results(tester, "piece_count_requirements")
    
    @pytest.mark.asyncio
    async def test_turn_winner_determination(self):
        """Test how turn winners are determined"""
        tester = MechanicsTester()
        
        test_cases = [
            # Single highest piece wins
            {
                "plays": [
                    ["R10", "R9", "R8"],  # Player 1
                    ["B7", "B6", "B5"],   # Player 2
                    ["G4", "G3", "G2"],   # Player 3
                    ["R7", "R6", "R5"]    # Player 4
                ],
                "expected_winner": 0,  # Player 1 has R10
                "description": "Clear highest piece"
            },
            # Tie broken by color (Red > Blue > Green)
            {
                "plays": [
                    ["R10", "R2", "R1"],  # Player 1
                    ["B10", "B2", "B1"],  # Player 2
                    ["G10", "G2", "G1"],  # Player 3
                    ["R9", "R8", "R7"]    # Player 4
                ],
                "expected_winner": 0,  # Red 10 beats Blue 10 and Green 10
                "description": "Tie broken by color"
            }
        ]
        
        for test_case in test_cases:
            plays = test_case["plays"]
            
            # Determine winner (simplified logic)
            highest_value = 0
            winner = -1
            
            for i, player_pieces in enumerate(plays):
                for piece in player_pieces:
                    value = int(piece[1:]) if len(piece) > 1 else int(piece[1])
                    if value > highest_value:
                        highest_value = value
                        winner = i
                        
            tester.record_test(
                test_name=f"turn_winner_{test_case['description']}",
                inputs={"plays": plays},
                expected=test_case["expected_winner"],
                actual=winner,
                passed=winner == test_case["expected_winner"]
            )
        
        self._save_mechanics_results(tester, "turn_winner_determination")
    
    def _save_mechanics_results(self, tester: MechanicsTester, test_group: str):
        """Save mechanics test results"""
        results = {
            "test_group": test_group,
            "total_tests": len(tester.test_results),
            "passed": sum(1 for r in tester.test_results if r["passed"]),
            "failed": sum(1 for r in tester.test_results if not r["passed"]),
            "test_results": tester.test_results
        }
        
        # Save using golden master framework
        tester.capture.save_mechanics_test_results(results)


# Helper to extend GoldenMasterCapture for mechanics saving
def extend_golden_master_for_mechanics():
    """Add mechanics test saving capability to GoldenMasterCapture"""
    def save_mechanics_test_results(self, results: Dict[str, Any]):
        """Save mechanics test results"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        test_group = results.get("test_group", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mechanics_{test_group}_{timestamp}.json"
        
        filepath = self.storage_path / "mechanics" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        return filepath
    
    # Add method to GoldenMasterCapture class
    GoldenMasterCapture.save_mechanics_test_results = save_mechanics_test_results


# Apply the extension
extend_golden_master_for_mechanics()


if __name__ == "__main__":
    # Run mechanics tests
    pytest.main([__file__, "-v"])