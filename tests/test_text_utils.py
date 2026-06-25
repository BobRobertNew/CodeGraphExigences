import unittest
from unittest.mock import patch
from graph_tool.utils.text_utils import find_best_match, generate_short_id

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

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_extractone_returns_none(self, mock_extractOne):
        mock_extractOne.return_value = None
        choices = ["apple", "banana"]
        self.assertIsNone(find_best_match("apple", choices))

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_score_exact_threshold(self, mock_extractOne):
        mock_extractOne.return_value = ("apple", 70)
        choices = ["apple", "banana"]
        self.assertEqual(find_best_match("apple", choices, threshold=70), "apple")

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_score_below_threshold(self, mock_extractOne):
        mock_extractOne.return_value = ("apple", 69)
        choices = ["apple", "banana"]
        self.assertIsNone(find_best_match("apple", choices, threshold=70))

    def test_generate_short_id_normal(self):
        # Hash of "hello" is 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        result = generate_short_id("TEST", "hello")
        self.assertEqual(result, "TEST-2CF24DBA")

    def test_generate_short_id_empty_text(self):
        # Hash of "" is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        result = generate_short_id("PRE", "")
        self.assertEqual(result, "PRE-E3B0C442")

    def test_generate_short_id_none_text(self):
        result = generate_short_id("PRE", None)
        self.assertEqual(result, "PRE-E3B0C442")

    def test_generate_short_id_custom_length(self):
        result = generate_short_id("PRE", "hello", length=4)
        self.assertEqual(result, "PRE-2CF2")

if __name__ == "__main__":
    unittest.main()
