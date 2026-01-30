"""
Gloss Mapper

Maps English text to Indian Sign Language (ISL) glosses.
Orchestrates the NLP pipeline: Text Processing -> Grammar Transformation -> Gloss Lookup.
"""

import logging
import time
from typing import List, Optional

from src.nlp.dataclasses import GlossPhrase, ProcessedText
from src.nlp.text_processor import TextProcessor
from src.nlp.grammar_transformer import GrammarTransformer
from src.database.retriever import GlossRetriever

logger = logging.getLogger(__name__)


class GlossMapper:
    """
    Orchestrator for the NLP pipeline.
    Converts English text to ISL GlossPhrases with HamNoSys validation.
    """

    def __init__(self, prewarm: bool = True):
        """
        Initialize NLP components.

        Args:
            prewarm: If True, pre-warm WordNet to avoid cold-start latency.
        """
        self.text_processor = TextProcessor()
        self.grammar_transformer = GrammarTransformer()
        self.retriever = GlossRetriever()

        # Pre-warm WordNet to avoid ~9s cold-start on first lemmatization
        if prewarm and self.text_processor.lemmatizer:
            logger.debug("Pre-warming WordNet lemmatizer...")
            _ = self.text_processor.lemmatizer.lemmatize("warmup")

    def process(self, text: str) -> GlossPhrase:
        """
        Convert English text to ISL GlossPhrase.

        Pipeline:
        1. Text Processing (Tokenize, Tag, Lemmatize)
        2. Grammar Transformation (SVO -> SOV)
        3. Gloss Lookup (DB check, Fuzzy match, Fingerspelling fallback)

        Args:
            text: Input English text

        Returns:
            GlossPhrase object containing ordered glosses.
        """
        start_time = time.time()

        # 1. Text Processing
        processed_text: ProcessedText = self.text_processor.process(text)

        # 2. Grammar Transformation
        raw_glosses: List[str] = self.grammar_transformer.transform(
            processed_text)

        # 3. Gloss Validation & Mapping
        final_glosses: List[str] = []

        for gloss in raw_glosses:
            # Check if gloss exists in DB (Exact or Fuzzy)
            hamnosys = self.retriever.get_hamnosys(gloss)

            if hamnosys:
                final_glosses.append(gloss)
            else:
                # Fallback: Fingerspelling
                logger.info(
                    f"Gloss '{gloss}' not found. Falling back to fingerspelling.")
                fingerspelled = self._fingerspell(gloss)
                final_glosses.extend(fingerspelled)

        total_time = (time.time() - start_time) * 1000
        logger.info(
            f"NLP Pipeline: '{text}' -> {final_glosses} ({total_time:.2f}ms)")

        return GlossPhrase(
            glosses=final_glosses,
            original_text=text
        )

    def _fingerspell(self, word: str) -> List[str]:
        """
        Convert a word to a list of character glosses.

        Args:
            word: Word to fingerspell (e.g., "RAM")

        Returns:
            List of character glosses (e.g., ["R", "A", "M"])
        """
        # Filter only alphanumeric characters
        clean_word = ''.join(filter(str.isalnum, word))
        return list(clean_word.upper())
