import unittest
import pandas as pd
from graph_tool.infrastructure.data_loader import extract_document_preuve_pairs

class TestExtractDocumentPreuvePairs(unittest.TestCase):
    def test_extract_simple_format(self):
        df = pd.DataFrame({
            'Documents': ['Doc1', 'Doc2', ''],
            'Preuves': ['Prv1', 'Prv2', 'Prv3'],
            'Other': ['a', 'b', 'c']
        })
        result = extract_document_preuve_pairs(df)
        self.assertEqual(len(result), 2)
        self.assertListEqual(list(result.columns), ['Document', 'Preuve'])

        pairs = set(zip(result['Document'], result['Preuve']))
        self.assertIn(('Doc1', 'Prv1'), pairs)
        self.assertIn(('Doc2', 'Prv2'), pairs)
        self.assertNotIn(('', 'Prv3'), pairs)

    def test_extract_2row_header_format(self):
        df = pd.DataFrame({
            'Elec_Reference GED PC': ['Doc1', 'Doc3'],
            'Elec_Preuve de conformité': ['Prv1', 'Prv3'],
            'Meca_Reference GED PC': ['Doc2', ''],
            'Meca_Preuve de conformité': ['Prv2', 'Prv4'],
            'Unrelated': ['x', 'y']
        })
        result = extract_document_preuve_pairs(df)
        self.assertEqual(len(result), 3)
        self.assertListEqual(list(result.columns), ['Document', 'Preuve'])

        pairs = set(zip(result['Document'], result['Preuve']))
        self.assertIn(('Doc1', 'Prv1'), pairs)
        self.assertIn(('Doc3', 'Prv3'), pairs)
        self.assertIn(('Doc2', 'Prv2'), pairs)

    def test_extract_custom_columns(self):
        df = pd.DataFrame({
            'Documents': ['Doc1'],
            'Preuves': ['Prv1']
        })
        result = extract_document_preuve_pairs(df, doc_col='D', preuve_col='P')
        self.assertListEqual(list(result.columns), ['D', 'P'])
        self.assertEqual(result.iloc[0]['D'], 'Doc1')
        self.assertEqual(result.iloc[0]['P'], 'Prv1')
