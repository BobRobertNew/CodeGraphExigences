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
            "Etat de Conformité": ["Surveillance conformité", "Other", "Surveillance conformité"]
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
            "Etat de Conformité": ["surveillance conformité", "Other"]
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
            self.assertIn("Column 'Etat de Conformité' not found. Proceeding without filtering.", str(w[0].message))

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 2)

    def test_add_rex_legacy_columns(self):
        # Initial project and exigences
        self.commands.add_project_exigences("ProjA", pd.DataFrame({
            "Exigence": ["Exg1"]
        }))

        # Add REX using legacy column names
        data = {
            "Exigence": ["Exg1"],
            "REX Detail": ["This is a legacy REX detail"]
        }
        df = pd.DataFrame(data)

        self.commands.add_rex("ProjA", df)

        rex_nodes = self.repo.get_nodes_by_type(NodeType.REX)
        self.assertEqual(len(rex_nodes), 1)
        self.assertEqual(rex_nodes[0].metadata["description"], "This is a legacy REX detail")

        edges = self.repo.get_all_edges()
        linked = [(e.source_id, e.target_id) for e in edges if e.target_id.startswith("REX") or e.source_id.startswith("REX")]
        self.assertEqual(len(linked), 2)  # Should link to project and exigence

    def test_add_rex_new_columns_and_loader(self):
        # Initial project and exigences
        self.commands.add_project_exigences("ProjB", pd.DataFrame({
            "Exigence": ["Exg2"]
        }))

        # Simulating the loader behavior with a custom function
        def mock_loader(data_source):
            return data_source

        data = {
            "Exigences": ["Exg2"],
            "Commentaire general": ["This is a new format REX detail"]
        }
        df = pd.DataFrame(data)

        self.commands.add_rex("ProjB", df, loader=mock_loader)

        rex_nodes = self.repo.get_nodes_by_type(NodeType.REX)
        self.assertEqual(len(rex_nodes), 1)
        self.assertEqual(rex_nodes[0].metadata["description"], "This is a new format REX detail")

    def test_add_rex_missing_rex_columns(self):
        # Initial project and exigences
        self.commands.add_project_exigences("ProjC", pd.DataFrame({
            "Exigence": ["Exg3"]
        }))

        data = {
            "Exigence": ["Exg3"],
            "SomeOtherColumn": ["Value"]
        }
        df = pd.DataFrame(data)

        with self.assertRaises(ValueError) as context:
            self.commands.add_rex("ProjC", df)

        self.assertIn("Neither 'REX Detail' nor 'Commentaire general' column is found", str(context.exception))

    def test_add_rex_exact_match_only(self):
        self.commands.add_project_exigences("ProjD", pd.DataFrame({
            "Exigence": ["Exg4 Exact"]
        }))

        data = {
            "Exigence": ["Exg4 Exact", "Exg4 Typo"],
            "REX Detail": ["Detail 1", "Detail 2"]
        }
        df = pd.DataFrame(data)

        def mock_loader(data_source):
            return data_source

        self.commands.add_rex("ProjD", df, loader=mock_loader, exact_match_only=True)

        rex_nodes = self.repo.get_nodes_by_type(NodeType.REX)
        self.assertEqual(len(rex_nodes), 1)
        self.assertEqual(rex_nodes[0].metadata["description"], "Detail 1")

    def test_add_specification_exact_match_only(self):
        self.commands.add_project_exigences("ProjE", pd.DataFrame({
            "Exigence": ["Exg5 Exact"]
        }))

        data = {
            "Exigence": ["Exg5 Exact", "Exg5 Typo"]
        }
        df = pd.DataFrame(data)

        self.commands.add_specification("SPEC-1", "Spec 1", df, exact_match_only=True)

        # In exact match only, we expect only the exact match to be linked to spec
        spec_nodes = self.repo.get_nodes_by_type(NodeType.SPECIFICATION)
        self.assertEqual(len(spec_nodes), 1)

        edges = self.repo.get_all_edges()
        spec_edges = [e for e in edges if e.source_id == "SPEC-1" or e.target_id == "SPEC-1"]
        self.assertEqual(len(spec_edges), 1)

    def test_add_preuves(self):
        # Initial project and exigences
        from graph_tool.utils.text_utils import generate_short_id
        from graph_tool.domain.entities import Node

        exigence_text = "Exigence Preuve"
        exg_id = generate_short_id("EXG", exigence_text)
        exg_node = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
        self.repo.add_node(exg_node)

        data = {
            "Exigences": [exigence_text],
            "MétierX_Concerné": ["x"],
            "MétierX_Preuve de conformité": ["Phase Contrat: contract text"]
        }
        df = pd.DataFrame(data)

        # Simulating the loader behavior with a custom function
        def mock_loader(data_source):
            return data_source

        self.commands.add_preuves(data_source=df, loader=mock_loader)

        preuves = self.repo.get_nodes_by_type(NodeType.PREUVE)
        self.assertEqual(len(preuves), 1)
        self.assertEqual(preuves[0].metadata["description"], "contract text")

        metiers = self.repo.get_nodes_by_type(NodeType.METIER)
        self.assertEqual(len(metiers), 1)
        self.assertEqual(metiers[0].metadata["name"], "MétierX")

        phases = self.repo.get_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].metadata["name"], "Contrat")

if __name__ == '__main__':
    unittest.main()
