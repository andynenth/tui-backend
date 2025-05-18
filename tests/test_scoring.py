import unittest
from dataclasses import dataclass
from engine.scoring import calculate_round_scores

@dataclass
class MockPlayer:
    name: str
    declared: int = 0
    score: int = 0

class TestScoreMultipleRounds(unittest.TestCase):
    def test_simulate_4_rounds(self):
        players = [
            MockPlayer("P1"),
            MockPlayer("P2"),
            MockPlayer("P3"),
            MockPlayer("P4")
        ]

        # Round 1 (×1)
        for i, (d, a) in enumerate([(5, 1), (1, 0), (1, 3), (3, 4)]):
            players[i].declared = d
        pile_counts = {"P1": 1, "P2": 0, "P3": 3, "P4": 4}
        calculate_round_scores(players, pile_counts, redeal_multiplier=1)

        # Round 2 (×2)
        for i, (d, a) in enumerate([(1, 0), (7, 7), (0, 0), (3, 1)]):
            players[i].declared = d
        pile_counts = {"P1": 0, "P2": 7, "P3": 0, "P4": 1}
        calculate_round_scores(players, pile_counts, redeal_multiplier=2)

        # Round 3 (×2)
        for i, (d, a) in enumerate([(1, 1), (1, 1), (5, 5), (0, 1)]):
            players[i].declared = d
        pile_counts = {"P1": 1, "P2": 1, "P3": 5, "P4": 1}
        calculate_round_scores(players, pile_counts, redeal_multiplier=2)

        # Round 4 (×2)
        for i, (d, a) in enumerate([(2, 2), (2, 0), (2, 3), (2, 2)]):
            players[i].declared = d
        pile_counts = {"P1": 2, "P2": 0, "P3": 3, "P4": 2}
        calculate_round_scores(players, pile_counts, redeal_multiplier=2)

        # Final score assertions
        self.assertEqual(players[0].score, 14)
        self.assertEqual(players[1].score, 35)
        self.assertEqual(players[2].score, 24)
        self.assertEqual(players[3].score, -7)

if __name__ == "__main__":
    unittest.main()
