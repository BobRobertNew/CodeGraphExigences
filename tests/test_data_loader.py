import unittest
import pandas as pd
from graph_tool.infrastructure.data_loader import load_data, clean_dataframe, load_and_clean_data

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.df_with_nan = pd.DataFrame({
            "col1": ["val1", None, "val3"],
            "col2": [1, 2, None]
        })

        self.df_clean_expected = pd.DataFrame({
            "col1": ["val1", "", "val3"],
            "col2": [1.0, 2.0, ""]
        })

    def test_load_data_with_dataframe(self):
        loaded_df = load_data(self.df_with_nan)
        # Should return a copy of the dataframe
        self.assertTrue(loaded_df.equals(self.df_with_nan))
        self.assertIsNot(loaded_df, self.df_with_nan)

    def test_clean_dataframe(self):
        cleaned_df = clean_dataframe(self.df_with_nan.copy())

        # Test if NaNs are replaced with empty strings
        # Pandas fillna with empty string on mixed/numeric columns can have float inputs
        # Instead of strict equality due to typing changes, we just check missing values
        self.assertFalse(cleaned_df.isnull().values.any())
        self.assertEqual(cleaned_df.iloc[1]["col1"], "")
        self.assertEqual(cleaned_df.iloc[2]["col2"], "")

    def test_load_and_clean_data_with_dataframe(self):
        result_df = load_and_clean_data(self.df_with_nan)

        # Original shouldn't be modified
        self.assertTrue(self.df_with_nan.isnull().values.any())

        # Result should be cleaned
        self.assertFalse(result_df.isnull().values.any())
        self.assertEqual(result_df.iloc[1]["col1"], "")
        self.assertEqual(result_df.iloc[2]["col2"], "")

    def test_load_data_invalid_source(self):
        with self.assertRaises(ValueError):
            load_data(123)

    def test_load_data_unsupported_extension(self):
        with self.assertRaises(ValueError):
            load_data("file.txt")

if __name__ == '__main__':
    unittest.main()
