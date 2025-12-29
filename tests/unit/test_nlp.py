"""
Unit tests for NLP Engine (Phase 4).
"""
import unittest
from unittest.mock import MagicMock, patch
from src.nlp.text_processor import TextProcessor
from src.nlp.grammar_transformer import GrammarTransformer
from src.nlp.gloss_mapper import GlossMapper
from src.nlp.dataclasses import ProcessedText

class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()

    def test_process_simple_sentence(self):
        text = "The cat is eating."
        result = self.processor.process(text)
        
        # "The" and "is" might be removed or kept depending on logic, 
        # but TextProcessor keeps them as tokens, GrammarTransformer removes them.
        # TextProcessor removes punctuation.
        self.assertIn("cat", result.tokens)
        self.assertIn("eating", result.tokens)
        self.assertEqual(result.original_text, text)
        
    def test_lemmatization(self):
        text = "cats are running"
        result = self.processor.process(text)
        # cats -> cat, running -> run (if verb)
        # Note: "are" might be tagged as VBP, running as VBG.
        # Lemmatizer should handle "cats" -> "cat"
        self.assertIn("cat", result.tokens)

class TestGrammarTransformer(unittest.TestCase):
    def setUp(self):
        self.transformer = GrammarTransformer()

    def test_svo_to_sov(self):
        # I eat apple -> I APPLE EAT
        tokens = ["i", "eat", "apple"]
        # Mock tags: i (PRP), eat (VBP), apple (NN)
        tagged = [("i", "PRP"), ("eat", "VBP"), ("apple", "NN")]
        
        processed = ProcessedText(tokens, tagged, "I eat apple")
        glosses = self.transformer.transform(processed)
        
        expected = ["I", "APPLE", "EAT"]
        self.assertEqual(glosses, expected)

    def test_question_word_movement(self):
        # What is your name -> YOUR NAME WHAT
        # "is" is stopword
        tokens = ["what", "is", "your", "name"]
        tagged = [("what", "WP"), ("is", "VBZ"), ("your", "PRP$"), ("name", "NN")]
        
        processed = ProcessedText(tokens, tagged, "What is your name")
        glosses = self.transformer.transform(processed)
        
        # "what" moves to end
        self.assertEqual(glosses[-1], "WHAT")
        self.assertIn("NAME", glosses)

class TestGlossMapper(unittest.TestCase):
    @patch('src.nlp.gloss_mapper.GlossRetriever')
    def test_pipeline_flow(self, MockRetriever):
        # Setup mock
        mock_retriever_instance = MockRetriever.return_value
        # Mock get_hamnosys to return True (found) for "HELLO", None for "XYZ"
        def side_effect(gloss):
            if gloss == "HELLO":
                return "hamnosys_string"
            return None
        mock_retriever_instance.get_hamnosys.side_effect = side_effect

        mapper = GlossMapper()
        
        # Test 1: Known word
        result = mapper.process("Hello")
        self.assertIn("HELLO", result.glosses)
        
        # Test 2: Unknown word (Fingerspelling)
        # "XYZ" -> X, Y, Z
        result = mapper.process("xyz")
        self.assertEqual(result.glosses, ["X", "Y", "Z"])

if __name__ == '__main__':
    unittest.main()
