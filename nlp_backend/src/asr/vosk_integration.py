"""
Real-time ASR integration for SignVani
Integrates Vosk speech recognition with the pipeline
"""

import logging
import json
import wave
import io
import numpy as np
from typing import Optional, Dict, Any
import tempfile
import os

try:
    import vosk
    import soundfile as sf
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logging.warning("Vosk not available. Using placeholder ASR.")

logger = logging.getLogger(__name__)

class VoskASR:
    """Vosk-based ASR engine for real-time speech recognition"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Vosk ASR
        
        Args:
            model_path: Path to Vosk model directory
        """
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.recognizer = None
        
        if VOSK_AVAILABLE:
            self._initialize_model()
        else:
            logger.warning("Vosk not available - using placeholder ASR")
    
    def _get_default_model_path(self) -> str:
        """Get default Vosk model path"""
        # Check common model locations
        possible_paths = [
            "models/vosk-model-small-en-us-0.15",
            "../models/vosk-model-small-en-us-0.15",
            "signvani_service/models/vosk-model-small-en-us-0.15"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return first path as default (will be downloaded if needed)
        return possible_paths[0]
    
    def _initialize_model(self):
        """Initialize Vosk model and recognizer"""
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Vosk model not found at {self.model_path}")
                return
            
            logger.info(f"Loading Vosk model from {self.model_path}")
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            logger.info("Vosk ASR initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vosk: {e}")
            self.model = None
            self.recognizer = None
    
    def transcribe_audio_file(self, audio_data: bytes) -> str:
        """
        Transcribe audio file data
        
        Args:
            audio_data: Raw audio bytes (WAV format)
        
        Returns:
            Transcribed text
        """
        if not VOSK_AVAILABLE or not self.recognizer:
            return self._placeholder_transcribe()
        
        try:
            # Create recognizer for each transcription
            recognizer = vosk.KaldiRecognizer(self.model, 16000)
            
            # Process audio data
            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                return result.get('text', '')
            else:
                # Get partial result
                result = json.loads(recognizer.PartialResult())
                return result.get('partial', '')
                
        except Exception as e:
            logger.error(f"ASR transcription error: {e}")
            return self._placeholder_transcribe()
    
    def transcribe_audio_stream(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe streaming audio data
        
        Args:
            audio_data: Audio chunk bytes
        
        Returns:
            Dict with transcription results
        """
        if not VOSK_AVAILABLE or not self.recognizer:
            return {
                "text": "",
                "partial": self._placeholder_transcribe(),
                "final": False
            }
        
        try:
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                return {
                    "text": result.get('text', ''),
                    "partial": '',
                    "final": True
                }
            else:
                result = json.loads(self.recognizer.PartialResult())
                return {
                    "text": '',
                    "partial": result.get('partial', ''),
                    "final": False
                }
                
        except Exception as e:
            logger.error(f"Streaming ASR error: {e}")
            return {
                "text": "",
                "partial": self._placeholder_transcribe(),
                "final": False
            }
    
    def reset_recognizer(self):
        """Reset the recognizer for new session"""
        if VOSK_AVAILABLE and self.model:
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
    
    def _placeholder_transcribe(self) -> str:
        """Placeholder transcription when Vosk is not available"""
        # Return a sample phrase for demo purposes
        return "hello world"

# Global ASR instance
asr_engine: Optional[VoskASR] = None

def get_asr_engine() -> VoskASR:
    """Get or create ASR engine instance"""
    global asr_engine
    if asr_engine is None:
        asr_engine = VoskASR()
    return asr_engine

def convert_to_wav(audio_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    Convert audio data to WAV format
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Target sample rate
    
    Returns:
        WAV format bytes
    """
    try:
        # If audio is already WAV, return as-is
        if audio_data.startswith(b'RIFF'):
            return audio_data
        
        # For other formats, you would use ffmpeg or similar
        # For now, assume the input is properly formatted
        return audio_data
        
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return audio_data
