"""
SignVani Configuration Settings
Optimized for Raspberry Pi 4B deployment
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""

    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = "SignVani"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ============================================
    # Paths
    # ============================================
    BASE_DIR: Path = Path(__file__).parent
    SERVICE_DIR: Path = BASE_DIR / "signvani_service"
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = SERVICE_DIR / "models"
    TEMP_DIR: Path = BASE_DIR / "temp"

    # Database
    DATABASE_PATH: Path = DATA_DIR / "signvani.db"
    SEED_DATA_PATH: Path = DATA_DIR / "seed_gloss_mappings.json"

    # ============================================
    # Audio Acquisition Settings
    # ============================================
    # Audio input device (3.5mm audio jack with earphone mic)
    AUDIO_INPUT_DEVICE_INDEX: int = None  # None = default device
    AUDIO_SAMPLE_RATE: int = 16000  # 16kHz for Vosk compatibility
    AUDIO_CHANNELS: int = 1  # Mono
    AUDIO_CHUNK_SIZE: int = 1024  # Buffer size for real-time
    AUDIO_FORMAT: str = "int16"  # 16-bit PCM
    AUDIO_MAX_DURATION: int = 60  # Maximum recording duration (seconds)

    # Noise reduction
    ENABLE_NOISE_REDUCTION: bool = True
    NOISE_REDUCTION_STRENGTH: float = 0.5  # 0.0 to 1.0

    # ============================================
    # Vosk ASR Settings
    # ============================================
    VOSK_MODEL_PATH: Path = MODELS_DIR / "vosk-model-small-en-us-0.15"
    VOSK_SAMPLE_RATE: int = 16000
    VOSK_ALTERNATIVES: int = 1  # Number of recognition alternatives

    # ============================================
    # NLP Processing Settings
    # ============================================
    # spaCy model
    SPACY_MODEL: str = "en_core_web_sm"

    # Stop-words to remove (ISL doesn't use these)
    STOP_WORDS: list = [
        "is", "am", "are", "was", "were", "be", "been", "being",
        "the", "a", "an", "to", "of", "in", "on", "at",
        "for", "with", "from", "by", "as", "into", "through"
    ]

    # POS tags to keep for gloss generation
    KEEP_POS_TAGS: list = ["NOUN", "VERB", "ADJ", "PRON", "NUM", "PROPN"]

    # Enable SVO to SOV transformation
    ENABLE_SOV_TRANSFORMATION: bool = True

    # Gloss formatting
    GLOSS_UPPERCASE: bool = True
    GLOSS_SEPARATOR: str = " "

    # ============================================
    # Visual Synthesis Settings
    # ============================================
    # HamNoSys retrieval
    DEFAULT_REGION: str = "Mumbai"  # Default ISL regional variant
    HAMNOSYS_CONFIDENCE_THRESHOLD: float = 0.7

    # SiGML generation
    SIGML_VERSION: str = "1.0"
    SIGML_ENCODING: str = "UTF-8"
    AVATAR_NAME: str = "ISL_Avatar"

    # Animation settings
    ENABLE_FRAME_BLENDING: bool = True
    FRAME_INTERPOLATION_STEPS: int = 5  # Smooth transitions
    ANIMATION_FPS: int = 30

    # ============================================
    # API Settings
    # ============================================
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    # SSE (Server-Sent Events)
    SSE_RETRY_TIMEOUT: int = 3000  # milliseconds
    SSE_KEEPALIVE_INTERVAL: int = 15  # seconds

    # Request limits
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT: int = 300  # 5 minutes for long processing

    # ============================================
    # Performance Settings (Raspberry Pi 4B)
    # ============================================
    # Memory optimization
    ENABLE_MEMORY_OPTIMIZATION: bool = True
    MAX_CACHE_SIZE: int = 100  # Cache up to 100 gloss mappings in memory

    # CPU optimization
    NUM_WORKERS: int = 2  # Uvicorn workers (Pi 4B has 4 cores)
    ENABLE_MULTIPROCESSING: bool = False  # Keep single process for Pi

    # GPU acceleration (VideoCore)
    ENABLE_GPU_ACCELERATION: bool = True

    # ============================================
    # Logging Settings
    # ============================================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE_PATH: Path = BASE_DIR / "logs" / "signvani.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "7 days"

    # ============================================
    # Database Settings
    # ============================================
    # SQLite optimization for Raspberry Pi
    SQLITE_JOURNAL_MODE: str = "WAL"  # Write-Ahead Logging
    SQLITE_CACHE_SIZE: int = -2000  # 2MB cache (negative = KB)
    SQLITE_SYNCHRONOUS: str = "NORMAL"  # Balance performance/safety
    SQLITE_TIMEOUT: int = 30  # seconds

    # ============================================
    # Development Settings
    # ============================================
    # Mock mode (for testing without hardware)
    MOCK_AUDIO_INPUT: bool = False
    MOCK_ASR: bool = False
    MOCK_HAMNOSYS: bool = False

    # Test audio file
    TEST_AUDIO_PATH: Path = BASE_DIR / "tests" / "test_audio.wav"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# ============================================
# Helper Functions
# ============================================
def ensure_directories():
    """Create necessary directories if they don't exist"""
    dirs = [
        settings.DATA_DIR,
        settings.MODELS_DIR,
        settings.TEMP_DIR,
        settings.LOG_FILE_PATH.parent,
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def get_vosk_model_path() -> str:
    """Get Vosk model path, raise error if not found"""
    if not settings.VOSK_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Vosk model not found at {settings.VOSK_MODEL_PATH}\n"
            "Please download it using:\n"
            "wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip\n"
            f"unzip vosk-model-small-en-us-0.15.zip -d {settings.MODELS_DIR}/"
        )
    return str(settings.VOSK_MODEL_PATH)


def validate_config():
    """Validate configuration settings"""
    errors = []

    # Check critical paths
    if not settings.DATA_DIR.exists():
        errors.append(f"Data directory not found: {settings.DATA_DIR}")

    if not settings.MOCK_ASR and not settings.VOSK_MODEL_PATH.exists():
        errors.append(f"Vosk model not found: {settings.VOSK_MODEL_PATH}")

    # Check database
    if not settings.DATABASE_PATH.parent.exists():
        errors.append(
            f"Database directory not found: {settings.DATABASE_PATH.parent}")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(errors))

    return True


# Initialize directories on import
ensure_directories()


if __name__ == "__main__":
    # Display configuration
    print("=== SignVani Configuration ===")
    print(f"App Name: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"\nPaths:")
    print(f"  Base Directory: {settings.BASE_DIR}")
    print(f"  Database: {settings.DATABASE_PATH}")
    print(f"  Vosk Model: {settings.VOSK_MODEL_PATH}")
    print(f"\nAudio Settings:")
    print(f"  Sample Rate: {settings.AUDIO_SAMPLE_RATE} Hz")
    print(f"  Channels: {settings.AUDIO_CHANNELS}")
    print(f"  Chunk Size: {settings.AUDIO_CHUNK_SIZE}")
    print(f"\nNLP Settings:")
    print(f"  spaCy Model: {settings.SPACY_MODEL}")
    print(f"  SOV Transformation: {settings.ENABLE_SOV_TRANSFORMATION}")
    print(f"\nPerformance:")
    print(f"  Workers: {settings.NUM_WORKERS}")
    print(f"  GPU Acceleration: {settings.ENABLE_GPU_ACCELERATION}")
    print(f"  Cache Size: {settings.MAX_CACHE_SIZE}")
