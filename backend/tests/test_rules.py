import unittest
from engine.rules import is_valid_play, get_play_type, compare_plays
from engine.piece import Piece

# -------------------------------
# PAIR
# -------------------------------
class TestPair(unittest.TestCase):
    def test_valid_pair(self):
        play = [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")]
        self.assertTrue(is_valid_play(play))
        self.assertEqual(get_play_type(play), "PAIR")


# -------------------------------
# INVALID PLAY
# -------------------------------
class TestInvalidPlay(unittest.TestCase):
    def test_invalid_pair(self):
        play = [Piece("SOLDIER_RED"), Piece("CANNON_BLACK")]
        self.assertFalse(is_valid_play(play))
        self.assertEqual(get_play_type(play), "INVALID")

    def test_extended_straight_wrong_color(self):
        pieces = [
            Piece("CHARIOT_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_BLACK"),
            Piece("HORSE_RED")
        ]
        self.assertFalse(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "INVALID")

    def test_extended_straight_wrong_group(self):
        pieces = [
            Piece("SOLDIER_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_RED"),
            Piece("HORSE_RED")
        ]
        self.assertFalse(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "INVALID")

    def test_extended_straight_no_duplicate(self):
        pieces = [
            Piece("CHARIOT_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_RED"),
            Piece("ADVISOR_RED")
        ]
        self.assertFalse(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "INVALID")


# -------------------------------
# EXTENDED_STRAIGHT
# -------------------------------
class TestExtendedStraight(unittest.TestCase):
    def test_valid_extended_straight(self):
        pieces = [
            Piece("CHARIOT_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_RED"),
            Piece("HORSE_RED")  # duplicated HORSE
        ]
        self.assertTrue(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "EXTENDED_STRAIGHT")
        
    def test_valid_extended_straight(self):
        pieces = [
            Piece("GENERAL_RED"),
            Piece("ADVISOR_RED"),
            Piece("ELEPHANT_RED"),
            Piece("ELEPHANT_RED")  # duplicated ELEPHANT
        ]
        self.assertTrue(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "EXTENDED_STRAIGHT")
        
    def test_valid_extended_straight(self):
        pieces = [
            Piece("CHARIOT_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_RED"),
            Piece("CANNON_RED"),
            Piece("HORSE_RED")  # duplicated HORSE
        ]
        self.assertTrue(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "EXTENDED_STRAIGHT_5")
        
    def test_valid_extended_straight(self):
        pieces = [
            Piece("GENERAL_RED"),
            Piece("ADVISOR_RED"),
            Piece("ADVISOR_RED"),
            Piece("ELEPHANT_RED"),
            Piece("ELEPHANT_RED")  
        ]
        self.assertTrue(is_valid_play(pieces))
        self.assertEqual(get_play_type(pieces), "EXTENDED_STRAIGHT_5")


# -------------------------------
# COMPARE PLAYS
# -------------------------------
class TestComparePlays(unittest.TestCase):
    def test_compare_pair_by_point_sum(self):
        play1 = [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")]  # 3 + 3 = 6
        play2 = [Piece("CANNON_RED"), Piece("CANNON_RED")]    # 7 + 7 = 14
        result = compare_plays(play1, play2)
        self.assertEqual(result, 2)  # play2 wins
        
    def test_compare_extended_straight_draw(self):
        black = [
            Piece("CHARIOT_BLACK"),
            Piece("CHARIOT_BLACK"),
            Piece("HORSE_BLACK"),
            Piece("CANNON_BLACK")
        ]
        red = [
            Piece("CHARIOT_RED"),
            Piece("HORSE_RED"),
            Piece("CANNON_RED"),
            Piece("CANNON_RED")
        ]
        self.assertEqual(get_play_type(black), "EXTENDED_STRAIGHT")
        self.assertEqual(get_play_type(red), "EXTENDED_STRAIGHT")

        result = compare_plays(black, red)
        self.assertEqual(result, 2) 
        

if __name__ == "__main__":
    unittest.main()
