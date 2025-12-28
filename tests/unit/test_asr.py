import unittest
import queue
import threading
import time
import numpy as np
from src.asr.vosk_engine import VoskEngine
from src.asr.asr_worker import ASRWorker
from src.nlp.dataclasses import AudioChunk, TranscriptEvent


class TestASR(unittest.TestCase):
    def test_vosk_engine_initialization(self):
        """Test that VoskEngine initializes correctly (singleton)."""
        print("\nInitializing VoskEngine...")
        engine1 = VoskEngine()
        engine2 = VoskEngine()
        self.assertIs(engine1, engine2)
        self.assertIsNotNone(engine1._model)
        print("VoskEngine initialized successfully.")

    def test_asr_worker(self):
        """Test ASR worker with silence/dummy audio."""
        print("\nTesting ASRWorker...")
        input_queue = queue.Queue()
        output_queue = queue.Queue()

        worker = ASRWorker(input_queue, output_queue)
        worker.start()

        # Create a dummy audio chunk (silence)
        # 1 second of silence at 16kHz
        silence = np.zeros(16000, dtype=np.float32)
        chunk = AudioChunk(data=silence, sample_rate=16000)

        input_queue.put(chunk)

        # Wait a bit
        time.sleep(2)

        worker.stop()
        worker.join()

        # We expect no transcript for silence, but worker should run without error
        self.assertTrue(output_queue.empty())
        print("ASRWorker test completed.")


if __name__ == '__main__':
    unittest.main()
