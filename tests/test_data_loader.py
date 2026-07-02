import unittest
import pandas as pd
from graph_tool.infrastructure.data_loader import load_data, load_and_clean_data

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

    def test_load_and_clean_data_auto_detects_unnamed_columns(self):
        # Create a dataframe simulating pd.read_excel(header=0) on a 2-row header excel file
        # where the first row has empty headers.
        df_input = pd.DataFrame({
            "First Name": ["John", "Doe"],
            "Unnamed: 1": ["Jane", "Smith"],
            "City": ["New York", "Los Angeles"]
        })

        # By passing the dataframe to load_and_clean_data, it should detect "Unnamed: 1",
        # reconstruct the raw DataFrame, and apply _apply_2row_header_logic.
        df_output = load_and_clean_data(df_input)

        # Because of forward fill (`ffill(axis=1)`), the NaN in "Unnamed: 1" is replaced with "First Name".
        # So "First Name" and "Jane" merge to "First Name_Jane".

        expected_columns = ["First Name_John", "First Name_Jane", "City_New York"]
        self.assertEqual(list(df_output.columns), expected_columns)
        self.assertEqual(df_output.iloc[0, 0], "Doe")
        self.assertEqual(df_output.iloc[0, 1], "Smith")
        self.assertEqual(df_output.iloc[0, 2], "Los Angeles")

if __name__ == "__main__":
    unittest.main()
