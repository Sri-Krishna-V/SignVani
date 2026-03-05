"""
Integration Test: Phase 1 (Audio) + Phase 2 (ASR)

Verifies the data flow from Audio Capture -> Queue -> ASR Worker.
Uses mocks for the actual ASR inference to avoid needing real audio files.
"""

import unittest
import queue
import threading
import time
import numpy as np
from unittest.mock import MagicMock, patch

from src.audio.audio_capture import AudioCaptureSystem
from src.asr.asr_worker import ASRWorker
from src.nlp.dataclasses import AudioChunk, TranscriptEvent
from src.asr.vosk_engine import VoskEngine

class TestAudioASRPipeline(unittest.TestCase):

    def setUp(self):
        self.audio_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        
        # Initialize components
        # We won't start AudioCaptureSystem's stream, but we'll use its queue
        self.capture_system = AudioCaptureSystem(output_queue=self.audio_queue)
        self.asr_worker = ASRWorker(input_queue=self.audio_queue, output_queue=self.transcript_queue)

    @patch('src.asr.asr_worker.VoskEngine')
    def test_pipeline_flow(self, MockVoskEngine):
        """
        Test data flow: AudioChunk -> ASRWorker -> TranscriptEvent
        """
        # Setup Mock Engine
        mock_engine_instance = MockVoskEngine.return_value
        
        # Configure mock to return a result for the 3rd chunk
        mock_engine_instance.process_audio.side_effect = [
            None, 
            None, 
            {'text': 'hello world'}
        ]

        # Start Worker
        self.asr_worker.start()

        # Simulate Audio Capture producing chunks
        print("\nSimulating audio capture...")
        for i in range(3):
            # Create dummy chunk
            data = np.random.uniform(-0.5, 0.5, 1024).astype(np.float32)
            chunk = AudioChunk(data, 16000)
            self.audio_queue.put(chunk)
            time.sleep(0.01)

        # Wait for processing
        time.sleep(0.5)
        
        # Stop worker
        self.asr_worker.stop()
        self.asr_worker.join()

        # Verify interactions
        self.assertEqual(mock_engine_instance.process_audio.call_count, 3, "Engine should process 3 chunks")
        
        # Verify output
        self.assertFalse(self.transcript_queue.empty(), "Transcript queue should have an event")
        event = self.transcript_queue.get()
        self.assertEqual(event.text, "hello world")
        self.assertTrue(event.is_final)
        
        print("Pipeline integration test passed!")

    def test_real_vosk_loading(self):
        """
        Verify that the real VoskEngine can load the model without crashing.
        This ensures the model path and files are correct.
        """
        print("\nVerifying real Vosk model loading...")
        try:
            engine = VoskEngine()
            self.assertIsNotNone(engine._model)
            print("Real Vosk model loaded successfully.")
        except Exception as e:
            self.fail(f"Failed to load real Vosk model: {e}")

if __name__ == '__main__':
    unittest.main()
