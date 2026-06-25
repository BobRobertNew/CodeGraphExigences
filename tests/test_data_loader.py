import unittest
from graph_tool.infrastructure.data_loader import load_data

class TestDataLoader(unittest.TestCase):
    def test_load_data_unsupported_extension(self):
        with self.assertRaisesRegex(ValueError, "Unsupported file format. Please provide .xls, .xlsx, or .csv"):
            load_data("data.txt")

    def test_load_data_invalid_source_type(self):
        with self.assertRaisesRegex(ValueError, "Source must be a file path string or a pandas DataFrame."):
            load_data(123)

        with self.assertRaisesRegex(ValueError, "Source must be a file path string or a pandas DataFrame."):
            load_data(["list", "of", "strings"])

        with self.assertRaisesRegex(ValueError, "Source must be a file path string or a pandas DataFrame."):
            load_data(None)

if __name__ == "__main__":
    unittest.main()
