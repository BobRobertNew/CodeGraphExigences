import unittest
from graph_tool.utils.text_utils import find_best_match

class TestTextUtils(unittest.TestCase):
    def test_find_best_match_exact(self):
        choices = ["apple", "banana", "cherry"]
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_fuzzy_above_threshold(self):
        choices = ["Securite du systeme", "Performance", "Fiabilite"]
        # "Sécurité du système" is fuzzy-matched with "Securite du systeme"
        self.assertEqual(find_best_match("Sécurité du système", choices), "Securite du systeme")

    def test_find_best_match_fuzzy_below_threshold(self):
        choices = ["apple", "banana", "cherry"]
        # "xylophone" is very different from any of the choices, should score below 70
        self.assertIsNone(find_best_match("xylophone", choices))

    def test_find_best_match_custom_threshold(self):
        choices = ["apple", "banana", "cherry"]
        # "app" to "apple" matches with a certain score (often around 90)
        # If we set threshold to 100, it should fail
        self.assertIsNone(find_best_match("app", choices, threshold=100))
        # If we set threshold lower, it should pass
        self.assertEqual(find_best_match("app", choices, threshold=50), "apple")

    def test_find_best_match_empty_query(self):
        choices = ["apple", "banana", "cherry"]
        self.assertIsNone(find_best_match("", choices))

    def test_find_best_match_none_query(self):
        choices = ["apple", "banana", "cherry"]
        self.assertIsNone(find_best_match(None, choices))

    def test_find_best_match_empty_choices(self):
        self.assertIsNone(find_best_match("apple", []))

    def test_find_best_match_none_choices(self):
        self.assertIsNone(find_best_match("apple", None))

    def test_find_best_match_extract_returns_none(self):
        self.assertIsNone(find_best_match("apple", [None]))

    def test_find_best_match_almost_match(self):
        choices = ["apples", "bananas", "cherries"]
        self.assertEqual(find_best_match("apple", choices), "apples")

    def test_find_best_match_case_insensitive(self):
        choices = ["APPLE", "Banana", "Cherry"]
        self.assertEqual(find_best_match("apple", choices), "APPLE")

    def test_find_best_match_misspelled(self):
        choices = ["apple", "banana", "cherry"]
        self.assertEqual(find_best_match("aple", choices), "apple")

    def test_find_best_match_special_characters(self):
        choices = ["test-case", "test_case", "test case"]
        self.assertIn(find_best_match("test~case", choices), choices)

    def test_find_best_match_score_exactly_threshold(self):
        # We need a case where the fuzzy match score is exactly 70.
        # This is hard to guess, but we can verify threshold boundary behavior.
        choices = ["apple"]
        # "ap" against "apple" typically scores around 90
        self.assertEqual(find_best_match("ap", choices, threshold=90), "apple")
        # Ensure it fails if threshold is higher than the score
        self.assertIsNone(find_best_match("ap", choices, threshold=91))

if __name__ == "__main__":
    unittest.main()
