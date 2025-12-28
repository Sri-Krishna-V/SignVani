"""
Unit tests for Audio Subsystem
"""
import unittest
import numpy as np
import queue
import time
from unittest.mock import MagicMock, patch

from src.audio.vad import VoiceActivityDetector
from src.audio.noise_filter import SpectralSubtractor
from src.audio.audio_buffer import CircularAudioBuffer
from src.audio.audio_capture import AudioCaptureSystem
from src.nlp.dataclasses import AudioChunk
from config.settings import audio_config

class TestAudioSubsystem(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.chunk_size = 1024

    # ==========================================
    # VAD Tests
    # ==========================================
    def test_vad_silence(self):
        """Test VAD with silence."""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)
        
        # Create silence chunk
        silence_data = np.zeros(self.chunk_size, dtype=np.float32)
        chunk = AudioChunk(silence_data, self.sample_rate)
        
        # Feed enough frames to fill history
        for _ in range(5):
            is_speech = vad.process_chunk(chunk)
        
        self.assertFalse(is_speech, "VAD should not detect speech in silence")

    def test_vad_speech(self):
        """Test VAD with high energy noise (simulated speech)."""
        vad = VoiceActivityDetector(threshold=0.01, frame_count=3)
        
        # Create high energy chunk (random noise > threshold)
        # RMS of uniform [0.5, 1.0] is > 0.5
        speech_data = np.random.uniform(0.5, 1.0, self.chunk_size).astype(np.float32)
        chunk = AudioChunk(speech_data, self.sample_rate)
        
        # Feed enough frames
        is_speech = False
        for _ in range(5):
            is_speech = vad.process_chunk(chunk)
            
        self.assertTrue(is_speech, "VAD should detect speech in high energy signal")

    # ==========================================
    # Noise Filter Tests
    # ==========================================
    def test_noise_filter_shape(self):
        """Test that noise filter preserves data shape."""
        nf = SpectralSubtractor(fft_size=1024)
        
        data = np.random.random(self.chunk_size).astype(np.float32)
        
        # Calibration phase
        nf.update_noise_profile(data)
        
        # Filtering phase
        filtered = nf.filter(data)
        
        self.assertEqual(len(filtered), len(data))
        self.assertEqual(filtered.dtype, np.float32)

    def test_noise_filter_calibration(self):
        """Test noise filter calibration state."""
        nf = SpectralSubtractor(fft_size=1024)
        self.assertFalse(nf._is_calibrated)
        
        data = np.zeros(self.chunk_size, dtype=np.float32)
        
        # Feed 3 chunks (as per implementation requirement)
        for _ in range(3):
            nf.update_noise_profile(data)
            
        self.assertTrue(nf._is_calibrated)

    # ==========================================
    # Audio Buffer Tests
    # ==========================================
    def test_buffer_overflow(self):
        """Test circular buffer overflow behavior."""
        buf = CircularAudioBuffer(max_size=3)
        
        # Fill buffer
        for i in range(3):
            chunk = AudioChunk(np.zeros(10), 16000)
            buf.put(chunk)
            
        self.assertEqual(len(buf._buffer), 3)
        self.assertEqual(buf._total_chunks_dropped, 0)
        
        # Overflow
        chunk = AudioChunk(np.zeros(10), 16000)
        buf.put(chunk)
        
        self.assertEqual(len(buf._buffer), 3)
        self.assertEqual(buf._total_chunks_dropped, 1)

    # ==========================================
    # Audio Capture Tests (Mocked)
    # ==========================================
    @patch('pyaudio.PyAudio')
    def test_audio_capture_initialization(self, mock_pyaudio):
        """Test AudioCaptureSystem initialization."""
        capture = AudioCaptureSystem()
        self.assertIsNotNone(capture._output_queue)
        self.assertFalse(capture._is_running)

if __name__ == '__main__':
    unittest.main()
