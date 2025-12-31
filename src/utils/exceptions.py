"""
SignVani Custom Exception Hierarchy

Provides domain-specific exceptions for better error handling and debugging.
Each subsystem has its own exception class for targeted error catching.
"""


class SignVaniError(Exception):
    """Base exception for all SignVani errors"""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ============================================================================
# Audio Subsystem Exceptions
# ============================================================================


class AudioError(SignVaniError):
    """Base exception for audio-related errors"""
    pass


class AudioCaptureError(AudioError):
    """Raised when audio capture fails"""
    pass


class AudioStreamError(AudioError):
    """Raised when audio stream operations fail"""
    pass


class NoiseFilterError(AudioError):
    """Raised when noise filtering fails"""
    pass


class VADError(AudioError):
    """Raised when Voice Activity Detection fails"""
    pass


# ============================================================================
# ASR (Automatic Speech Recognition) Exceptions
# ============================================================================


class ASRError(SignVaniError):
    """Base exception for ASR-related errors"""
    pass


class ModelLoadError(ASRError):
    """Raised when Vosk model fails to load"""
    pass


class TranscriptionError(ASRError):
    """Raised when speech transcription fails"""
    pass


class ASRWorkerError(ASRError):
    """Raised when ASR worker thread encounters an error"""
    pass


# ============================================================================
# NLP (Natural Language Processing) Exceptions
# ============================================================================


class NLPError(SignVaniError):
    """Base exception for NLP-related errors"""
    pass


class TokenizationError(NLPError):
    """Raised when text tokenization fails"""
    pass


class LemmatizationError(NLPError):
    """Raised when lemmatization fails"""
    pass


class GrammarTransformError(NLPError):
    """Raised when SVO→SOV transformation fails"""
    pass


class GlossMappingError(NLPError):
    """Raised when word-to-gloss mapping fails"""
    pass


# ============================================================================
# Database Exceptions
# ============================================================================


class DatabaseError(SignVaniError):
    """Base exception for database-related errors"""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class QueryError(DatabaseError):
    """Raised when database query fails"""
    pass


class SchemaError(DatabaseError):
    """Raised when database schema is invalid"""
    pass


class SeedDataError(DatabaseError):
    """Raised when seeding database fails"""
    pass


# ============================================================================
# SiGML Generation Exceptions
# ============================================================================


class SiGMLError(SignVaniError):
    """Base exception for SiGML generation errors"""
    pass


class SiGMLGenerationError(SiGMLError):
    """Raised when SiGML XML generation fails"""
    pass


class HamNoSysError(SiGMLError):
    """Raised when HamNoSys notation is invalid"""
    pass


# ============================================================================
# Pipeline Exceptions
# ============================================================================


class PipelineError(SignVaniError):
    """Base exception for pipeline-related errors"""
    pass


class ThreadError(PipelineError):
    """Raised when worker thread encounters an error"""
    pass


class QueueError(PipelineError):
    """Raised when queue operations fail"""
    pass


class TimeoutError(PipelineError):
    """Raised when operations exceed timeout threshold"""
    pass


class OrchestrationError(PipelineError):
    """Raised when pipeline orchestration fails"""
    pass


# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigError(SignVaniError):
    """Base exception for configuration errors"""
    pass


class InvalidConfigError(ConfigError):
    """Raised when configuration is invalid"""
    pass


class MissingConfigError(ConfigError):
    """Raised when required configuration is missing"""
    pass


# ============================================================================
# Utility Functions
# ============================================================================


def get_exception_hierarchy():
    """
    Return the complete exception hierarchy as a dictionary.
    Useful for documentation and debugging.
    """
    return {
        'SignVaniError': {
            'AudioError': [
                'AudioCaptureError',
                'AudioStreamError',
                'NoiseFilterError',
                'VADError'
            ],
            'ASRError': [
                'ModelLoadError',
                'TranscriptionError',
                'ASRWorkerError'
            ],
            'NLPError': [
                'TokenizationError',
                'LemmatizationError',
                'GrammarTransformError',
                'GlossMappingError'
            ],
            'DatabaseError': [
                'ConnectionError',
                'QueryError',
                'SchemaError',
                'SeedDataError'
            ],
            'SiGMLError': [
                'SiGMLGenerationError',
                'HamNoSysError'
            ],
            'PipelineError': [
                'ThreadError',
                'QueueError',
                'TimeoutError',
                'OrchestrationError'
            ],
            'ConfigError': [
                'InvalidConfigError',
                'MissingConfigError'
            ]
        }
    }


def print_exception_hierarchy():
    """Print the exception hierarchy in a readable format"""
    import json
    hierarchy = get_exception_hierarchy()
    print("SignVani Exception Hierarchy:")
    print("=" * 60)
    print(json.dumps(hierarchy, indent=2))


if __name__ == '__main__':
    # Test exception hierarchy
    print_exception_hierarchy()

    # Test custom exception
    try:
        raise AudioCaptureError(
            "Failed to initialize PyAudio stream",
            details="Sample rate 16000 Hz not supported by device"
        )
    except SignVaniError as e:
        print(f"\nTest exception caught: {e}")
        print(f"Exception type: {type(e).__name__}")
