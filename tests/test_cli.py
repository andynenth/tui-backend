import unittest
from ui.cli import show_winner
from engine.player import Player

class TestCLI(unittest.TestCase):
    def test_show_winner_single(self):
        p1 = Player("P1")
        p1.score = 50
        show_winner([p1]) 

    def test_show_winner_tie(self):
        p1 = Player("P1")
        p2 = Player("P2")
        p1.score = 50
        p2.score = 50
        show_winner([p1, p2])

    def test_show_winner_none(self):
        show_winner([])

if __name__ == "__main__":
    unittest.main()
