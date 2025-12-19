"""
SignVani Audio Acquisition Module
Handles audio capture from 3.5mm audio jack (earphone mic) and speech recognition using Vosk
"""
import wave
import io
import time
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from vosk import Model, KaldiRecognizer
import json

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio acquisition and speech-to-text transcription"""

    def __init__(self, model_path: str, sample_rate: int = 16000):
        """
        Initialize audio processor with Vosk ASR model

        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate (must match Vosk model requirements)
        """
        self.sample_rate = sample_rate
        self.model_path = Path(model_path)

        # Load Vosk model
        logger.info(f"Loading Vosk model from {model_path}...")
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at {model_path}\n"
                "Download: wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            )

        self.model = Model(str(self.model_path))
        logger.info("Vosk model loaded successfully")

    def transcribe_audio_file(self, audio_file: bytes) -> Tuple[str, float]:
        """
        Transcribe audio from uploaded file

        Args:
            audio_file: Audio file bytes (WAV format)

        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        start_time = time.time()

        try:
            # Read WAV file
            wf = wave.open(io.BytesIO(audio_file), "rb")

            # Validate format
            if wf.getnchannels() != 1:
                raise ValueError("Audio must be mono (1 channel)")
            if wf.getsampwidth() != 2:
                raise ValueError("Audio must be 16-bit PCM")
            if wf.getframerate() != self.sample_rate:
                logger.warning(
                    f"Audio sample rate {wf.getframerate()} Hz does not match "
                    f"expected {self.sample_rate} Hz. Results may be inaccurate."
                )

            # Create recognizer
            recognizer = KaldiRecognizer(self.model, wf.getframerate())
            recognizer.SetWords(True)  # Enable word-level timestamps

            # Process audio in chunks
            transcription_parts = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if 'text' in result and result['text']:
                        transcription_parts.append(result['text'])

            # Final result
            final_result = json.loads(recognizer.FinalResult())
            if 'text' in final_result and final_result['text']:
                transcription_parts.append(final_result['text'])

            # Combine all parts
            full_text = ' '.join(transcription_parts).strip()

            # Calculate confidence (Vosk doesn't provide this directly, using heuristic)
            confidence = 0.85 if full_text else 0.0

            processing_time = time.time() - start_time
            logger.info(
                f"Transcription completed in {processing_time:.2f}s: {full_text}")

            return full_text, confidence

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    def reduce_noise(self, audio_data: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """
        Apply spectral subtraction noise reduction

        Args:
            audio_data: Audio samples as numpy array
            strength: Noise reduction strength (0.0 to 1.0)

        Returns:
            Noise-reduced audio as numpy array
        """
        # Simple spectral subtraction approximation
        # For production, consider using noisereduce library

        if strength == 0:
            return audio_data

        # Estimate noise floor from first 0.5 seconds
        noise_sample_size = min(
            int(self.sample_rate * 0.5), len(audio_data) // 4)
        noise_profile = np.mean(np.abs(audio_data[:noise_sample_size]))

        # Apply threshold
        threshold = noise_profile * (1 + strength)
        reduced = np.where(np.abs(audio_data) < threshold, 0, audio_data)

        logger.debug(f"Applied noise reduction (strength={strength})")
        return reduced

    def validate_audio_format(self, audio_file: bytes) -> dict:
        """
        Validate audio file format and return metadata

        Returns:
            Dictionary with audio metadata
        """
        try:
            wf = wave.open(io.BytesIO(audio_file), "rb")

            metadata = {
                'channels': wf.getnchannels(),
                'sample_width': wf.getsampwidth(),
                'frame_rate': wf.getframerate(),
                'num_frames': wf.getnframes(),
                'duration': wf.getnframes() / float(wf.getframerate()),
                'valid': True,
                'errors': []
            }

            # Validation checks
            if metadata['channels'] != 1:
                metadata['errors'].append(
                    f"Expected mono audio, got {metadata['channels']} channels")
                metadata['valid'] = False

            if metadata['sample_width'] != 2:
                metadata['errors'].append(
                    f"Expected 16-bit audio, got {metadata['sample_width'] * 8}-bit")
                metadata['valid'] = False

            if metadata['frame_rate'] != self.sample_rate:
                metadata['errors'].append(
                    f"Expected {self.sample_rate} Hz, got {metadata['frame_rate']} Hz"
                )
                # Don't mark as invalid, just warn

            if metadata['duration'] > 60:
                metadata['errors'].append(
                    f"Audio too long: {metadata['duration']:.1f}s (max 60s)")
                metadata['valid'] = False

            wf.close()
            return metadata

        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Invalid WAV file: {str(e)}"]
            }

    def convert_to_wav(self, audio_bytes: bytes, input_format: str = "auto") -> bytes:
        """
        Convert audio to WAV format (16kHz, mono, 16-bit)

        Note: For production use, integrate with pydub or ffmpeg
        Currently returns input if already valid WAV
        """
        # Check if already valid WAV
        metadata = self.validate_audio_format(audio_bytes)

        if metadata['valid']:
            logger.debug("Audio already in correct WAV format")
            return audio_bytes

        # TODO: Implement conversion using pydub or ffmpeg
        # For now, raise error if format is invalid
        raise ValueError(
            f"Audio format conversion not implemented. Errors: {metadata['errors']}"
        )


class MockAudioProcessor(AudioProcessor):
    """Mock audio processor for testing without Vosk model"""

    def __init__(self, sample_rate: int = 16000):
        """Initialize mock processor"""
        self.sample_rate = sample_rate
        self.model_path = Path("mock")
        logger.warning(
            "Using MockAudioProcessor - transcriptions will be simulated")

    def transcribe_audio_file(self, audio_file: bytes) -> Tuple[str, float]:
        """Return mock transcription"""
        time.sleep(1)  # Simulate processing time

        # Validate it's a WAV file
        try:
            wf = wave.open(io.BytesIO(audio_file), "rb")
            duration = wf.getnframes() / float(wf.getframerate())
            wf.close()

            logger.info(f"Mock transcription of {duration:.1f}s audio")
            return "I am going to the market", 0.85

        except Exception as e:
            logger.error(f"Mock transcription error: {e}")
            return "Hello world", 0.50


def create_audio_processor(
    model_path: Optional[str] = None,
    mock: bool = False,
    sample_rate: int = 16000
) -> AudioProcessor:
    """
    Factory function to create audio processor

    Args:
        model_path: Path to Vosk model (required if not mock)
        mock: Use mock processor for testing
        sample_rate: Audio sample rate

    Returns:
        AudioProcessor instance
    """
    if mock:
        return MockAudioProcessor(sample_rate)

    if not model_path:
        raise ValueError("model_path required when mock=False")

    return AudioProcessor(model_path, sample_rate)


if __name__ == "__main__":
    # Test audio processor
    logging.basicConfig(level=logging.INFO)

    # Create mock processor for testing
    processor = MockAudioProcessor()

    # Test with dummy WAV file
    # In real usage, this would be actual audio from earphone mic via audio jack
    print("Audio processor initialized")
    print(f"Sample rate: {processor.sample_rate} Hz")
