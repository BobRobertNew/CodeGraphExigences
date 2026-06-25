import unittest
import os
import pandas as pd
from graph_tool.infrastructure.data_loader import load_data, SecurityError

class TestDataLoaderSecurity(unittest.TestCase):
    def setUp(self):
        # Create a dummy CSV file in the current directory for testing
        self.test_dir = os.path.abspath(os.path.dirname(__file__))
        self.project_root = os.path.dirname(self.test_dir)
        self.safe_base_dir = os.path.join(self.test_dir, "safe_dir")
        os.makedirs(self.safe_base_dir, exist_ok=True)

        self.valid_csv_path = os.path.join(self.safe_base_dir, "test.csv")
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        df.to_csv(self.valid_csv_path, index=False)

        # Create a dummy file outside the safe dir
        self.outside_csv_path = os.path.join(self.test_dir, "outside.csv")
        df.to_csv(self.outside_csv_path, index=False)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.valid_csv_path):
            os.remove(self.valid_csv_path)
        if os.path.exists(self.outside_csv_path):
            os.remove(self.outside_csv_path)
        if os.path.exists(self.safe_base_dir):
            os.rmdir(self.safe_base_dir)

    def test_load_data_within_safe_dir(self):
        # Should succeed because file is in safe_base_dir
        df = load_data(self.valid_csv_path, safe_base_dir=self.safe_base_dir)
        self.assertEqual(len(df), 2)

    def test_load_data_outside_safe_dir_raises_security_error(self):
        # Should raise SecurityError because file is outside safe_base_dir
        with self.assertRaises(SecurityError):
            load_data(self.outside_csv_path, safe_base_dir=self.safe_base_dir)

    def test_load_data_path_traversal_attack(self):
        # Attack payload: attempting to go up and out of the safe_base_dir
        attack_path = os.path.join(self.safe_base_dir, "..", "outside.csv")
        with self.assertRaises(SecurityError):
            load_data(attack_path, safe_base_dir=self.safe_base_dir)

if __name__ == "__main__":
    unittest.main()
