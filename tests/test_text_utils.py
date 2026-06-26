import unittest
from graph_tool.utils.text_utils import find_best_match, generate_short_id

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

    def test_find_best_match_choices_with_none(self):
        self.assertIsNone(find_best_match("apple", [None]))

    def test_find_best_match_whitespace_query(self):
        self.assertIsNone(find_best_match("   ", ["apple", "banana"]))

    def test_find_best_match_choices_with_empty_strings(self):
        self.assertIsNone(find_best_match("apple", ["", " "]))

if __name__ == "__main__":
    unittest.main()
