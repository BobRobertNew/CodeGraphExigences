import unittest
import pandas as pd
import warnings
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.domain.entities import NodeType

class TestCommands(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.commands = CommandHandler(self.repo, self.repo)

    def test_add_project_exigences_filter_exact_match(self):
        data = {
            "Exigence": ["Exigence 1", "Exigence 2", "Exigence 3"],
            "Etat de conformité": ["Surveillance conformité", "Other", "Surveillance conformité"]
        }
        df = pd.DataFrame(data)

        # Catch warnings to ensure no warnings are emitted
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.commands.add_project_exigences("P1", df)
            self.assertEqual(len(w), 0)

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 2)
        descriptions = [node.metadata["description"] for node in exg_nodes]
        self.assertIn("Exigence 1", descriptions)
        self.assertIn("Exigence 3", descriptions)
        self.assertNotIn("Exigence 2", descriptions)

    def test_add_project_exigences_filter_case_insensitive_warning(self):
        data = {
            "Exigence": ["Exigence 1", "Exigence 2"],
            "Etat de conformité": ["surveillance conformité", "Other"]
        }
        df = pd.DataFrame(data)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.commands.add_project_exigences("P2", df)

            # Check warning
            self.assertEqual(len(w), 1)
            self.assertIn("Some rows matched 'Surveillance conformité' with different casing.", str(w[0].message))

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 1)
        self.assertEqual(exg_nodes[0].metadata["description"], "Exigence 1")

    def test_add_project_exigences_missing_column_warning(self):
        data = {
            "Exigence": ["Exigence 1", "Exigence 2"]
        }
        df = pd.DataFrame(data)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.commands.add_project_exigences("P3", df)

            # Check warning
            self.assertEqual(len(w), 1)
            self.assertIn("Column 'Etat de conformité' not found. Proceeding without filtering.", str(w[0].message))

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 2)

if __name__ == '__main__':
    unittest.main()
