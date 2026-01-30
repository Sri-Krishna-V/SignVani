"""
SignVani Configuration Settings

Central configuration for all modules using frozen dataclasses for immutability.
Optimized for Raspberry Pi 4 deployment with MicroPython-style efficiency.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass(frozen=True)
class AudioConfig:
    """Audio capture and processing configuration"""

    # PyAudio stream parameters
    SAMPLE_RATE: int = 16000          # Vosk requires 16kHz
    CHANNELS: int = 1                  # Mono audio
    FRAMES_PER_BUFFER: int = 1024      # ~64ms @ 16kHz for low latency
    FORMAT: int = 8                    # paInt16 (16-bit signed integer)

    # Noise reduction settings
    NOISE_REDUCTION_ENABLED: bool = True
    # FFT size for spectral subtraction (tunable: 512/1024/2048)
    FFT_SIZE: int = 1024
    ALPHA: float = 2.0                # Over-subtraction factor
    BETA: float = 0.01                # Spectral floor

    # Voice Activity Detection (VAD)
    VAD_ENABLED: bool = True
    VAD_ENERGY_THRESHOLD: float = 0.02  # Energy threshold for speech detection
    VAD_FRAME_COUNT: int = 3            # Consecutive frames to trigger VAD


@dataclass(frozen=True)
class VoskConfig:
    """Vosk ASR engine configuration"""

    # Model path (auto-downloaded by setup_models.py)
    MODEL_NAME: str = 'vosk-model-small-en-in-0.4'
    MODEL_PATH: str = str(PROJECT_ROOT / 'models' / 'vosk' / MODEL_NAME)

    # Vosk optimization settings (memory and performance)
    MAX_ALTERNATIVES: int = 1         # Reduce to 1 for memory efficiency
    # Disable word-level timing (saves memory)
    WORDS: bool = False

    # Model download URL
    MODEL_URL: str = f'https://alphacephei.com/vosk/models/{MODEL_NAME}.zip'


@dataclass(frozen=True)
class NLPConfig:
    """Natural Language Processing configuration"""

    # NLTK data path
    NLTK_DATA_PATH: str = str(PROJECT_ROOT / 'models' / 'nltk_data')

    # Required NLTK resources (updated for NLTK 3.9+)
    NLTK_RESOURCES: tuple = (
        'punkt_tab', 'wordnet', 'stopwords', 'averaged_perceptron_tagger_eng')

    # Processing options
    LEMMATIZATION_ENABLED: bool = True
    MIN_TOKEN_LENGTH: int = 2         # Filter out single characters

    # Grammar transformation
    TRANSFORM_SVO_TO_SOV: bool = True  # Enable SVO→SOV transformation


@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite database configuration"""

    # Database file path
    DB_PATH: str = str(PROJECT_ROOT / 'data' / 'signvani.db')

    # Connection pooling (thread-safe SQLite access)
    CONNECTION_POOL_SIZE: int = 3

    # Query optimization
    CACHE_SIZE: int = 100             # LRU cache for most common glosses
    ENABLE_FTS: bool = True           # Enable Full-Text Search for fuzzy matching

    # SQLite pragma settings (optimized for embedded systems)
    PRAGMA_JOURNAL_MODE: str = 'DELETE'  # Avoid WAL for SD card longevity
    PRAGMA_SYNCHRONOUS: str = 'NORMAL'   # Balance between safety and performance
    PRAGMA_CACHE_SIZE: int = -2000       # 2MB page cache


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline orchestration configuration"""

    # Queue sizes (memory-conscious sizing)
    AUDIO_QUEUE_SIZE: int = 10         # 10 chunks * ~20KB = ~200KB
    TRANSCRIPT_QUEUE_SIZE: int = 5     # 5 events * ~5KB = ~25KB
    GLOSS_QUEUE_SIZE: int = 3          # 3 phrases * ~3KB = ~9KB

    # Thread management
    THREAD_TIMEOUT: float = 5.0        # Watchdog timeout in seconds
    GRACEFUL_SHUTDOWN_TIMEOUT: float = 2.0

    # Performance targets
    TARGET_LATENCY: float = 1.0        # <1s end-to-end requirement
    MAX_MEMORY_MB: int = 500           # Memory budget (excluding OS overhead)


@dataclass(frozen=True)
class SiGMLConfig:
    """SiGML generation configuration"""

    # SiGML XML template settings
    ENCODING: str = 'UTF-8'
    XML_VERSION: str = '1.0'

    # Output options
    PRETTY_PRINT: bool = False         # Disable for production (faster)
    INCLUDE_TIMESTAMP: bool = True


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration (SD card-friendly)"""

    # Log file settings
    LOG_DIR: str = str(PROJECT_ROOT / 'logs')
    LOG_LEVEL: str = 'INFO'            # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # File rotation (prevent SD card wear)
    MAX_LOG_SIZE_MB: int = 10
    BACKUP_COUNT: int = 3

    # Console output
    CONSOLE_LOG_ENABLED: bool = True


# Global configuration instances (read-only)
audio_config = AudioConfig()
vosk_config = VoskConfig()
nlp_config = NLPConfig()
database_config = DatabaseConfig()
pipeline_config = PipelineConfig()
sigml_config = SiGMLConfig()
logging_config = LoggingConfig()


# Utility function to print all configurations
def print_config():
    """Print all configuration settings for debugging"""
    configs = {
        'Audio': audio_config,
        'Vosk': vosk_config,
        'NLP': nlp_config,
        'Database': database_config,
        'Pipeline': pipeline_config,
        'SiGML': sigml_config,
        'Logging': logging_config
    }

    print("=" * 60)
    print("SignVani Configuration")
    print("=" * 60)
    for name, config in configs.items():
        print(f"\n{name} Configuration:")
        print("-" * 60)
        for field, value in config.__dict__.items():
            print(f"  {field}: {value}")
    print("=" * 60)


if __name__ == '__main__':
    # Test configuration by printing all settings
    print_config()
