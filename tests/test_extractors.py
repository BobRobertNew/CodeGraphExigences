import unittest
import pandas as pd
from graph_tool.domain.entities import Node, NodeType
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.extractors import (
    CreateExigenceAndArticlesStep,
    LinkMetierStep,
    LinkPhaseProjetStep
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

if __name__ == '__main__':
    unittest.main()
