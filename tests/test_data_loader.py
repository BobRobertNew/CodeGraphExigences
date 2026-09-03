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

    def test_load_data_with_safe_base_dir(self):
        import tempfile
        import os
        from graph_tool.infrastructure.data_loader import SecurityError

        # Create a temporary directory structure to simulate the error condition
        with tempfile.TemporaryDirectory() as root_temp_dir:
            # Create a base directory
            base_dir = os.path.join(root_temp_dir, "base")
            os.makedirs(base_dir)

            # Create a dummy excel file in base_dir
            df = pd.DataFrame({"A": [1, 2]})
            file_path = os.path.join(base_dir, "test_file.xlsx")
            df.to_excel(file_path, index=False)

            # Verify that loading it with safe_base_dir works
            loaded_df = load_data(file_path, safe_base_dir=base_dir)
            self.assertEqual(loaded_df.shape, (2, 1))

            # Try to load a file from outside base_dir
            outside_dir = os.path.join(root_temp_dir, "outside")
            os.makedirs(outside_dir)
            outside_file = os.path.join(outside_dir, "outside.xlsx")
            df.to_excel(outside_file, index=False)

            with self.assertRaises(SecurityError):
                load_data(outside_file, safe_base_dir=base_dir)

if __name__ == "__main__":
    unittest.main()
