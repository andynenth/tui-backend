import unittest
from engine.scoring import calculate_score

class TestScoring(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(calculate_score(2, 2), 7)

    def test_zero_success(self):
        self.assertEqual(calculate_score(0, 0), 3)

    def test_zero_fail(self):
        self.assertEqual(calculate_score(0, 1), -1)

    def test_under(self):
        self.assertEqual(calculate_score(3, 1), -2)

    def test_over(self):
        self.assertEqual(calculate_score(2, 5), -3)

if __name__ == "__main__":
    unittest.main()
