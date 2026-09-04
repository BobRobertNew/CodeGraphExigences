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

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_boundary_exact_threshold(self, mock_extractOne):
        # Test boundary condition where score equals exactly the threshold
        mock_extractOne.return_value = ("apple", 70)
        choices = ["apple", "banana"]
        self.assertEqual(find_best_match("appl", choices, threshold=70), "apple")

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_boundary_below_threshold(self, mock_extractOne):
        # Test boundary condition where score is just below the threshold
        mock_extractOne.return_value = ("apple", 69.9)
        choices = ["apple", "banana"]
        self.assertIsNone(find_best_match("appl", choices, threshold=70))

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

    def test_find_best_match_case_sensitivity(self):
        # rapidfuzz is case-sensitive by default
        self.assertIsNone(find_best_match("apple", ["APPLE"]))

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_type_error_on_integers(self, mock_extractOne):
        # Ensure we mock external library behavior explicitly for invalid inputs
        mock_extractOne.side_effect = TypeError("Mocked TypeError for invalid input")
        with self.assertRaises(TypeError):
            find_best_match("123", [123])

    def test_find_best_match_emoji_handling(self):
        # rapidfuzz does not strip emojis
        choices = ["apple 🍎", "banana"]
        self.assertEqual(find_best_match("apple", choices), "apple 🍎")

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

    def test_find_best_match_generators(self):
        # rapidfuzz extractOne supports generic iterables
        choices = (x for x in ["apple", "banana"])
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_empty_generator(self):
        # Because bool(generator) is True, the `if not choices:` check passes it through
        # and rapidfuzz handles empty generators by returning None
        choices = (x for x in [])
        self.assertIsNone(find_best_match("apple", choices))

    def test_find_best_match_out_of_bounds_threshold(self):
        choices = ["apple", "banana"]
        # Threshold > 100 should never match since max score is 100
        self.assertIsNone(find_best_match("apple", choices, threshold=105))
        # Threshold < 0 should act like threshold 0
        self.assertEqual(find_best_match("apple", choices, threshold=-10), "apple")
        # Floating point threshold
        self.assertEqual(find_best_match("apple", choices, threshold=99.9), "apple")
        self.assertIsNone(find_best_match("appl", choices, threshold=99.9))

    def test_find_best_match_tie_breaking(self):
        # rapidfuzz returns the first best match it encounters when there is a tie
        choices1 = ["cat", "bat"]
        choices2 = ["bat", "cat"]
        # "mat" matches "cat" and "bat" with the same score (66.66...)
        self.assertEqual(find_best_match("mat", choices1, threshold=60), "cat")
        self.assertEqual(find_best_match("mat", choices2, threshold=60), "bat")

    def test_find_best_match_whitespace_only(self):
        choices = ["   ", "\t", "\n"]
        self.assertEqual(find_best_match("   ", choices, threshold=100), "   ")
        # Query is all whitespace, matching a normal string
        self.assertIsNone(find_best_match("   ", ["apple", "banana"]))

    def test_find_best_match_newlines(self):
        choices = ["apple\nbanana", "apple banana"]
        self.assertEqual(find_best_match("apple\nbanana", choices, threshold=100), "apple\nbanana")
        # fuzzy matching with differing whitespaces
        self.assertEqual(find_best_match("apple\r\nbanana", choices, threshold=90), "apple\nbanana")

    def test_find_best_match_unicode(self):
        choices = ["こんにちは", "さようなら"]
        self.assertEqual(find_best_match("こんにちは", choices, threshold=100), "こんにちは")
        # Not a match
        self.assertIsNone(find_best_match("こんばんわ", choices, threshold=90))

    def test_find_best_match_long_strings(self):
        long_query = "a" * 1000
        choices = ["a" * 1000, "b" * 1000]
        self.assertEqual(find_best_match(long_query, choices), "a" * 1000)

        # 1 character off in a 1000 char string should have a very high score
        almost_query = "a" * 999 + "b"
        self.assertEqual(find_best_match(almost_query, choices, threshold=99), "a" * 1000)

    def test_find_best_match_transposition(self):
        # rapidfuzz handles small typos like transposition
        choices = ["receive", "deceive", "believe"]
        self.assertEqual(find_best_match("recieve", choices, threshold=80), "receive")

    def test_find_best_match_substring(self):
        # Substring/prefix should match the larger string with a high score
        choices = ["authentication", "authorization", "administration"]
        self.assertEqual(find_best_match("auth", choices, threshold=90), "authentication")

    def test_find_best_match_punctuation_mixed(self):
        # Punctuation differences should be handled
        choices = ["id-123", "id_124", "id.125"]
        self.assertEqual(find_best_match("id_123", choices, threshold=80), "id-123")

    def test_find_best_match_single_character(self):
        # Short strings or single characters matching exactly or closely
        choices = ["apple", "banana", "cherry"]
        self.assertEqual(find_best_match("a", choices, threshold=90), "apple")

    def test_find_best_match_numeric_strings(self):
        # Strings that contain numbers
        choices = ["12346", "99999", "11111"]
        self.assertEqual(find_best_match("12345", choices, threshold=80), "12346")



    def test_find_best_match_string_zero(self):
        # "0" evaluates to True, unlike integer 0
        choices = ["0", "1", "2"]
        self.assertEqual(find_best_match("0", choices), "0")

    def test_find_best_match_with_score_string_zero(self):
        choices = ["0", "1", "2"]
        match, score = find_best_match_with_score("0", choices)
        self.assertEqual(match, "0")
        self.assertEqual(score, 100)

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_with_score_boundary_exact_threshold(self, mock_extractOne):
        mock_extractOne.return_value = ("apple", 70)
        choices = ["apple", "banana"]
        match, score = find_best_match_with_score("appl", choices, threshold=70)
        self.assertEqual(match, "apple")
        self.assertEqual(score, 70)

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_with_score_boundary_below_threshold(self, mock_extractOne):
        mock_extractOne.return_value = ("apple", 69.9)
        choices = ["apple", "banana"]
        match, score = find_best_match_with_score("appl", choices, threshold=70)
        self.assertIsNone(match)
        self.assertIsNone(score)

    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_with_score_type_error(self, mock_extractOne):
        mock_extractOne.side_effect = TypeError("Mocked TypeError")
        with self.assertRaises(TypeError):
            find_best_match_with_score("123", [123])

    def test_find_best_match_choices_as_set(self):
        choices = {"apple", "banana", "cherry"}
        self.assertEqual(find_best_match("apple", choices), "apple")

    def test_find_best_match_with_score_choices_as_set(self):
        choices = {"apple", "banana", "cherry"}
        match, score = find_best_match_with_score("apple", choices)
        self.assertEqual(match, "apple")
        self.assertEqual(score, 100)



    @patch('graph_tool.utils.text_utils.process.extractOne')
    def test_find_best_match_exception_propagation(self, mock_extractOne):
        mock_extractOne.side_effect = ValueError("Something went wrong")
        with self.assertRaises(ValueError):
            find_best_match("apple", ["apple"])

    def test_find_best_match_with_score_out_of_bounds_threshold(self):
        choices = ["apple", "banana"]
        match, score = find_best_match_with_score("apple", choices, threshold=105)
        self.assertIsNone(match)
        self.assertIsNone(score)

    def test_find_best_match_order_independent(self):
        choices = ["John Doe", "Jane Smith"]
        self.assertEqual(find_best_match("Doe John", choices, threshold=80), "John Doe")

    def test_find_best_match_different_separators(self):
        choices = ["hello-world", "foo_bar", "test.case"]
        self.assertEqual(find_best_match("hello world", choices, threshold=80), "hello-world")

    def test_find_best_match_accented_characters(self):
        choices = ["cafe", "resume", "expose"]
        # rapidfuzz may not automatically normalize accents depending on configuration,
        # but check if it's close enough due to 1 char difference
        self.assertEqual(find_best_match("café", choices, threshold=70), "cafe")

    def test_find_best_match_prefix_partial(self):
        choices = ["supercalifragilisticexpialidocious", "something else"]
        self.assertEqual(find_best_match("supercali", choices, threshold=80), "supercalifragilisticexpialidocious")


if __name__ == "__main__":
    unittest.main()
