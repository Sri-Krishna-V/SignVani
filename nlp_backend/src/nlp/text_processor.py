"""
Text Processor

Handles tokenization, lemmatization, and Part-of-Speech (POS) tagging.
Optimized for low-latency processing on Raspberry Pi 4.
"""

import logging
import re
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

    # Contraction expansion map — applied before tokenisation so that NLTK
    # POS tagger receives full-form tokens (e.g. "do not" rather than "n't").
    CONTRACTIONS = {
        "don't":    "do not",
        "doesn't":  "does not",
        "didn't":   "did not",
        "can't":    "can not",
        "won't":    "will not",
        "isn't":    "is not",
        "aren't":   "are not",
        "wasn't":   "was not",
        "weren't":  "were not",
        "haven't":  "have not",
        "hasn't":   "has not",
        "couldn't": "could not",
        "shouldn't": "should not",
        "wouldn't": "would not",
    }

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
        1. Expand contractions
        2. Replace punctuation with sentinel tokens
        3. Tokenize (on original-cased text)
        4. Filter tokens
        5. POS Tagging (on original-cased tokens — preserves accuracy for "I" etc.)
        6. Lowercase all tokens
        7. Lemmatization (optional)

        Args:
            text: Raw input text (e.g., "The cat is eating.")

        Returns:
            ProcessedText object containing tokens and tags.
        """
        start_time = time.time()
        original_text = text

        # Detect question-sentence flag before any transformation
        ends_with_question: bool = original_text.strip().endswith('?')

        # 1. Expand contractions (before lowercasing so patterns match any case)
        text = self._expand_contractions(text)

        # 2. Replace periods with special tokens before tokenization
        #    (done on original-cased text so POS tagging sees proper capitalisation)
        text = text.replace('.', ' <PERIOD> ')
        text = text.replace('?', ' <QUESTION> ')
        text = text.replace('!', ' <EXCLAMATION> ')
        text = text.replace(',', ' <COMMA> ')

        # 3. Tokenize (on original-cased text for accurate POS tagging)
        try:
            tokens = nltk.word_tokenize(text)
        except LookupError:
            # Fallback if punkt is missing
            tokens = text.split()

        # 4. Handle punctuation tokens and filter empty tokens
        clean_tokens = []
        for token in tokens:
            token_lower = token.lower()
            # Check if it's a special punctuation token (case-insensitive match)
            if token_lower in ['<period>', '<question>', '<exclamation>', '<comma>']:
                clean_tokens.append(
                    token_lower.upper().replace('<', '').replace('>', ''))
            else:
                # Remove regular punctuation from token
                token = token.translate(self.punctuation_map)
                if token and len(token) >= NLPConfig.MIN_TOKEN_LENGTH:
                    clean_tokens.append(token)

        tokens = clean_tokens

        # 5. POS Tagging on original-cased tokens.
        #    NLTK's tagger is case-sensitive: "I" is correctly tagged as PRP
        #    (personal pronoun) while lowercase "i" is often mistagged as NN,
        #    which in turn causes subsequent verbs to receive wrong tense tags.
        try:
            tagged_tokens = nltk.pos_tag(tokens)
        except LookupError:
            # Fallback if tagger is missing
            logger.warning("POS tagger missing, using default tags")
            tagged_tokens = [(t, 'NN') for t in tokens]

        # 6. Lowercase AFTER POS tagging so downstream logic uses lower-case strings
        tagged_tokens = [(token.lower(), tag) for token, tag in tagged_tokens]
        tokens = [t[0] for t in tagged_tokens]

        # 7. Lemmatization
        if self.lemmatizer:
            final_tagged = []
            for token, tag in tagged_tokens:
                # Skip lemmatization for punctuation tokens (now stored lowercase)
                if token in ['period', 'question', 'exclamation', 'comma']:
                    final_tagged.append((token, tag))
                else:
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
            original_text=original_text,
            ends_with_question=ends_with_question,
        )

    def _expand_contractions(self, text: str) -> str:
        """
        Replace common English contractions with their full forms.

        Applied on the original-cased text before lowercasing so that
        mixed-case input (e.g. "Don't") is handled correctly.

        Args:
            text: Raw input string.

        Returns:
            String with contractions replaced by full forms.
        """
        for contraction, expansion in self.CONTRACTIONS.items():
            # Use word-boundary regex, case-insensitive
            pattern = re.compile(re.escape(contraction), re.IGNORECASE)
            text = pattern.sub(expansion, text)
        return text

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
