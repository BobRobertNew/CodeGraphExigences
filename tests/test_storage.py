import unittest
import os
import pandas as pd
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.storage import StorageHandler
from graph_tool.domain.entities import NodeType

class TestStorageHandler(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.commands = CommandHandler(self.repo, self.repo)
        self.storage = StorageHandler(self.repo)

        # Populate with some test data
        data = {
            "Normes": ["Loi 1"],
            "Exigence": ["Le système doit être sécurisé"],
            "Phase projet": ["Conception"],
            "Métier": ["DevSecOps"],
            "Preuve de conformité": ["Audit code"]
        }
        df = pd.DataFrame(data)
        self.commands.add_project_exigences("Projet Storage Test", df)

        self.test_files = ["test_graph.graphml", "test_graph.gexf", "test_graph.json", "test_graph.pkl"]

    def tearDown(self):
        # Cleanup files after tests
        for f in self.test_files:
            if os.path.exists(f):
                os.remove(f)

    def _verify_graph_loaded(self):
        proj_nodes = self.repo.get_nodes_by_type(NodeType.PROJET)
        self.assertEqual(len(proj_nodes), 1)
        self.assertEqual(proj_nodes[0].metadata.get("name"), "Projet Storage Test")

        exg_nodes = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exg_nodes), 1)
        self.assertEqual(exg_nodes[0].metadata.get("description"), "Le système doit être sécurisé")

    def test_save_load_graphml(self):
        filepath = "test_graph.graphml"
        self.storage.save_graph(filepath, format="graphml")
        self.assertTrue(os.path.exists(filepath))

        # Clear graph by creating a new repo and handler
        self.repo = NetworkXGraphRepository()
        self.storage = StorageHandler(self.repo)

        # Load and verify
        self.storage.load_graph(filepath, format="graphml")
        self._verify_graph_loaded()

    def test_save_load_gexf(self):
        filepath = "test_graph.gexf"
        self.storage.save_graph(filepath, format="gexf")
        self.assertTrue(os.path.exists(filepath))

        # Clear graph by creating a new repo and handler
        self.repo = NetworkXGraphRepository()
        self.storage = StorageHandler(self.repo)

        # Load and verify
        self.storage.load_graph(filepath, format="gexf")
        self._verify_graph_loaded()

    def test_save_load_json(self):
        filepath = "test_graph.json"
        self.storage.save_graph(filepath, format="json")
        self.assertTrue(os.path.exists(filepath))

        # Clear graph
        self.repo = NetworkXGraphRepository()
        self.storage = StorageHandler(self.repo)

        # Load and verify
        self.storage.load_graph(filepath, format="json")
        self._verify_graph_loaded()

    def test_save_load_pickle(self):
        filepath = "test_graph.pkl"
        self.storage.save_graph(filepath, format="pickle")
        self.assertTrue(os.path.exists(filepath))

        # Clear graph
        self.repo = NetworkXGraphRepository()
        self.storage = StorageHandler(self.repo)

        # Load and verify
        self.storage.load_graph(filepath, format="pickle")
        self._verify_graph_loaded()

if __name__ == '__main__':
    unittest.main()
