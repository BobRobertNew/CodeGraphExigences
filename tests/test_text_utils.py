import unittest
from unittest.mock import patch
from graph_tool.utils.text_utils import find_best_match, generate_short_id, find_best_match_with_score

class TestTextUtils(unittest.TestCase):
    def test_generate_short_id_normal(self):
        result = generate_short_id("REQ", "some text")
        self.assertTrue(result.startswith("REQ-"))
        self.assertEqual(len(result), 4 + 8) # prefix + '-' + 8 chars length

    def test_generate_short_id_empty_text(self):
        result = generate_short_id("REQ", "")
        self.assertTrue(result.startswith("REQ-"))

    def test_generate_short_id_none_text(self):
        result = generate_short_id("REQ", None)
        self.assertTrue(result.startswith("REQ-"))

    def test_generate_short_id_custom_length(self):
        result = generate_short_id("REQ", "some text", length=12)
        self.assertTrue(result.startswith("REQ-"))
        self.assertEqual(len(result), 4 + 12)

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

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_result_none(self, mock_extractOne):
        # Triggering a case where process.extractOne returns None
        # by mocking it.
        # This exercises the falsy `if result:` branch.
        mock_extractOne.return_value = None
        self.assertIsNone(find_best_match("apple", ["banana"]))

    def test_find_best_match_whitespace_handling(self):
        choices = ["apple", "banana", "cherry"]
        self.assertEqual(find_best_match("  apple  ", choices), "apple")
        # Just spaces should likely match nothing above 70 threshold for these choices
        self.assertIsNone(find_best_match("   ", choices))

    def test_find_best_match_empty_elements_in_choices(self):
        choices = ["", "apple", "banana"]
        self.assertEqual(find_best_match("apple", choices), "apple")

        # Test empty query with empty element in choices
        self.assertIsNone(find_best_match("", choices))

    def test_find_best_match_special_characters(self):
        choices = ["apple!", "@banana", "cherry#"]
        self.assertEqual(find_best_match("apple!", choices), "apple!")
        self.assertEqual(find_best_match("@banana", choices), "@banana")

    def test_find_best_match_threshold_bounds(self):
        choices = ["apple", "banana", "cherry"]
        self.assertEqual(find_best_match("apple", choices, threshold=0), "apple")
        self.assertEqual(find_best_match("apple", choices, threshold=100), "apple")
        # For non-exact match with threshold 100
        self.assertIsNone(find_best_match("appl", choices, threshold=100))

    def test_find_best_match_similar_strings(self):
        choices = ["apple tree", "apple", "green apple"]
        # Ensure it matches the exact one rather than substrings
        self.assertEqual(find_best_match("apple", choices, threshold=100), "apple")

    def test_find_best_match_choices_with_none(self):
        # rapidfuzz process can handle None elements by ignoring them
        choices = ["banana", None, "apple"]
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_choices_all_none(self):
        # If all choices are None, no match will be found
        choices = [None, None]
        self.assertIsNone(find_best_match("apple", choices))

    def test_find_best_match_duplicates_in_choices(self):
        choices = ["banana", "apple", "apple"]
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_dict_choices(self):
        # rapidfuzz supports passing a dictionary for choices.
        # ExtractOne returns a 3-element tuple: (match, score, key)
        # Our function expects result[0] to be the match and result[1] to be the score.
        choices = {"b": "banana", "a": "apple"}
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_with_score_exact(self):
        choices = ["apple", "banana", "orange"]
        match, score = find_best_match_with_score("apple", choices)
        self.assertEqual(match, "apple")
        self.assertEqual(score, 100)

    def test_find_best_match_with_score_fuzzy(self):
        choices = ["apple", "banana", "orange"]
        match, score = find_best_match_with_score("aple", choices)
        self.assertEqual(match, "apple")
        self.assertGreaterEqual(score, 70)
        self.assertLess(score, 100)

    def test_find_best_match_with_score_below_threshold(self):
        choices = ["apple", "banana", "orange"]
        match, score = find_best_match_with_score("grapefruit", choices, threshold=90)
        self.assertIsNone(match)
        self.assertIsNone(score)

    def test_find_best_match_with_score_empty_choices(self):
        match, score = find_best_match_with_score("apple", [])
        self.assertIsNone(match)
        self.assertIsNone(score)

    def test_find_best_match_with_score_empty_query(self):
        choices = ["apple", "banana"]
        match, score = find_best_match_with_score("", choices)
        self.assertIsNone(match)
        self.assertIsNone(score)

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_with_score_result_none(self, mock_extractOne):
        mock_extractOne.return_value = None
        match, score = find_best_match_with_score("apple", ["banana"])
        self.assertIsNone(match)
        self.assertIsNone(score)

if __name__ == "__main__":
    unittest.main()
