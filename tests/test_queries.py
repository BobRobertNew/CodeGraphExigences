import unittest
import pandas as pd
from graph_tool.domain.entities import Node, Edge, NodeType
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.queries import QueryHandler

class TestQueryHandler(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.query_handler = QueryHandler(self.repo)

    def test_get_total_node_count(self):
        n1 = Node(id="n1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        n2 = Node(id="n2", type=NodeType.PROJET, metadata={"name": "Proj 1"})
        self.repo.add_node(n1)
        self.repo.add_node(n2)
        count = self.query_handler.get_total_node_count()
        self.assertEqual(count, 2)

    def test_get_exigences_for_project(self):
        proj = Node(id="p1", type=NodeType.PROJET, metadata={"name": "Project A"})
        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "Exg 2"})
        self.repo.add_node(proj)
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_edge(Edge(source_id="p1", target_id="e1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="p1", target_id="e2", type="LINKED_TO"))

        exg_nodes = self.query_handler.get_exigences_for_project("Project A")
        self.assertEqual(len(exg_nodes), 2)
        count = self.query_handler.get_exigences_count_for_project("Project A")
        self.assertEqual(count, 2)

    def test_get_exigences_with_rex_for_project(self):
        proj = Node(id="p1", type=NodeType.PROJET, metadata={"name": "Project A"})
        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "Exg 2"})
        rex1 = Node(id="r1", type=NodeType.REX, metadata={"description": "REX 1"})
        self.repo.add_node(proj)
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_node(rex1)
        self.repo.add_edge(Edge(source_id="p1", target_id="e1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="p1", target_id="e2", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e1", target_id="r1", type="LINKED_TO"))

        exg_rex_nodes = self.query_handler.get_exigences_with_rex_for_project("Project A")
        self.assertEqual(len(exg_rex_nodes), 1)
        self.assertEqual(exg_rex_nodes[0].id, "e1")
        count = self.query_handler.get_exigences_count_with_rex_for_project("Project A")
        self.assertEqual(count, 1)

    def test_get_exigences_for_project_and_metier(self):
        proj = Node(id="p1", type=NodeType.PROJET, metadata={"name": "Project A"})
        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "Exg 2"})
        metier = Node(id="m1", type=NodeType.METIER, metadata={"name": "Mécanique"})
        self.repo.add_node(proj)
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_node(metier)
        self.repo.add_edge(Edge(source_id="p1", target_id="e1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="p1", target_id="e2", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e1", target_id="m1", type="LINKED_TO"))

        nodes = self.query_handler.get_exigences_for_project_and_metier("Project A", "Mécanique")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].id, "e1")
        count = self.query_handler.get_exigences_count_for_project_and_metier("Project A", "Mécanique")
        self.assertEqual(count, 1)

    def test_get_connected_nodes(self):
        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "Exg 2"})
        rex1 = Node(id="r1", type=NodeType.REX, metadata={"status": "open", "description": "REX 1"})
        rex2 = Node(id="r2", type=NodeType.REX, metadata={"status": "closed", "description": "REX 2"})
        metier1 = Node(id="m1", type=NodeType.METIER, metadata={"name": "Mec"})
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_node(rex1)
        self.repo.add_node(rex2)
        self.repo.add_node(metier1)
        self.repo.add_edge(Edge(source_id="e1", target_id="r1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e1", target_id="r2", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e2", target_id="r1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e2", target_id="m1", type="LINKED_TO"))

        count, nodes = self.query_handler.get_connected_nodes(["e1", "e2"])
        self.assertEqual(count, 3)
        count, nodes = self.query_handler.get_connected_nodes(["e1", "e2"], target_type=NodeType.REX)
        self.assertEqual(count, 2)
        count, nodes = self.query_handler.get_connected_nodes(
            ["e1", "e2"],
            target_type=NodeType.REX,
            metadata_filters={"status": "open"}
        )
        self.assertEqual(count, 1)
        self.assertEqual(nodes[0].id, "r1")

    def test_get_preuves_connection_status_for_project(self):
        # Create a graph: Project -> Exigence -> Preuve -> Document
        proj = Node(id="p1", type=NodeType.PROJET, metadata={"name": "Project A"})

        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "Exg 1"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "Exg 2"})

        # Preuves for exg1
        preuve1 = Node(id="pr1", type=NodeType.PREUVE, metadata={"description": "Preuve 1"})
        preuve2 = Node(id="pr2", type=NodeType.PREUVE, metadata={"description": "Preuve 2"})

        # Preuves for exg2
        preuve3 = Node(id="pr3", type=NodeType.PREUVE, metadata={"description": "Preuve 3"})

        # Document (only connected to pr2 and pr3)
        doc1 = Node(id="d1", type=NodeType.DOCUMENT, metadata={"name": "Doc 1"})
        doc2 = Node(id="d2", type=NodeType.DOCUMENT, metadata={"name": "Doc 2"})

        self.repo.add_node(proj)
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_node(preuve1)
        self.repo.add_node(preuve2)
        self.repo.add_node(preuve3)
        self.repo.add_node(doc1)
        self.repo.add_node(doc2)

        self.repo.add_edge(Edge(source_id="p1", target_id="e1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="p1", target_id="e2", type="LINKED_TO"))

        self.repo.add_edge(Edge(source_id="e1", target_id="pr1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e1", target_id="pr2", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="e2", target_id="pr3", type="LINKED_TO"))

        self.repo.add_edge(Edge(source_id="pr2", target_id="d1", type="LINKED_TO"))
        self.repo.add_edge(Edge(source_id="pr3", target_id="d2", type="LINKED_TO"))

        preuves_no_doc, preuves_with_doc = self.query_handler.get_preuves_connection_status_for_project("Project A")

        # pr1 has no doc. pr2 and pr3 have docs.
        self.assertEqual(len(preuves_no_doc), 1)
        self.assertEqual(preuves_no_doc[0].id, "pr1")

        self.assertEqual(len(preuves_with_doc), 2)
        with_doc_ids = {p.id for p in preuves_with_doc}
        self.assertEqual(with_doc_ids, {"pr2", "pr3"})

        # Test non-existent project
        no_doc, with_doc = self.query_handler.get_preuves_connection_status_for_project("NonExistent Project")
        self.assertEqual(no_doc, [])
        self.assertEqual(with_doc, [])

    def test_find_most_similar_exigencies(self):
        exg1 = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": "System shall run fast"})
        exg2 = Node(id="e2", type=NodeType.EXIGENCE, metadata={"description": "The system must be secure"})
        self.repo.add_node(exg1)
        self.repo.add_node(exg2)

        input_exigencies = ["System must run fast", "System must be secure", ""]

        df = self.query_handler.find_most_similar_exigencies(input_exigencies)

        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ["Input Exigence", "Best Match Exigence", "Similarity Score"])

        self.assertEqual(df.iloc[0]["Input Exigence"], "System must run fast")
        self.assertEqual(df.iloc[0]["Best Match Exigence"], "System shall run fast")
        self.assertGreaterEqual(df.iloc[0]["Similarity Score"], 70)

        self.assertEqual(df.iloc[1]["Input Exigence"], "System must be secure")
        self.assertEqual(df.iloc[1]["Best Match Exigence"], "The system must be secure")
        self.assertGreaterEqual(df.iloc[1]["Similarity Score"], 70)

        self.assertEqual(df.iloc[2]["Input Exigence"], "")
        self.assertTrue(pd.isna(df.iloc[2]["Best Match Exigence"]))
        self.assertTrue(pd.isna(df.iloc[2]["Similarity Score"]))

    def test_get_exigencies_with_multiple_sous_articles(self):
        exg1 = Node(id="EXG1", type=NodeType.EXIGENCE, metadata={"description": "Exigence 1"})
        exg2 = Node(id="EXG2", type=NodeType.EXIGENCE, metadata={"description": "Exigence 2"})
        sart1 = Node(id="SART1", type=NodeType.SOUS_ARTICLE, metadata={"name": "Sous Article 1"})
        sart2 = Node(id="SART2", type=NodeType.SOUS_ARTICLE, metadata={"name": "Sous Article 2"})
        sart3 = Node(id="SART3", type=NodeType.SOUS_ARTICLE, metadata={"name": "Sous Article 3"})

        self.repo.add_node(exg1)
        self.repo.add_node(exg2)
        self.repo.add_node(sart1)
        self.repo.add_node(sart2)
        self.repo.add_node(sart3)
        self.repo.add_edge(Edge("EXG1", "SART1"))
        self.repo.add_edge(Edge("EXG1", "SART2"))
        self.repo.add_edge(Edge("EXG2", "SART3"))

        res = self.query_handler.get_exigencies_with_multiple_sous_articles()
        self.assertEqual(len(res), 1)
        self.assertIn("Exigence 1", res)
        self.assertCountEqual(res["Exigence 1"], ["Sous Article 1", "Sous Article 2"])

    def test_get_sous_articles_with_multiple_articles(self):
        sart1 = Node(id="SART1", type=NodeType.SOUS_ARTICLE, metadata={"name": "Sous Article 1"})
        sart2 = Node(id="SART2", type=NodeType.SOUS_ARTICLE, metadata={"name": "Sous Article 2"})
        art1 = Node(id="ART1", type=NodeType.ARTICLE, metadata={"name": "Article 1"})
        art2 = Node(id="ART2", type=NodeType.ARTICLE, metadata={"name": "Article 2"})
        art3 = Node(id="ART3", type=NodeType.ARTICLE, metadata={"name": "Article 3"})

        self.repo.add_node(sart1)
        self.repo.add_node(sart2)
        self.repo.add_node(art1)
        self.repo.add_node(art2)
        self.repo.add_node(art3)
        self.repo.add_edge(Edge("ART1", "SART1"))
        self.repo.add_edge(Edge("ART2", "SART1"))
        self.repo.add_edge(Edge("ART3", "SART2"))

        res = self.query_handler.get_sous_articles_with_multiple_articles()
        self.assertEqual(len(res), 1)
        self.assertIn("Sous Article 1", res)
        self.assertCountEqual(res["Sous Article 1"], ["Article 1", "Article 2"])

    def test_export_dict_to_excel(self):
        import os
        filepath = "test_export.xlsx"
        data = {"Key1": ["Val1", "Val2"], "Key2": ["Val3"]}

        self.query_handler.export_dict_to_excel(data, filepath, "MyKey", "MyValues")

        self.assertTrue(os.path.exists(filepath))
        df = pd.read_excel(filepath)
        self.assertEqual(list(df.columns), ["MyKey", "MyValues"])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["MyKey"], "Key1")
        self.assertEqual(df.iloc[0]["MyValues"], "Val1, Val2")
        self.assertEqual(df.iloc[1]["MyKey"], "Key2")
        self.assertEqual(df.iloc[1]["MyValues"], "Val3")

        os.remove(filepath)
    def test_complete_pivot_excel_with_graph_info(self):
        exg_text = "exigence 1"
        exg = Node(id="e1", type=NodeType.EXIGENCE, metadata={"description": exg_text})
        phase_etude = Node(id="ph1", type=NodeType.PHASE_PROJET, metadata={"name": "Etude"})
        metier_gc = Node(id="m1", type=NodeType.METIER, metadata={"name": "Génie Civil"})
        preuve = Node(id="prv1", type=NodeType.PREUVE, metadata={"description": "My Preuve GC"})
        doc = Node(id="d1", type=NodeType.DOCUMENT, metadata={"name": "Doc123"})

        self.repo.add_node(exg)
        self.repo.add_node(phase_etude)
        self.repo.add_node(metier_gc)
        self.repo.add_node(preuve)
        self.repo.add_node(doc)

        self.repo.add_edge(Edge(exg.id, phase_etude.id))
        self.repo.add_edge(Edge(exg.id, preuve.id))
        self.repo.add_edge(Edge(preuve.id, metier_gc.id))
        self.repo.add_edge(Edge(preuve.id, doc.id))

        df = pd.DataFrame({
            "Exigences": [exg_text],
            "Phase Etude": [""],
            "Conception": [""],
            "Génie Civil_Concerné": [""],
            "Génie Civil_Preuve de conformité": [""],
            "Génie Civil_Reference GED PC": [""]
        })

        df_out = self.query_handler.complete_pivot_excel_with_graph_info(df)

        self.assertEqual(df_out.at[0, "Phase Etude"], "X")
        self.assertEqual(df_out.at[0, "Conception"], "")
        self.assertEqual(df_out.at[0, "Génie Civil_Concerné"], "X")
        self.assertEqual(df_out.at[0, "Génie Civil_Preuve de conformité"], "My Preuve GC")
        self.assertEqual(df_out.at[0, "Génie Civil_Reference GED PC"], "Doc123")

    def test_transform_to_2row_header(self):
        df = pd.DataFrame({
            "Data_Source File": ["val1"],
            "Data": ["val2"],
            "Article": ["val3"],
            "Génie Civil_Concerné": ["val4"],
            "Génie Civil_Preuve de conformité": ["val5"],
            "Unknown Column": ["val6"]
        })

        df_out = self.query_handler.transform_to_2row_header(df)

        expected_cols = pd.MultiIndex.from_tuples([
            ("Data", "Source File"),
            ("Data", "Line"),
            ("Article", "Unnamed"),
            ("Génie Civil", "Concerné"),
            ("Génie Civil", "Preuve de conformité"),
            ("Unknown Column", "Unnamed")
        ])

        pd.testing.assert_index_equal(df_out.columns, expected_cols)

if __name__ == '__main__':
    unittest.main()

    def test_complete_excel_with_graph_info_additions(self):
        # Setting up nodes
        exg = Node(id="exg_mock", type=NodeType.EXIGENCE, metadata={"description": "Mock Exigence"})
        ph1 = Node(id="ph_1", type=NodeType.PHASE_PROJET, metadata={"name": "Realisation"})
        ph2 = Node(id="ph_2", type=NodeType.PHASE_PROJET, metadata={"name": "Conception"})
        met1 = Node(id="met_1", type=NodeType.METIER, metadata={"name": "GC"})
        prv1 = Node(id="prv_1", type=NodeType.PREUVE, metadata={"description": "Preuve A"})
        prv2 = Node(id="prv_2", type=NodeType.PREUVE, metadata={"description": "Preuve B"})

        for n in [exg, ph1, ph2, met1, prv1, prv2]:
            self.repo.add_node(n)

        # Edges for Exigence
        self.repo.add_edge(Edge(exg.id, ph1.id))
        self.repo.add_edge(Edge(exg.id, ph2.id))
        self.repo.add_edge(Edge(exg.id, met1.id))
        self.repo.add_edge(Edge(exg.id, prv1.id))
        self.repo.add_edge(Edge(exg.id, prv2.id))

        # Edges for Preuves
        # Preuve 1 is linked to GC and Realisation
        self.repo.add_edge(Edge(prv1.id, ph1.id))
        self.repo.add_edge(Edge(prv1.id, met1.id))

        # Preuve 2 is linked to GC and Conception
        self.repo.add_edge(Edge(prv2.id, ph2.id))
        self.repo.add_edge(Edge(prv2.id, met1.id))

        df = pd.DataFrame([
            {"Exigences": "Mock Exigence"},
            {"Exigences": "Unknown Exigence"}
        ])

        df_res = self.query_handler.complete_excel_with_graph_info(df)

        # Verify columns exist
        self.assertIn("Realisation", df_res.columns)
        self.assertIn("Conception", df_res.columns)
        self.assertIn("GC_Concerné", df_res.columns)
        self.assertIn("GC_Preuve de conformité", df_res.columns)

        # Verify values for "Mock Exigence"
        self.assertEqual(df_res.loc[0, "Realisation"], "X")
        self.assertEqual(df_res.loc[0, "Conception"], "X")
        self.assertEqual(df_res.loc[0, "GC_Concerné"], "X")

        expected_preuves = "Phase Realisation : Preuve A\nPhase Conception : Preuve B"
        # The order of phase proofs might differ depending on how get_neighbors returns them
        res_preuves = df_res.loc[0, "GC_Preuve de conformité"]
        self.assertIn("Phase Realisation : Preuve A", res_preuves)
        self.assertIn("Phase Conception : Preuve B", res_preuves)
        self.assertEqual(len(res_preuves.split("\n")), 2)

        # Verify values for "Unknown Exigence"
        self.assertEqual(df_res.loc[1, "Realisation"], "")
        self.assertEqual(df_res.loc[1, "Conception"], "")
        self.assertEqual(df_res.loc[1, "GC_Concerné"], "")
        self.assertEqual(df_res.loc[1, "GC_Preuve de conformité"], "")
