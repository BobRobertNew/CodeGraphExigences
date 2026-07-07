import unittest
import pandas as pd
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.domain.entities import NodeType

class TestCommandAddDocuments(unittest.TestCase):
    def setUp(self):
        self.repo = NetworkXGraphRepository()
        self.cmd = CommandHandler(self.repo, self.repo)

    def test_add_documents(self):
        df = pd.DataFrame({
            'Document': ['Doc1', 'Doc2'],
            'Preuve': ['Prv1', 'Prv2']
        })

        self.cmd.add_documents('TestProject', df)

        nodes = self.repo.get_all_nodes()
        self.assertTrue(any(n.type == NodeType.PROJET and n.metadata.get('name') == 'TestProject' for n in nodes))
        self.assertTrue(any(n.type == NodeType.DOCUMENT and n.metadata.get('name') == 'Doc1' for n in nodes))
        self.assertTrue(any(n.type == NodeType.DOCUMENT and n.metadata.get('name') == 'Doc2' for n in nodes))
        self.assertTrue(any(n.type == NodeType.PREUVE and n.metadata.get('description') == 'Prv1' for n in nodes))
        self.assertTrue(any(n.type == NodeType.PREUVE and n.metadata.get('description') == 'Prv2' for n in nodes))

        proj_node = next(n for n in nodes if n.type == NodeType.PROJET)
        doc1_node = next(n for n in nodes if n.type == NodeType.DOCUMENT and n.metadata.get('name') == 'Doc1')
        doc2_node = next(n for n in nodes if n.type == NodeType.DOCUMENT and n.metadata.get('name') == 'Doc2')
        prv1_node = next(n for n in nodes if n.type == NodeType.PREUVE and n.metadata.get('description') == 'Prv1')
        prv2_node = next(n for n in nodes if n.type == NodeType.PREUVE and n.metadata.get('description') == 'Prv2')

        edges = self.repo.get_all_edges()
        self.assertTrue(any(e.source_id == proj_node.id and e.target_id == doc1_node.id for e in edges))
        self.assertTrue(any(e.source_id == proj_node.id and e.target_id == doc2_node.id for e in edges))

        self.assertTrue(any(e.source_id == doc1_node.id and e.target_id == prv1_node.id for e in edges))
        self.assertTrue(any(e.source_id == doc2_node.id and e.target_id == prv2_node.id for e in edges))

    def test_add_documents_custom_cols(self):
        df = pd.DataFrame({
            'D': ['Doc1'],
            'P': ['Prv1']
        })
        self.cmd.add_documents('TestProject', df, doc_col='D', preuve_col='P')
        nodes = self.repo.get_all_nodes()
        self.assertTrue(any(n.type == NodeType.DOCUMENT and n.metadata.get('name') == 'Doc1' for n in nodes))
