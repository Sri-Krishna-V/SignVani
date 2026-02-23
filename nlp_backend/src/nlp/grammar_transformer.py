"""
Grammar Transformer

Converts English grammatical structure (SVO) to Indian Sign Language structure (SOV).
Rule-based transformation using POS tags.
"""

import logging
import time
from typing import List, Tuple

from src.nlp.dataclasses import GrammarMetadata, ProcessedText

logger = logging.getLogger(__name__)


class GrammarTransformer:
    """
    Rule-based SVO -> SOV transformer for ISL.
    """

    # Words to ignore in ISL (articles, present-tense copulas that carry no tense info)
    STOPWORDS = {
        'a', 'an', 'the',
        'is', 'am', 'are', 'be', 'being',
        'to', 'of', 'for', 'with', 'by', 'at', 'in', 'on'
    }

    # Past-tense auxiliaries — trigger PAST marker, then suppressed from output
    PAST_AUXILIARIES = {'was', 'were', 'been', 'did'}

    # Future auxiliaries — trigger FUTURE marker, then suppressed from output
    FUTURE_AUXILIARIES = {'will', 'shall'}

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

    # Auxiliaries that open a yes/no-question when sentence ends with '?'
    YES_NO_AUX = {
        'do', 'does', 'did',
        'is', 'are', 'am', 'was', 'were',
        'can', 'could', 'will', 'would', 'shall', 'should',
        'have', 'has', 'had',
    }

    def transform(self, processed_text: ProcessedText) -> Tuple[List[str], GrammarMetadata]:
        """
        Transform processed English text to ISL gloss sequence.

        Rules applied:
        1. Remove articles and present-tense copulas (stopwords)
        2. Detect tense from past/future auxiliaries and verb morphology (VBD/VBN)
        3. Identify Subject, Verb, Object
        4. Reorder to [Tense] + Time + Subject + Object + Verb + Question + Negation
           (ISL convention: negation is the final sentence modifier)
        5. Collapse multiple negation words to a single NOT
        6. Detect question type: WH (question word present) or YES_NO (ends with '?')
        7. Convert to uppercase glosses

        Args:
            processed_text: Tokenized and tagged text

        Returns:
            Tuple of (ISL gloss list, GrammarMetadata with tense/negation/question annotations).
        """
        start_time = time.time()

        tokens = processed_text.tokens
        tags = processed_text.tagged_tokens

        if not tokens:
            return [], GrammarMetadata()

        # 1. Filter and Classify
        subjects = []
        verbs = []
        objects = []
        time_markers = []
        question_markers = []
        negations = []
        adjectives = []  # To keep with nouns if possible, but for now simple list
        others = []

        # Tense detection state
        detected_tense: str = None

        # Simple state machine
        # 0: Pre-verb (Subject), 1: Verb found, 2: Post-verb (Object)
        state = 0

        for word, tag in tags:
            word_lower = word.lower()

            # --- Tense auxiliaries (consume without emitting into output) ---
            if word_lower in self.PAST_AUXILIARIES:
                detected_tense = 'PAST'
                continue

            if word_lower in self.FUTURE_AUXILIARIES:
                detected_tense = 'FUTURE'
                continue

            # Skip remaining stopwords
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
                # Detect past tense from verb morphology when no auxiliary found
                # VBD = past tense verb ("went"), VBN = past participle ("eaten")
                if detected_tense is None and tag in ('VBD', 'VBN'):
                    detected_tense = 'PAST'
                verbs.append(word)
                state = 1  # Verb found, switch to Object territory
            elif state == 0:
                # Before verb -> Subject
                subjects.append(word)
            else:
                # After verb -> Object
                objects.append(word)

        # 2. Construct ISL Sentence Structure
        # Order: [Tense marker] + Time + Subject + Object + Verb + Question + Negation
        # (negation last — ISL convention for sentential negation)

        # Record whether sentence is negated before any deduplication
        is_negated = bool(negations)

        # Collapse multiple negation words to a single NOT (avoid double negation)
        if len(negations) > 1:
            negations = ['not']

        isl_sequence = []

        if detected_tense:
            isl_sequence.append(detected_tense)
        isl_sequence.extend(time_markers)
        isl_sequence.extend(subjects)
        isl_sequence.extend(objects)
        isl_sequence.extend(verbs)
        isl_sequence.extend(question_markers)
        isl_sequence.extend(negations)

        # 3. Convert to Glosses (Uppercase)
        glosses = [word.upper() for word in isl_sequence]

        # 4. Detect question type
        if question_markers:
            detected_question_type = 'WH'
        elif getattr(processed_text, 'ends_with_question', False):
            detected_question_type = 'YES_NO'  # question mark alone is sufficient signal
        else:
            detected_question_type = None

        metadata = GrammarMetadata(
            tense=detected_tense,
            is_negated=is_negated,
            question_type=detected_question_type,
        )

        transform_time = (time.time() - start_time) * 1000
        logger.debug(
            f"Grammar transformation took {transform_time:.2f}ms: {glosses} "
            f"| tense={detected_tense} | question_type={detected_question_type}")

        return glosses, metadata
