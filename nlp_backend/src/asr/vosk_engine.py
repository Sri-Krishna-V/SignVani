"""
Vosk ASR Engine Wrapper

Thread-safe singleton wrapper for the Vosk offline speech recognition engine.
Handles model loading and audio transcription.
"""

import json
import os
import threading
import logging
from typing import Optional, Dict, Any

from vosk import Model, KaldiRecognizer, SetLogLevel
from config.settings import vosk_config, audio_config
from src.utils.exceptions import ASRError, ModelLoadError

# Configure logging
logger = logging.getLogger(__name__)


class VoskEngine:
    """
    Thread-safe singleton for Vosk ASR engine.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VoskEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self._model_path = vosk_config.MODEL_PATH
            self._sample_rate = audio_config.SAMPLE_RATE
            self._model: Optional[Model] = None
            self._recognizer: Optional[KaldiRecognizer] = None

            self._load_model()
            self._initialized = True

    def _load_model(self):
        """Load Vosk model from disk."""
        if not os.path.exists(self._model_path):
            raise ModelLoadError(
                f"Vosk model not found at {self._model_path}. Please run scripts/setup_models.py")

        try:
            logger.info(f"Loading Vosk model from {self._model_path}...")
            # Suppress Vosk verbose logs
            SetLogLevel(-1)

            self._model = Model(self._model_path)

            self._recognizer = KaldiRecognizer(self._model, self._sample_rate)
            self._recognizer.SetMaxAlternatives(vosk_config.MAX_ALTERNATIVES)
            self._recognizer.SetWords(vosk_config.WORDS)

            logger.info("Vosk model loaded successfully.")
        except Exception as e:
            raise ModelLoadError(f"Failed to load Vosk model: {e}")

    def process_audio(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Process a chunk of audio data.
        Uses timeout on lock to prevent deadlocks on RPi.

        Args:
            audio_data: Raw audio bytes (int16 PCM)

        Returns:
            Dictionary with result if a complete utterance is recognized,
            None if partial result or silence.
        """
        # Use timeout to prevent deadlock on RPi
        if not self._lock.acquire(timeout=2.0):
            logger.warning("Vosk engine lock acquisition timeout")
            return None

        try:
            if self._recognizer.AcceptWaveform(audio_data):
                try:
                    result = json.loads(self._recognizer.Result())
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to decode Vosk result JSON")
                    return None
            else:
                # Partial result available via self._recognizer.PartialResult()
                return None
        finally:
            self._lock.release()

    def get_final_result(self) -> Dict[str, Any]:
        """Get the final result from the recognizer (flush buffer)."""
        if not self._lock.acquire(timeout=1.0):
            logger.warning("Vosk get_final_result lock timeout")
            return {}

        try:
            return json.loads(self._recognizer.FinalResult())
        except json.JSONDecodeError:
            return {}
        finally:
            self._lock.release()

    def reset(self):
        """Reset the recognizer."""
        if not self._lock.acquire(timeout=1.0):
            logger.warning("Vosk reset lock timeout")
            return

        try:
            self._recognizer.Reset()
        finally:
            self._lock.release()
