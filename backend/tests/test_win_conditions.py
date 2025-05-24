import unittest
from engine.win_conditions import is_game_over, get_winners, WinConditionType
from engine.player import Player

class DummyGame:
    def __init__(self, players, round_number=1, win_condition_type=WinConditionType.FIRST_TO_REACH_50):
        self.players = players
        self.round_number = round_number
        self.win_condition_type = win_condition_type
        self.max_score = 50
        self.max_rounds = 20

class TestWinConditions(unittest.TestCase):
    def test_first_to_50(self):
        p1 = Player("P1")
        p2 = Player("P2")
        p1.score = 51
        game = DummyGame([p1, p2])
        self.assertTrue(is_game_over(game))
        self.assertEqual(get_winners(game), [p1])

    def test_exactly_50(self):
        p1 = Player("P1")
        p2 = Player("P2")
        p2.score = 50
        game = DummyGame([p1, p2], win_condition_type=WinConditionType.EXACTLY_50_POINTS)
        self.assertTrue(is_game_over(game))
        self.assertEqual(get_winners(game), [p2])

    def test_most_points_after_20(self):
        p1 = Player("P1")
        p2 = Player("P2")
        p1.score = 43
        p2.score = 45
        game = DummyGame([p1, p2], round_number=20, win_condition_type=WinConditionType.MOST_POINTS_AFTER_20_ROUNDS)
        self.assertTrue(is_game_over(game))
        self.assertEqual(get_winners(game), [p2])

if __name__ == "__main__":
    unittest.main()
