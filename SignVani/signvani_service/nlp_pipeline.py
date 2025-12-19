"""
SignVani NLP Pipeline
Handles text processing and English to ISL Gloss conversion
"""
import logging
import time
from typing import List, Tuple, Dict

import spacy
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)


class NLPPipeline:
    """
    Natural Language Processing pipeline for converting English text 
    to Indian Sign Language (ISL) Gloss format.
    """

    def __init__(self, model_name: str = "en_core_web_sm", enable_sov: bool = True):
        """
        Initialize NLP pipeline

        Args:
            model_name: spaCy model name
            enable_sov: Enable SVO to SOV transformation
        """
        self.enable_sov = enable_sov

        # Load spaCy model
        logger.info(f"Loading spaCy model: {model_name}...")
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            from spacy.cli import download
            download(model_name)
            self.nlp = spacy.load(model_name)

        # Initialize NLTK components
        logger.info("Initializing NLTK components...")
        try:
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            logger.info("Downloading NLTK data...")
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('omw-1.4')
            nltk.download('punkt')

        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

        # Custom stop words to keep for ISL (e.g., negation)
        self.keep_words = {'not', 'no', 'never', 'what',
                           'where', 'when', 'who', 'why', 'how'}
        self.stop_words = self.stop_words - self.keep_words

        logger.info("NLP Pipeline initialized successfully")

    def process_text(self, text: str) -> Dict:
        """
        Process English text and convert to ISL Gloss

        Args:
            text: Input English text

        Returns:
            Dictionary containing original text, gloss, tokens, and metadata
        """
        start_time = time.time()

        # 1. Text Normalization
        normalized_text = text.lower().strip()
        doc = self.nlp(normalized_text)

        # 2. Tokenization & POS Tagging (handled by spaCy)

        # 3. SVO to SOV Transformation
        if self.enable_sov:
            ordered_tokens = self._convert_svo_to_sov(doc)
        else:
            ordered_tokens = [token for token in doc]

        # 4. Filtration (Stop-word removal) & Lemmatization
        processed_tokens = []
        for token in ordered_tokens:
            # Skip stop words unless they are in the keep list
            if token.text.lower() in self.stop_words and token.text.lower() not in self.keep_words:
                continue

            # Skip punctuation
            if token.is_punct:
                continue

            # Lemmatization (convert to root form)
            # Use spaCy's lemma if available, else NLTK
            lemma = token.lemma_ if token.lemma_ != "-PRON-" else token.text

            # Handle specific cases
            if lemma == "be":  # Skip 'be' verbs often
                continue

            processed_tokens.append(lemma.upper())

        # 5. Gloss Formatting
        gloss_text = " ".join(processed_tokens)

        processing_time = time.time() - start_time

        return {
            "original_text": text,
            "gloss": gloss_text,
            "tokens": processed_tokens,
            "transformation_applied": self.enable_sov,
            "processing_time": processing_time
        }

    def _convert_svo_to_sov(self, doc) -> List[spacy.tokens.Token]:
        """
        Rearrange sentence structure from Subject-Verb-Object to Subject-Object-Verb

        Args:
            doc: spaCy Doc object

        Returns:
            List of reordered tokens
        """
        # Simple heuristic for SVO -> SOV
        # Find the main verb
        verbs = [token for token in doc if token.pos_ == "VERB"]

        if not verbs:
            return list(doc)

        # Take the first main verb as the root of the action
        main_verb = verbs[0]

        # Identify Subject and Object
        subjects = []
        objects = []
        others = []

        for token in doc:
            if token == main_verb:
                continue

            # Dependency parsing checks
            if token.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass"):
                subjects.append(token)
                # Add subtree (adjectives etc attached to subject)
                # This is a simplification; a full tree traversal is better for complex sentences
            elif token.dep_ in ("dobj", "pobj", "iobj", "attr"):
                objects.append(token)
            else:
                others.append(token)

        # Construct SOV order: Subject + Others + Object + Verb
        # Note: Time markers usually go first in ISL, but we'll stick to basic SOV for now

        # We need to preserve the order of words within the subject/object phrases
        # A simple reordering of the tokens based on their role

        # Better approach: Iterate through original tokens and bucket them
        reordered = []

        # Add subjects
        for token in doc:
            if token in subjects or any(ancestor in subjects for ancestor in token.ancestors):
                if token != main_verb and token not in objects:
                    reordered.append(token)

        # Add objects
        for token in doc:
            if token in objects or any(ancestor in objects for ancestor in token.ancestors):
                if token != main_verb and token not in subjects:
                    reordered.append(token)

        # Add others (adverbs, time, place - usually place/time come early, but keeping simple)
        for token in doc:
            if token not in subjects and token not in objects and token != main_verb:
                reordered.append(token)

        # Add Verb at the end
        reordered.append(main_verb)

        # Fallback: if we lost tokens or messed up, return original
        if len(reordered) != len(doc):
            # This simple logic might miss tokens not in subtrees correctly
            # For robustness, let's just return the simple [Subj, Obj, Verb] if identified,
            # else original.

            # Alternative simple swap:
            # Find V and O, swap to O V

            return list(doc)  # Fallback to original order if complex

        return reordered

    def _simple_svo_to_sov(self, doc) -> List[spacy.tokens.Token]:
        """
        A simpler, more robust SVO to SOV reordering based on chunks
        """
        # Identify chunks
        subj = []
        verb = []
        obj = []
        rest = []

        for token in doc:
            if token.pos_ == "VERB":
                verb.append(token)
            elif token.dep_ in ("nsubj", "nsubjpass"):
                subj.append(token)
            elif token.dep_ in ("dobj", "pobj"):
                obj.append(token)
            else:
                rest.append(token)

        # ISL Structure: Time + Subject + Object + Verb + Question
        # We will approximate: Subject + Rest + Object + Verb

        # This is hard to do perfectly token-by-token without full tree traversal
        # For the prototype, we will rely on the standard order but move verbs to end

        tokens = list(doc)
        verbs = [t for t in tokens if t.pos_ == "VERB"]

        if not verbs:
            return tokens

        # Move main verbs to the end
        non_verbs = [t for t in tokens if t.pos_ != "VERB"]
        return non_verbs + verbs


if __name__ == "__main__":
    # Test NLP Pipeline
    logging.basicConfig(level=logging.INFO)

    pipeline = NLPPipeline()

    test_sentences = [
        "I am going to the market",
        "What is your name?",
        "The cat is sleeping on the mat",
        "I will help you tomorrow"
    ]

    print("\n=== NLP Pipeline Test ===")
    for sentence in test_sentences:
        result = pipeline.process_text(sentence)
        print(f"\nInput: {sentence}")
        print(f"Gloss: {result['gloss']}")
        print(f"Tokens: {result['tokens']}")
