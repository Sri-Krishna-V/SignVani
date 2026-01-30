"""
Text Processor

Handles tokenization, lemmatization, and Part-of-Speech (POS) tagging.
Optimized for low-latency processing on Raspberry Pi 4.
"""

import logging
import string
import time
from typing import List, Tuple

import nltk
from nltk.stem import WordNetLemmatizer

from config.settings import NLPConfig
from src.nlp.dataclasses import ProcessedText

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Lightweight NLP text processor using NLTK.
    """

    def __init__(self):
        """Initialize text processor and load NLTK resources."""
        self._ensure_nltk_resources()
        self.lemmatizer = WordNetLemmatizer() if NLPConfig.LEMMATIZATION_ENABLED else None

        # Pre-compile punctuation map for faster removal
        self.punctuation_map = str.maketrans('', '', string.punctuation)

    def _ensure_nltk_resources(self):
        """Ensure required NLTK data is available."""
        # Add custom path for NLTK data
        nltk.data.path.insert(0, NLPConfig.NLTK_DATA_PATH)

        try:
            # Check if resources exist, if not they should have been downloaded by setup_models.py
            for resource in NLPConfig.NLTK_RESOURCES:
                found = False
                # Try different NLTK data paths
                search_paths = [
                    f'tokenizers/{resource}',
                    f'corpora/{resource}',
                    f'taggers/{resource}',
                ]
                for path in search_paths:
                    try:
                        nltk.data.find(path)
                        found = True
                        break
                    except LookupError:
                        continue

                if not found:
                    logger.warning(
                        f"NLTK resource '{resource}' not found. Attempting download...")
                    nltk.download(resource, quiet=True,
                                  download_dir=NLPConfig.NLTK_DATA_PATH)
        except Exception as e:
            logger.error(f"Failed to verify NLTK resources: {e}")

    def process(self, text: str) -> ProcessedText:
        """
        Process raw text into tokens and POS tags.

        Steps:
        1. Lowercase and clean
        2. Tokenize
        3. Remove punctuation
        4. POS Tagging
        5. Lemmatization (optional)

        Args:
            text: Raw input text (e.g., "The cat is eating.")

        Returns:
            ProcessedText object containing tokens and tags.
        """
        start_time = time.time()
        original_text = text

        # 1. Lowercase
        text = text.lower().strip()

        # 2. Tokenize
        try:
            tokens = nltk.word_tokenize(text)
        except LookupError:
            # Fallback if punkt is missing
            tokens = text.split()

        # 3. Remove punctuation and filter empty tokens
        clean_tokens = []
        for token in tokens:
            # Remove punctuation from token
            token = token.translate(self.punctuation_map)
            if token and len(token) >= NLPConfig.MIN_TOKEN_LENGTH:
                clean_tokens.append(token)

        tokens = clean_tokens

        # 4. POS Tagging
        # Uses averaged_perceptron_tagger (included in NLTK default)
        try:
            tagged_tokens = nltk.pos_tag(tokens)
        except LookupError:
            # Fallback if tagger is missing
            logger.warning("POS tagger missing, using default tags")
            tagged_tokens = [(t, 'NN') for t in tokens]

        # 5. Lemmatization
        if self.lemmatizer:
            final_tagged = []
            for token, tag in tagged_tokens:
                wordnet_tag = self._get_wordnet_pos(tag)
                if wordnet_tag:
                    lemma = self.lemmatizer.lemmatize(token, wordnet_tag)
                else:
                    lemma = self.lemmatizer.lemmatize(token)
                final_tagged.append((lemma, tag))
            tagged_tokens = final_tagged
            tokens = [t[0] for t in tagged_tokens]

        processing_time = (time.time() - start_time) * 1000
        logger.debug(f"Text processing took {processing_time:.2f}ms")

        return ProcessedText(
            tokens=tokens,
            tagged_tokens=tagged_tokens,
            original_text=original_text
        )

    def _get_wordnet_pos(self, treebank_tag):
        """Map Treebank POS tag to WordNet POS tag."""
        if treebank_tag.startswith('J'):
            return nltk.corpus.wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return nltk.corpus.wordnet.VERB
        elif treebank_tag.startswith('N'):
            return nltk.corpus.wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return nltk.corpus.wordnet.ADV
        else:
            return None
