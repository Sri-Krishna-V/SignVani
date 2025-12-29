"""
Grammar Transformer

Converts English grammatical structure (SVO) to Indian Sign Language structure (SOV).
Rule-based transformation using POS tags.
"""

import logging
import time
from typing import List, Tuple

from src.nlp.dataclasses import ProcessedText

logger = logging.getLogger(__name__)


class GrammarTransformer:
    """
    Rule-based SVO -> SOV transformer for ISL.
    """

    # Words to ignore in ISL (articles, auxiliary verbs)
    STOPWORDS = {
        'a', 'an', 'the', 
        'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
        'to', 'of', 'for', 'with', 'by', 'at', 'in', 'on'
    }

    # Question words to move to end
    QUESTION_WORDS = {
        'what', 'where', 'when', 'who', 'why', 'how', 'which', 'whose', 'whom'
    }

    # Time words to move to start (simple list)
    TIME_WORDS = {
        'today', 'tomorrow', 'yesterday', 'now', 'later', 'morning', 'evening', 'night'
    }

    # Negation words
    NEGATION_WORDS = {'no', 'not', 'never', "n't"}

    def transform(self, processed_text: ProcessedText) -> List[str]:
        """
        Transform processed English text to ISL gloss sequence.

        Rules applied:
        1. Remove articles and auxiliary verbs
        2. Identify Subject, Verb, Object
        3. Reorder to Time + Subject + Object + Verb + Negation + Question
        4. Convert to uppercase glosses

        Args:
            processed_text: Tokenized and tagged text

        Returns:
            List of ISL gloss strings.
        """
        start_time = time.time()
        
        tokens = processed_text.tokens
        tags = processed_text.tagged_tokens

        if not tokens:
            return []

        # 1. Filter and Classify
        subjects = []
        verbs = []
        objects = []
        time_markers = []
        question_markers = []
        negations = []
        adjectives = [] # To keep with nouns if possible, but for now simple list
        others = []

        # Simple state machine
        # 0: Pre-verb (Subject), 1: Verb found, 2: Post-verb (Object)
        state = 0 

        for word, tag in tags:
            word_lower = word.lower()

            # Skip stopwords
            if word_lower in self.STOPWORDS:
                continue

            # Categorize special words
            if word_lower in self.TIME_WORDS:
                time_markers.append(word)
                continue
            
            if word_lower in self.QUESTION_WORDS:
                question_markers.append(word)
                continue

            if word_lower in self.NEGATION_WORDS:
                negations.append(word)
                continue

            # POS based classification
            is_verb = tag.startswith('VB')
            is_noun = tag.startswith('NN') or tag.startswith('PR')
            is_adj = tag.startswith('JJ')

            if is_verb:
                verbs.append(word)
                state = 1 # Verb found, switch to Object territory
            elif state == 0:
                # Before verb -> Subject
                subjects.append(word)
            else:
                # After verb -> Object
                objects.append(word)

        # 2. Construct ISL Sentence Structure
        # Order: Time + Subject + Object + Verb + Negation + Question
        
        isl_sequence = []
        
        isl_sequence.extend(time_markers)
        isl_sequence.extend(subjects)
        isl_sequence.extend(objects)
        isl_sequence.extend(verbs)
        isl_sequence.extend(negations)
        isl_sequence.extend(question_markers)

        # 3. Convert to Glosses (Uppercase)
        glosses = [word.upper() for word in isl_sequence]

        transform_time = (time.time() - start_time) * 1000
        logger.debug(f"Grammar transformation took {transform_time:.2f}ms: {glosses}")

        return glosses
