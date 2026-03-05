"""
Unit tests for SiGML Generator (Phase 5).
"""
import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

from src.sigml.generator import SiGMLGenerator
from src.nlp.dataclasses import GlossPhrase


class TestSiGMLGenerator(unittest.TestCase):
    @patch('src.sigml.generator.GlossRetriever')
    def test_generate_xml(self, MockRetriever):
        # Setup mock
        mock_retriever = MockRetriever.return_value
        mock_retriever.get_hamnosys.side_effect = lambda g: f"ham_{g}" if g in [
            "HELLO", "WORLD"] else None

        generator = SiGMLGenerator()

        # Input phrase
        phrase = GlossPhrase(
            glosses=["HELLO", "WORLD"], original_text="Hello world")

        # Generate
        output = generator.generate(phrase)

        # Verify output structure
        self.assertIn("<sigml>", output.sigml_xml)
        self.assertIn('gloss="HELLO"', output.sigml_xml)
        self.assertIn(">ham_HELLO<", output.sigml_xml)
        self.assertIn('gloss="WORLD"', output.sigml_xml)
        self.assertIn(">ham_WORLD<", output.sigml_xml)

        # Verify valid glosses list
        self.assertEqual(output.glosses, ["HELLO", "WORLD"])

    @patch('src.sigml.generator.GlossRetriever')
    def test_missing_gloss(self, MockRetriever):
        # Setup mock - WORLD is missing
        mock_retriever = MockRetriever.return_value
        mock_retriever.get_hamnosys.side_effect = lambda g: f"ham_{g}" if g == "HELLO" else None

        generator = SiGMLGenerator()
        phrase = GlossPhrase(
            glosses=["HELLO", "UNKNOWN"], original_text="Hello unknown")

        output = generator.generate(phrase)

        # Should contain HELLO but not UNKNOWN
        self.assertIn('gloss="HELLO"', output.sigml_xml)
        self.assertNotIn('gloss="UNKNOWN"', output.sigml_xml)
        self.assertEqual(output.glosses, ["HELLO"])


if __name__ == '__main__':
    unittest.main()
