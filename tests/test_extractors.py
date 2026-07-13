import unittest
import pandas as pd
from graph_tool.domain.entities import Node, NodeType
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.extractors import (
    CreateExigenceAndArticlesStep,
    LinkMetierStep,
    LinkPhaseProjetStep,
    LinkExploitationStep
)
from graph_tool.infrastructure.data_loader import load_excel_with_2row_header
import os

class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.cmd_handler = CommandHandler(self.repo, self.repo)

    def test_new_extraction_pipeline(self):
        # Create dummy dataframe matching the description
        data = {
            "Article": ["Art1", "Art1", "Art2"],
            "Sous_Article": ["Sub1", "Sub2", "Sub3"],
            "Exigences": ["Exigence1", "Exigence2", "Exigence3"],
            "MétierA_Concerné": ["X", "", "X"],
            "MétierB_Concerné": ["", "X", ""],
            "Conception": ["X", "X", ""],
            "Exploitation": ["", "", "X"]
        }
        df = pd.DataFrame(data)

        steps = [
            CreateExigenceAndArticlesStep(),
            LinkMetierStep(),
            LinkPhaseProjetStep()
        ]

        self.cmd_handler.add_project_exigences(
            project_name="TestProj",
            data_source=df,
            loader=lambda x: x, # Dummy loader since we pass DF
            steps=steps
        )

        # Verify nodes created
        proj_node = self.repo.find_node_by_exact_metadata("name", "TestProj", NodeType.PROJET)
        self.assertIsNotNone(proj_node)

        exigences = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exigences), 3)

        articles = self.repo.get_nodes_by_type(NodeType.ARTICLE)
        self.assertEqual(len(articles), 2)

        sous_articles = self.repo.get_nodes_by_type(NodeType.SOUS_ARTICLE)
        self.assertEqual(len(sous_articles), 3)

        metiers = self.repo.get_nodes_by_type(NodeType.METIER)
        self.assertEqual(len(metiers), 2)

        phases = self.repo.get_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 2)

        # Verify some edges
        # We know Exigence1 is linked to Art1/Sub1, MétierA, Conception
        exg1 = [e for e in exigences if e.metadata["description"] == "Exigence1"][0]

        edges = self.repo.get_all_edges()
        target_ids = [edge.target_id for edge in edges if edge.source_id == exg1.id]

        # In our logic, Exigence is linked to Sous Article or Article
        # And we linked Exigence -> Sous Article (if present)
        # And Exigence -> Métier
        # And Exigence -> Phase
        sub1 = [s for s in sous_articles if s.metadata["name"] == "Sub1"][0]
        self.assertIn(sub1.id, target_ids)

        metier_a = [m for m in metiers if m.metadata["name"] == "MétierA"][0]
        self.assertIn(metier_a.id, target_ids)

        conception = [p for p in phases if p.metadata["name"] == "Conception"][0]
        self.assertIn(conception.id, target_ids)

    def test_load_excel_with_2row_header(self):
        # Create a dummy excel with 2 row header using pandas
        # row 0: A, A, B
        # row 1: X, Y, nan
        # Using forward fill on headers:
        # A, A, B
        # X, Y, nan  (Actually, if row 1 has nan, B will have nan)
        # We should define headers carefully.

        # The prompt says:
        # header_rows = raw.iloc[:2].ffill(axis=1)
        # If the input is:
        # A, NaN, B
        # X, Y, NaN

        df_dummy = pd.DataFrame([
            ["A", float('nan'), "B"],
            ["X", "Y", float('nan')],
            [1, 2, 3],
            [4, 5, 6]
        ])
        # ffill(axis=1) will do:
        # A, A, B
        # X, Y, Y (since ffill will propagate Y to the right)
        # So column 2 will be B_Y instead of B.
        # Let's adjust the test to match pandas ffill behavior.
        filepath = "dummy_test.xlsx"
        df_dummy.to_excel(filepath, index=False, header=False)

        try:
            df_loaded = load_excel_with_2row_header(filepath)
            self.assertEqual(list(df_loaded.columns), ["A_X", "A_Y", "B_Y"])
            self.assertEqual(len(df_loaded), 2)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_link_preuve_step(self):
        # We need an Exigence to link to
        exigence_text = "Test Exigence"
        from graph_tool.utils.text_utils import generate_short_id
        exg_id = generate_short_id("EXG", exigence_text)
        exg_node = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
        self.cmd_handler.cmd.add_node(exg_node)

        data = {
            "Exigences": [exigence_text],
            "MétierA_Concerné": ["X"],
            "MétierA_Preuve de conformité": ["Phase Etude: text 1. Phase Conception: text 2"]
        }
        df = pd.DataFrame(data)

        from graph_tool.use_cases.extractors import LinkPreuveStep
        step = LinkPreuveStep()
        step.execute(df, None, self.cmd_handler.cmd, self.cmd_handler.qry)

        preuves = self.repo.get_nodes_by_type(NodeType.PREUVE)
        self.assertEqual(len(preuves), 2)

        preuve_texts = [p.metadata["description"] for p in preuves]
        self.assertIn("text 1.", preuve_texts)
        self.assertIn("text 2", preuve_texts)

        phases = self.repo.get_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 2)
        phase_names = [p.metadata["name"] for p in phases]
        self.assertIn("Etude", phase_names)
        self.assertIn("Conception", phase_names)

        metiers = self.repo.get_nodes_by_type(NodeType.METIER)
        self.assertEqual(len(metiers), 1)
        self.assertEqual(metiers[0].metadata["name"], "MétierA")

        edges = self.repo.get_all_edges()

        # Verify connections to the specific Preuve "text 1."
        prv_text1 = [p for p in preuves if p.metadata["description"] == "text 1."][0]
        linked_to_prv = [e for e in edges if e.source_id == prv_text1.id or e.target_id == prv_text1.id]

        # Should be linked to Exigence, Metier, and Phase Projet
        self.assertEqual(len(linked_to_prv), 3)

        # In the extraction logic, edges are created with Preuve as the source or target depending on how it's implemented.
        # However, checking the edges list directly for the connected node ids is safer.
        connected_ids = [e.target_id if e.source_id == prv_text1.id else e.source_id for e in linked_to_prv]

        self.assertIn(exg_id, connected_ids)
        self.assertIn(metiers[0].id, connected_ids)

        phase_etude = [p for p in phases if p.metadata["name"] == "Etude"][0]
        self.assertIn(phase_etude.id, connected_ids)

    def test_link_exploitation_step(self):
        proj_node = Node(id="PROJ-Test", type=NodeType.PROJET, metadata={"name": "Test"})
        self.cmd_handler.cmd.add_node(proj_node)

        data = {
            "Exigences": ["Exigence1", "Exigence2", "Exigence3", "Exigence4", "Exigence5"],
            "Exploitation": ["X", "x", "", "X ", "X"],
            "Etat de Conformité": ["-", "-", "-", "-", "Something else"]
        }
        df = pd.DataFrame(data)

        step = LinkExploitationStep()
        step.execute(df, proj_node, self.cmd_handler.cmd, self.cmd_handler.qry)

        exigences = self.repo.get_nodes_by_type(NodeType.EXIGENCE)
        self.assertEqual(len(exigences), 3)
        exg_descriptions = [e.metadata["description"] for e in exigences]
        self.assertIn("Exigence1", exg_descriptions)
        self.assertIn("Exigence2", exg_descriptions)
        self.assertIn("Exigence4", exg_descriptions)

        phases = self.repo.get_nodes_by_type(NodeType.PHASE_PROJET)
        self.assertEqual(len(phases), 1)
        phase_node = phases[0]
        self.assertEqual(phase_node.metadata["name"], "Exploitation")

        edges = self.repo.get_all_edges()
        exg1 = [e for e in exigences if e.metadata["description"] == "Exigence1"][0]
        exg2 = [e for e in exigences if e.metadata["description"] == "Exigence2"][0]

        # Phase and Proj nodes are added as target_id or source_id?
        # cmd.add_edge(Edge(exg_node.id, phase_node.id)) -> source: exg, target: phase
        # Let's check both ways just in case or correct it to match how edges are appended
        target_ids_exg1 = [edge.target_id for edge in edges if edge.source_id == exg1.id]
        if not target_ids_exg1: # If not found as source, maybe it's the target
            target_ids_exg1 = [edge.source_id for edge in edges if edge.target_id == exg1.id]
        self.assertIn(phase_node.id, target_ids_exg1)

        target_ids_exg2 = [edge.target_id for edge in edges if edge.source_id == exg2.id]
        if not target_ids_exg2:
            target_ids_exg2 = [edge.source_id for edge in edges if edge.target_id == exg2.id]
        self.assertIn(phase_node.id, target_ids_exg2)

        # cmd.add_edge(Edge(proj_node.id, exg_node.id))
        target_ids_proj = [edge.target_id for edge in edges if edge.source_id == proj_node.id]
        if not target_ids_proj:
            target_ids_proj = [edge.source_id for edge in edges if edge.target_id == proj_node.id]
        self.assertIn(exg1.id, target_ids_proj)
        self.assertIn(exg2.id, target_ids_proj)


if __name__ == '__main__':
    unittest.main()
