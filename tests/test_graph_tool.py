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

        self.commands.add_project_exigences("Projet Alpha", df)

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
        self.commands.add_project_exigences("Projet Alpha", pd.DataFrame(data))

        # Add REX with slightly different text to test fuzzy matching
        rex_data = {"Exigence": ["Securité systeme"]} # Note the missing accent
        self.commands.add_rex("Projet Alpha", pd.DataFrame(rex_data))

        rex_nodes = self.repo.get_nodes_by_type(NodeType.REX)
        self.assertEqual(len(rex_nodes), 1)

        proj = self.repo.find_node_by_exact_metadata("name", "Projet Alpha", NodeType.PROJET)
        exg = self.repo.get_nodes_by_type(NodeType.EXIGENCE)[0]

        self.assertTrue(self.repo.has_path(rex_nodes[0].id, proj.id))
        self.assertTrue(self.repo.has_path(rex_nodes[0].id, exg.id))

    def test_queries_similar_projects(self):
        data1 = {"Exigence": ["Exigence A", "Exigence B"]}
        data2 = {"Exigence": ["Exigence A", "Exigence C"]}
        data3 = {"Exigence": ["Exigence D"]}

        self.commands.add_project_exigences("P1", pd.DataFrame(data1))
        self.commands.add_project_exigences("P2", pd.DataFrame(data2))
        self.commands.add_project_exigences("P3", pd.DataFrame(data3))

        # P1 and P2 share Exigence A
        similar = self.queries.find_most_similar_projects("P1", ["Exigence A"], top_k=1)
        self.assertEqual(similar, ["P2"])

    def test_enhancement_integrity(self):
        data = {"Exigence": ["Exigence Sans Preuve"], "Preuve de conformité": [""]}
        self.commands.add_project_exigences("P1", pd.DataFrame(data))

        issues = self.enhancements.check_graph_integrity()
        self.assertEqual(len(issues["exigence_without_preuve"]), 1)
        self.assertEqual(len(issues["project_without_specification"]), 1)

if __name__ == "__main__":
    unittest.main()
