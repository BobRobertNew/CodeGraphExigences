import pandas as pd
import unittest
from graph_tool.domain.entities import Node, NodeType
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.use_cases.extractors import LegacyExigenceExtractionStep, LinkPhaseProjetStep

class MockCmd:
    def __init__(self):
        self.nodes = []
        self.edges = []
    def add_node(self, node, owner='TestOwner'):
        if node.id not in [n.id for n in self.nodes]:
            self.nodes.append(node)
    def add_log(self, log_entry: dict):
        pass

    def add_edge(self, edge):
        self.edges.append(edge)

class MockQry:
    def __init__(self, cmd):
        self.cmd = cmd
    def find_node_by_exact_metadata(self, key, value, node_type):
        for n in self.cmd.nodes:
            if n.type == node_type and n.metadata.get(key) == value:
                return n
        return None
    def get_node(self, node_id):
        for n in self.cmd.nodes:
            if n.id == node_id:
                return n
        return None
    def find_nodes_by_type(self, node_type):
        return [n for n in self.cmd.nodes if n.type == node_type]

class TestPhaseDeduplication(unittest.TestCase):
    def setUp(self):
        self.cmd = MockCmd()
        self.qry = MockQry(self.cmd)

        self.proj_node = Node(id="PROJ-TestProj", type=NodeType.PROJET, metadata={"name": "TestProj"})
        self.cmd.add_node(self.proj_node)

    def test_legacy_extraction_normalizes_phase(self):
        df = pd.DataFrame({
            "Exigence": ["Ex1"],
            "Phase projet": ["Phase Contrat"]
        })
        step = LegacyExigenceExtractionStep()
        step.execute(df, self.proj_node, self.cmd, self.qry, owner="TestOwner")

        phases = self.qry.find_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].id, "PHASE-Contrat")
        self.assertEqual(phases[0].metadata["name"], "Contrat")

    def test_link_phase_projet_normalizes_phase(self):
        df = pd.DataFrame({
            "Exigences": ["Ex1"],
            "Phase Contrat": ["X"]
        })
        step = LinkPhaseProjetStep()
        step.execute(df, self.proj_node, self.cmd, self.qry, owner="TestOwner")

        phases = self.qry.find_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].id, "PHASE-Contrat")
        self.assertEqual(phases[0].metadata["name"], "Contrat")

    def test_deduplication_between_steps(self):
        df = pd.DataFrame({
            "Exigences": ["Ex1"],
            "Exigence": ["Ex1"],
            "Phase projet": ["Phase Contrat"],
            "Phase Contrat": ["X"]
        })

        step1 = LegacyExigenceExtractionStep()
        step1.execute(df, self.proj_node, self.cmd, self.qry, owner="TestOwner")

        step2 = LinkPhaseProjetStep()
        step2.execute(df, self.proj_node, self.cmd, self.qry, owner="TestOwner")

        phases = self.qry.find_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].id, "PHASE-Contrat")

if __name__ == "__main__":
    unittest.main()
