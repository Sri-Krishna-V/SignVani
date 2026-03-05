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
        glosses, meta = self.transformer.transform(processed)

        expected = ["I", "APPLE", "EAT"]
        self.assertEqual(glosses, expected)
        self.assertIsNone(meta.tense)

    def test_question_word_movement(self):
        # What is your name -> YOUR NAME WHAT
        # "is" is stopword
        tokens = ["what", "is", "your", "name"]
        tagged = [("what", "WP"), ("is", "VBZ"),
                  ("your", "PRP$"), ("name", "NN")]

        processed = ProcessedText(tokens, tagged, "What is your name")
        glosses, meta = self.transformer.transform(processed)

        # "what" moves to end
        self.assertEqual(glosses[-1], "WHAT")
        self.assertIn("NAME", glosses)


class TestTenseDetection(unittest.TestCase):
    """Phase 1 — tense marker injection tests."""

    def setUp(self):
        self.transformer = GrammarTransformer()

    def _make(self, tagged):
        tokens = [w for w, _ in tagged]
        return ProcessedText(tokens, tagged, ' '.join(tokens))

    def test_past_tense_auxiliary(self):
        # "I was eating" — 'was' triggers PAST, dropped from output
        tagged = [("i", "PRP"), ("was", "VBD"), ("eating", "VBG")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertEqual(meta.tense, "PAST")
        self.assertIn("PAST", glosses)
        self.assertEqual(glosses[0], "PAST")
        self.assertNotIn("WAS", glosses)

    def test_past_tense_verb_morphology(self):
        # "I went to school" — no auxiliary, VBD verb triggers PAST
        tagged = [("i", "PRP"), ("go", "VBD"), ("school", "NN")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertEqual(meta.tense, "PAST")
        self.assertEqual(glosses[0], "PAST")
        self.assertIn("I", glosses)
        self.assertIn("SCHOOL", glosses)
        self.assertIn("GO", glosses)

    def test_future_tense(self):
        # "I will go to market" — 'will' triggers FUTURE
        tagged = [("i", "PRP"), ("will", "MD"), ("go", "VB"), ("market", "NN")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertEqual(meta.tense, "FUTURE")
        self.assertEqual(glosses[0], "FUTURE")
        self.assertNotIn("WILL", glosses)
        self.assertIn("GO", glosses)
        self.assertIn("MARKET", glosses)

    def test_present_tense_no_marker(self):
        # "I eat rice" — no tense marker should appear
        tagged = [("i", "PRP"), ("eat", "VBP"), ("rice", "NN")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertIsNone(meta.tense)
        self.assertNotIn("PAST", glosses)
        self.assertNotIn("FUTURE", glosses)
        self.assertEqual(glosses, ["I", "RICE", "EAT"])

    def test_tense_with_time_word(self):
        # "Yesterday I was playing" — "yesterday" encodes past tense on its own,
        # so the explicit PAST marker is suppressed (ISL convention: time words
        # that already imply tense make a separate tense marker redundant).
        # Expected: YESTERDAY I PLAY  (no PAST prefix)
        tagged = [("yesterday", "RB"), ("i", "PRP"),
                  ("was", "VBD"), ("play", "VBG")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertEqual(meta.tense, "PAST")
        self.assertEqual(glosses[0], "YESTERDAY")
        self.assertNotIn("PAST", glosses)


class TestNegation(unittest.TestCase):
    """Phase 2 — contraction expansion and negation ordering tests."""

    def setUp(self):
        self.processor = TextProcessor()
        self.transformer = GrammarTransformer()

    def _make(self, tagged):
        tokens = [w for w, _ in tagged]
        return ProcessedText(tokens, tagged, ' '.join(tokens))

    def test_contraction_expansion(self):
        # "I don't like cats" — contraction must be expanded before tokenisation
        result = self.processor.process("I don't like cats")
        # After expansion: "do not" — 'not' should appear, raw "n't" must not
        self.assertIn("not", result.tokens)
        self.assertNotIn("n't", result.tokens)
        self.assertIn("like", result.tokens)
        self.assertIn("cat", result.tokens)  # lemmatized

    def test_negation_at_end(self):
        # "I do not eat meat" (post-expansion of "I don't eat meat")
        # Negation (NOT) must be the final gloss; is_negated must be True
        tagged = [("i", "PRP"), ("do", "VBP"), ("not", "RB"),
                  ("eat", "VBP"), ("meat", "NN")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertTrue(meta.is_negated)
        self.assertEqual(glosses[-1], "NOT")

    def test_never(self):
        # "I never go" — single NEVER kept as-is (not collapsed to NOT), placed at end
        tagged = [("i", "PRP"), ("never", "RB"), ("go", "VBP")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertTrue(meta.is_negated)
        self.assertEqual(glosses[-1], "NEVER")
        self.assertNotIn("NOT", glosses)

    def test_double_negation_collapsed(self):
        # Multiple negation words must collapse to a single NOT
        tagged = [("i", "PRP"), ("not", "RB"), ("never", "RB"), ("go", "VBP")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertTrue(meta.is_negated)
        self.assertEqual(glosses.count("NOT"), 1)
        self.assertNotIn("NEVER", glosses)

    def test_negative_question(self):
        # "Do not you like it?" (expanded "Don't you like it?")
        # NOT must come after any question content — ISL convention
        tagged = [("do", "VBP"), ("not", "RB"), ("you", "PRP"),
                  ("like", "VBP"), ("it", "PRP")]
        glosses, meta = self.transformer.transform(self._make(tagged))
        self.assertTrue(meta.is_negated)
        self.assertEqual(glosses[-1], "NOT")


class TestQuestionTypes(unittest.TestCase):
    """Phase 3 — WH-question and yes/no-question detection tests."""

    def setUp(self):
        self.transformer = GrammarTransformer()

    def _make(self, tagged, ends_with_question: bool = False):
        tokens = [w for w, _ in tagged]
        return ProcessedText(tokens, tagged, ' '.join(tokens),
                             ends_with_question=ends_with_question)

    def test_wh_question(self):
        # "What is your name?" — WH-word present → question_type=WH, WHAT at end
        tagged = [("what", "WP"), ("is", "VBZ"),
                  ("your", "PRP$"), ("name", "NN")]
        glosses, meta = self.transformer.transform(
            self._make(tagged, ends_with_question=True))
        self.assertEqual(meta.question_type, "WH")
        self.assertEqual(glosses[-1], "WHAT")
        self.assertIn("NAME", glosses)

    def test_yn_question(self):
        # "Do you like coffee?" — no WH-word, ends with ? → question_type=YES_NO
        # "do" is a stopword-role verb here; output should be SOV: YOU COFFEE LIKE
        tagged = [("do", "VBP"), ("you", "PRP"),
                  ("like", "VBP"), ("coffee", "NN")]
        glosses, meta = self.transformer.transform(
            self._make(tagged, ends_with_question=True))
        self.assertEqual(meta.question_type, "YES_NO")
        self.assertIn("YOU", glosses)
        self.assertIn("COFFEE", glosses)
        self.assertIn("LIKE", glosses)

    def test_statement_no_question(self):
        # "I like coffee" — plain statement, no question
        tagged = [("i", "PRP"), ("like", "VBP"), ("coffee", "NN")]
        glosses, meta = self.transformer.transform(
            self._make(tagged, ends_with_question=False))
        self.assertIsNone(meta.question_type)

    def test_yn_question_with_future(self):
        # "Will you come tomorrow?" — FUTURE tense + YES_NO question
        tagged = [("will", "MD"), ("you", "PRP"),
                  ("come", "VB"), ("tomorrow", "NN")]
        glosses, meta = self.transformer.transform(
            self._make(tagged, ends_with_question=True))
        self.assertEqual(meta.question_type, "YES_NO")
        self.assertEqual(meta.tense, "FUTURE")
        self.assertNotIn("WILL", glosses)

    def test_ends_with_question_flag_via_text_processor(self):
        # Full integration: processor must set ends_with_question=True for '?'
        from src.nlp.text_processor import TextProcessor
        processor = TextProcessor()
        result = processor.process("Do you like coffee?")
        self.assertTrue(result.ends_with_question)

    def test_no_question_flag_for_statement(self):
        # No '?' → flag must be False
        from src.nlp.text_processor import TextProcessor
        processor = TextProcessor()
        result = processor.process("I like coffee.")
        self.assertFalse(result.ends_with_question)


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
