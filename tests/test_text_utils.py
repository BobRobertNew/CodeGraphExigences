import unittest
import hashlib
from graph_tool.utils.text_utils import generate_short_id

class TestTextUtils(unittest.TestCase):
    def test_generate_short_id_basic(self):
        prefix = "PRJ"
        text = "Test Project Name"
        expected_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8].upper()
        expected_output = f"{prefix}-{expected_hash}"

        result = generate_short_id(prefix, text)
        self.assertEqual(result, expected_output)

    def test_generate_short_id_empty_prefix(self):
        prefix = ""
        text = "Some text"
        expected_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8].upper()
        expected_output = f"-{expected_hash}"

        result = generate_short_id(prefix, text)
        self.assertEqual(result, expected_output)

    def test_generate_short_id_lengths(self):
        prefix = "TEST"
        text = "Hello World"
        full_hash = hashlib.md5(text.encode('utf-8')).hexdigest().upper()

        # Length 0
        self.assertEqual(generate_short_id(prefix, text, length=0), f"{prefix}-")

        # Negative length
        # Slicing with negative length up to -1 gives all but last character.
        # However, the user request says test negative length.
        # hash_hex[:length].upper() will behave like normal python slicing.
        # E.g. length=-1 will exclude the last character.
        expected_hash_neg_1 = full_hash[:-1]
        self.assertEqual(generate_short_id(prefix, text, length=-1), f"{prefix}-{expected_hash_neg_1}")

        # Length greater than 32
        self.assertEqual(generate_short_id(prefix, text, length=100), f"{prefix}-{full_hash}")

    def test_generate_short_id_empty_text(self):
        prefix = "EMPTY"
        text = ""
        expected_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8].upper()

        result = generate_short_id(prefix, text)
        self.assertEqual(result, f"{prefix}-{expected_hash}")

        result_none = generate_short_id(prefix, None)
        self.assertEqual(result_none, f"{prefix}-{expected_hash}")

if __name__ == '__main__':
    unittest.main()
