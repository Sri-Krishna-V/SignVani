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
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logging.warning("Vosk not available. Using placeholder ASR.")

try:
    import soundfile as sf
    import scipy.signal as _scipy_signal
    _RESAMPLE_AVAILABLE = True
except ImportError:
    _RESAMPLE_AVAILABLE = False

try:
    from config.settings import vosk_config
    _CONFIG_MODEL_PATH = vosk_config.MODEL_PATH
except Exception:
    _CONFIG_MODEL_PATH = None

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
        # Prefer path from config (set by setup_models.py)
        if _CONFIG_MODEL_PATH and os.path.exists(_CONFIG_MODEL_PATH):
            return _CONFIG_MODEL_PATH

        # Fallback: scan common locations
        possible_paths = [
            _CONFIG_MODEL_PATH,
            "models/vosk/vosk-model-small-en-in-0.4",
            "models/vosk-model-small-en-us-0.15",
            "../models/vosk-model-small-en-us-0.15",
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        # Return config path as default so error message shows the right location
        return _CONFIG_MODEL_PATH or possible_paths[1]
    
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
    
    def _to_vosk_wav(self, audio_data: bytes) -> bytes:
        """
        Convert any WAV to 16 kHz, mono, 16-bit PCM — the format Vosk requires.
        Uses scipy for resampling when the source rate differs from 16000.
        """
        with wave.open(io.BytesIO(audio_data)) as wf:
            src_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            raw_frames = wf.readframes(wf.getnframes())

        # Decode to int16 numpy array
        dtype = np.int16 if sampwidth == 2 else np.int32
        samples = np.frombuffer(raw_frames, dtype=dtype).astype(np.float32)

        # Downmix to mono
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        # Resample to 16 kHz if needed
        target_rate = 16000
        if src_rate != target_rate:
            if _RESAMPLE_AVAILABLE:
                num_samples = int(len(samples) * target_rate / src_rate)
                samples = _scipy_signal.resample(samples, num_samples)
            else:
                # Fallback: simple decimation (lower quality but no deps)
                step = src_rate / target_rate
                indices = np.arange(0, len(samples), step).astype(int)
                indices = indices[indices < len(samples)]
                samples = samples[indices]

        # Clip and convert back to int16
        samples = np.clip(samples, -32768, 32767).astype(np.int16)

        # Write as WAV in-memory
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(target_rate)
            out.writeframes(samples.tobytes())
        return buf.getvalue()

    def transcribe_audio_file(self, audio_data: bytes) -> str:
        """
        Transcribe audio file data (WAV).

        Automatically converts to 16 kHz mono before feeding to Vosk.
        Feeds audio in chunks and calls FinalResult() to get the full transcript.

        Args:
            audio_data: WAV bytes (any sample rate / channel count)

        Returns:
            Transcribed text string, empty string if nothing recognised
        """
        if not VOSK_AVAILABLE or not self.model:
            return self._placeholder_transcribe()

        try:
            # Normalise to 16 kHz mono WAV
            wav_bytes = self._to_vosk_wav(audio_data)

            with wave.open(io.BytesIO(wav_bytes)) as wf:
                sample_rate = wf.getframerate()
                recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
                recognizer.SetWords(False)

                chunk_size = 4000
                text_parts = []
                while True:
                    data = wf.readframes(chunk_size)
                    if not data:
                        break
                    if recognizer.AcceptWaveform(data):
                        partial = json.loads(recognizer.Result()).get('text', '')
                        if partial:
                            text_parts.append(partial)

                final = json.loads(recognizer.FinalResult()).get('text', '')
                if final:
                    text_parts.append(final)

            transcript = ' '.join(text_parts).strip()
            logger.info(f"Vosk transcript: '{transcript}'")
            return transcript

        except Exception as e:
            logger.error(f"ASR transcription error: {e}")
            return ''
    
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
