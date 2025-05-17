import unittest
from engine.game import Game
from engine.win_conditions import WinConditionType

class TestGameLogic(unittest.TestCase):
    def test_deal_gives_8_each(self):
        game = Game()
        game._deal_pieces()
        self.assertTrue(all(len(p.hand) == 8 for p in game.players))

    def test_redeal_multiplier(self):
        game = Game()
        game.redeal_multiplier = 1
        game._deal_pieces()

        # Force a redeal manually
        game.redeal_multiplier += 1
        self.assertEqual(game.redeal_multiplier, 2)

if __name__ == "__main__":
    unittest.main()
