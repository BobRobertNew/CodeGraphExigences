import unittest
import pandas as pd
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.use_cases.enhancements import GraphEnhancements
from graph_tool.domain.entities import NodeType

class TestGraphTool(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.commands = CommandHandler(self.repo, self.repo)
        self.queries = QueryHandler(self.repo)
        self.enhancements = GraphEnhancements(self.repo)

    def test_add_project_exigences(self):
        data = {
            "Normes": ["Loi 1"],
            "Exigence": ["Le système doit être sécurisé"],
            "Phase projet": ["Conception"],
            "Métier": ["DevSecOps"],
            "Preuve de conformité": ["Audit code"]
        }
        df = pd.DataFrame(data)

        self.commands.add_project_exigences("Projet Alpha", df, owner="TestOwner", author="TestAuthor")

        proj_nodes = self.repo.get_nodes_by_type(NodeType.PROJET)
        self.assertEqual(len(proj_nodes), 1)
        self.assertEqual(proj_nodes[0].metadata["name"], "Projet Alpha")

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 1)
        self.assertEqual(exg_nodes[0].metadata["description"], "Le système doit être sécurisé")

        # Test paths
        exg_id = exg_nodes[0].id
        neighbors = self.repo.get_neighbors(exg_id)
        neighbor_types = [n.type for n in neighbors]
        self.assertIn(NodeType.PROJET, neighbor_types)
        self.assertIn(NodeType.LOI, neighbor_types)
        self.assertIn(NodeType.PHASE_PROJET, neighbor_types)
        self.assertIn(NodeType.METIER, neighbor_types)
        self.assertIn(NodeType.PREUVE, neighbor_types)

    def test_add_rex_with_fuzzy_matching(self):
        # Create base
        data = {"Exigence": ["Sécurité du système"]}
        self.commands.add_project_exigences("Projet Alpha", pd.DataFrame(data), owner="TestOwner", author="TestAuthor")

        # Add REX with slightly different text to test fuzzy matching
        rex_data = {
            "Exigence": ["Securité systeme"], # Note the missing accent
            "REX Detail": ["Test detail"]
        }
        self.commands.add_rex("Projet Alpha", pd.DataFrame(rex_data), owner="TestOwner", author="TestAuthor")

        rex_nodes = self.repo.get_nodes_by_type(NodeType.REX)
        self.assertEqual(len(rex_nodes), 1)
        self.assertEqual(rex_nodes[0].metadata.get("description"), "Test detail")

        proj = self.repo.find_node_by_exact_metadata("name", "Projet Alpha", NodeType.PROJET)
        exg = self.repo.get_nodes_by_type(NodeType.EXIGENCE)[0]

        self.assertTrue(self.repo.has_path(rex_nodes[0].id, proj.id))
        self.assertTrue(self.repo.has_path(rex_nodes[0].id, exg.id))

    def test_queries_similar_projects(self):
        data1 = {"Exigence": ["Exigence A", "Exigence B"]}
        data2 = {"Exigence": ["Exigence A", "Exigence C"]}
        data3 = {"Exigence": ["Exigence D"]}

        self.commands.add_project_exigences("P1", pd.DataFrame(data1), owner="TestOwner", author="TestAuthor")
        self.commands.add_project_exigences("P2", pd.DataFrame(data2), owner="TestOwner", author="TestAuthor")
        self.commands.add_project_exigences("P3", pd.DataFrame(data3), owner="TestOwner", author="TestAuthor")

        # P1 and P2 share Exigence A
        similar = self.queries.find_most_similar_projects("P1", ["Exigence A"], top_k=1)
        self.assertEqual(similar, ["P2"])

    def test_queries_similar_projects_exact_match(self):
        data1 = {"Exigence": ["Exigence Alpha", "Exigence Beta"]}
        data2 = {"Exigence": ["Exigence Alpha", "Exigence Gamma"]}

        self.commands.add_project_exigences("P1", pd.DataFrame(data1), owner="TestOwner", author="TestAuthor")
        self.commands.add_project_exigences("P2", pd.DataFrame(data2), owner="TestOwner", author="TestAuthor")

        # Test exact match True, should find P2 with exact string
        similar_exact = self.queries.find_most_similar_projects("P1", ["Exigence Alpha"], top_k=1, exact_match=True)
        self.assertEqual(similar_exact, ["P2"])

        # Test exact match True with fuzzy string (should fail to find P2)
        similar_exact_fuzzy = self.queries.find_most_similar_projects("P1", ["Exigence Alph"], top_k=1, exact_match=True)
        self.assertEqual(similar_exact_fuzzy, [])

        # Test exact match False with fuzzy string (should find P2 using fuzzy match)
        similar_fuzzy = self.queries.find_most_similar_projects("P1", ["Exigence Alph"], top_k=1, exact_match=False)
        self.assertEqual(similar_fuzzy, ["P2"])

    def test_get_useful_rex_exact_match(self):
        # Create base
        data1 = {"Exigence": ["Sécurité du système", "Exigence Z"]}
        data2 = {"Exigence": ["Sécurité du système", "Exigence Y"]}
        self.commands.add_project_exigences("P1", pd.DataFrame(data1), owner="TestOwner", author="TestAuthor")
        self.commands.add_project_exigences("P2", pd.DataFrame(data2), owner="TestOwner", author="TestAuthor")

        rex_data = {
            "Exigence": ["Sécurité du système"],
            "REX Detail": ["Detail REX 1"]
        }
        self.commands.add_rex("P2", pd.DataFrame(rex_data), owner="TestOwner", author="TestAuthor")

        # Test get_useful_rex exact match with correct string
        useful_rex_exact = self.queries.get_useful_rex("P1", ["Sécurité du système"], exact_match=True)
        self.assertEqual(len(useful_rex_exact), 1)

        # Test get_useful_rex exact match with fuzzy string (should fail)
        useful_rex_exact_fuzzy = self.queries.get_useful_rex("P1", ["Securite du systeme"], exact_match=True)
        self.assertEqual(len(useful_rex_exact_fuzzy), 0)

        # Test get_useful_rex fuzzy match with fuzzy string (should find)
        useful_rex_fuzzy = self.queries.get_useful_rex("P1", ["Securite du systeme"], exact_match=False)
        self.assertEqual(len(useful_rex_fuzzy), 1)

    def test_enhancement_integrity(self):
        data = {"Exigence": ["Exigence Sans Preuve"], "Preuve de conformité": [""]}
        self.commands.add_project_exigences("P1", pd.DataFrame(data), owner="TestOwner", author="TestAuthor")

        issues = self.enhancements.check_graph_integrity()
        self.assertEqual(len(issues["exigence_without_preuve"]), 1)
        self.assertEqual(len(issues["project_without_specification"]), 1)

    def test_visualize_graph_path_traversal(self):
        import os
        import tempfile
        import shutil

        # Use a temporary directory as the base_dir to avoid polluting the workspace
        test_base_dir = tempfile.mkdtemp()

        try:
            # Valid path
            valid_path = "valid_graph.html"
            result = self.enhancements.visualize_graph(output_file=os.path.join(test_base_dir, valid_path), base_dir=test_base_dir)
            self.assertTrue(result.endswith(valid_path))

            # Valid path in subdirectory
            valid_sub_path = "reports/valid_graph.html"
            os.makedirs(os.path.join(test_base_dir, "reports"), exist_ok=True)
            result = self.enhancements.visualize_graph(output_file=os.path.join(test_base_dir, valid_sub_path), base_dir=test_base_dir)
            self.assertTrue(result.endswith(os.path.join("reports", "valid_graph.html")))

            # Invalid path traversal
            with self.assertRaises(ValueError) as context:
                # Try to write outside test_base_dir
                self.enhancements.visualize_graph(output_file=os.path.join(test_base_dir, "../malicious.html"), base_dir=test_base_dir)
            self.assertIn("Path traversal detected", str(context.exception))

            # Invalid absolute path outside base directory
            with self.assertRaises(ValueError) as context:
                self.enhancements.visualize_graph(output_file="/tmp/malicious.html", base_dir=test_base_dir)
            self.assertIn("Path traversal detected", str(context.exception))
        finally:
            # Clean up the temporary directory
            shutil.rmtree(test_base_dir)

if __name__ == "__main__":
    unittest.main()
