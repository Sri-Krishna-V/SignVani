"""
SignVani Data Classes

Memory-optimized data structures using __slots__ for efficient storage.
All numerical data uses float32 to halve memory footprint on ARM processors.
"""

import time
from typing import List, Optional
import numpy as np


class AudioChunk:
    """
    Represents a chunk of audio data from the capture stream.

    Uses __slots__ to reduce memory overhead (~50% savings vs regular class).
    Forces float32 for numerical data to minimize memory on embedded systems.
    """
    __slots__ = ('data', 'timestamp', 'sample_rate')

    def __init__(self, data: np.ndarray, sample_rate: int, timestamp: float = None):
        """
        Initialize audio chunk.

        Args:
            data: Audio samples (will be converted to float32)
            sample_rate: Sample rate in Hz (e.g., 16000)
            timestamp: Unix timestamp (defaults to current time)
        """
        # Force float32 for memory efficiency
        self.data = data.astype(
            np.float32) if data.dtype != np.float32 else data
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.sample_rate = sample_rate

    @property
    def duration(self) -> float:
        """Duration of audio chunk in seconds"""
        return len(self.data) / self.sample_rate

    @property
    def num_samples(self) -> int:
        """Number of samples in chunk"""
        return len(self.data)

    @property
    def energy(self) -> float:
        """RMS energy of audio chunk (for VAD)"""
        return float(np.sqrt(np.mean(self.data ** 2)))

    def __repr__(self):
        return (f"AudioChunk(samples={self.num_samples}, "
                f"duration={self.duration:.3f}s, "
                f"energy={self.energy:.6f})")


class TranscriptEvent:
    """
    Represents a transcription result from ASR.

    Uses __slots__ for memory efficiency in queue storage.
    """
    __slots__ = ('text', 'confidence', 'timestamp', 'is_final')

    def __init__(self, text: str, confidence: float = 1.0,
                 is_final: bool = True, timestamp: float = None):
        """
        Initialize transcript event.

        Args:
            text: Transcribed text
            confidence: Confidence score (0.0 to 1.0)
            is_final: Whether this is a final result or partial
            timestamp: Unix timestamp (defaults to current time)
        """
        self.text = text
        self.confidence = confidence
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.is_final = is_final

    def __repr__(self):
        final_marker = "FINAL" if self.is_final else "PARTIAL"
        return (f"TranscriptEvent({final_marker}, "
                f"text='{self.text}', "
                f"confidence={self.confidence:.2f})")


class ProcessedText:
    """
    Represents text processed by NLP engine (tokenized, tagged).

    Uses __slots__ for memory efficiency.
    """
    __slots__ = ('tokens', 'tagged_tokens', 'original_text', 'timestamp',
                 'ends_with_question')

    def __init__(self, tokens: List[str], tagged_tokens: List[tuple],
                 original_text: str, timestamp: float = None,
                 ends_with_question: bool = False):
        """
        Initialize processed text.

        Args:
            tokens: List of string tokens
            tagged_tokens: List of (token, tag) tuples
            original_text: Original input text
            timestamp: Unix timestamp
            ends_with_question: True when the original sentence ends with '?'
        """
        self.tokens = tokens
        self.tagged_tokens = tagged_tokens
        self.original_text = original_text
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.ends_with_question = ends_with_question

    def __repr__(self):
        return (f"ProcessedText(tokens={len(self.tokens)}, "
                f"ends_with_question={self.ends_with_question}, "
                f"original='{self.original_text}')")


class GrammarMetadata:
    """
    Carries grammar-level annotations produced by GrammarTransformer.

    Phases populate fields incrementally:
      Phase 1 — tense
      Phase 2 — is_negated
      Phase 3 — question_type

    Uses __slots__ for memory efficiency.
    """
    __slots__ = ('tense', 'is_negated', 'question_type')

    def __init__(
        self,
        tense: Optional[str] = None,
        is_negated: bool = False,
        question_type: Optional[str] = None,
    ):
        """
        Initialize grammar metadata.

        Args:
            tense: 'PAST', 'FUTURE', or None (present/default)
            is_negated: True if the sentence contains negation
            question_type: 'WH', 'YES_NO', or None (statement)
        """
        self.tense = tense
        self.is_negated = is_negated
        self.question_type = question_type

    def __repr__(self):
        return (f"GrammarMetadata(tense={self.tense!r}, "
                f"is_negated={self.is_negated}, "
                f"question_type={self.question_type!r})")


class GlossPhrase:
    """
    Represents a phrase converted to ISL glosses.

    Uses __slots__ for memory efficiency in pipeline queues.
    """
    __slots__ = ('glosses', 'original_text', 'timestamp',
                 'tense', 'is_negated', 'question_type')

    def __init__(
        self,
        glosses: List[str],
        original_text: str,
        timestamp: float = None,
        tense: Optional[str] = None,
        is_negated: bool = False,
        question_type: Optional[str] = None,
    ):
        """
        Initialize gloss phrase.

        Args:
            glosses: List of ISL glosses (uppercase convention)
            original_text: Original English text
            timestamp: Unix timestamp (defaults to current time)
            tense: 'PAST', 'FUTURE', or None
            is_negated: True if sentence contains negation
            question_type: 'WH', 'YES_NO', or None
        """
        self.glosses = glosses
        self.original_text = original_text
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.tense = tense
        self.is_negated = is_negated
        self.question_type = question_type

    @property
    def gloss_string(self) -> str:
        """Space-separated gloss string"""
        return ' '.join(self.glosses)

    @property
    def num_glosses(self) -> int:
        """Number of glosses in phrase"""
        return len(self.glosses)

    def __repr__(self):
        return (f"GlossPhrase(glosses={self.gloss_string}, "
                f"tense={self.tense!r}, "
                f"original='{self.original_text}')")


class SiGMLOutput:
    """
    Represents final SiGML XML output.

    Uses __slots__ for memory efficiency.
    """
    __slots__ = ('sigml_xml', 'glosses', 'original_text', 'timestamp')

    def __init__(self, sigml_xml: str, glosses: List[str],
                 original_text: str, timestamp: float = None):
        """
        Initialize SiGML output.

        Args:
            sigml_xml: Complete SiGML XML string
            glosses: List of glosses used
            original_text: Original English text
            timestamp: Unix timestamp (defaults to current time)
        """
        self.sigml_xml = sigml_xml
        self.glosses = glosses
        self.original_text = original_text
        self.timestamp = timestamp if timestamp is not None else time.time()

    def __repr__(self):
        return (f"SiGMLOutput(glosses={len(self.glosses)}, "
                f"original='{self.original_text}', "
                f"xml_size={len(self.sigml_xml)} bytes)")


# Memory footprint comparison (approximate)
def print_memory_savings():
    """
    Demonstrate memory savings from using __slots__.

    Regular class: ~56 bytes overhead + dict (~112 bytes) = ~168 bytes
    __slots__ class: ~56 bytes overhead only = ~56 bytes
    Savings: ~66% reduction in overhead
    """
    import sys

    class RegularClass:
        def __init__(self):
            self.data = None
            self.timestamp = None
            self.sample_rate = None

    class SlotsClass:
        __slots__ = ('data', 'timestamp', 'sample_rate')

        def __init__(self):
            self.data = None
            self.timestamp = None
            self.sample_rate = None

    regular = RegularClass()
    slots = SlotsClass()

    regular_size = sys.getsizeof(regular) + sys.getsizeof(regular.__dict__)
    slots_size = sys.getsizeof(slots)

    print("Memory Footprint Comparison (empty instances):")
    print(f"  Regular class: {regular_size} bytes")
    print(f"  __slots__ class: {slots_size} bytes")
    print(
        f"  Savings: {regular_size - slots_size} bytes ({(1 - slots_size/regular_size)*100:.1f}% reduction)")


if __name__ == '__main__':
    # Test data classes
    print("Testing SignVani Data Classes\n")
    print("=" * 60)

    # Test AudioChunk
    print("\n1. AudioChunk:")
    audio_data = np.random.randn(1024).astype(np.float32)
    chunk = AudioChunk(audio_data, sample_rate=16000)
    print(f"   {chunk}")
    print(f"   Memory (data only): {chunk.data.nbytes} bytes")

    # Test TranscriptEvent
    print("\n2. TranscriptEvent:")
    transcript = TranscriptEvent("Hello world", confidence=0.95, is_final=True)
    print(f"   {transcript}")

    # Test GlossPhrase
    print("\n3. GlossPhrase:")
    gloss = GlossPhrase(['HELLO', 'WORLD'], "Hello world")
    print(f"   {gloss}")

    # Test SiGMLOutput
    print("\n4. SiGMLOutput:")
    sigml = SiGMLOutput('<sigml>...</sigml>', ['HELLO'], "Hello")
    print(f"   {sigml}")

    # Show memory savings
    print("\n" + "=" * 60)
    print_memory_savings()
