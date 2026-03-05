"""
ASR Worker Thread

Consumes processed audio chunks from the queue and runs ASR.
Produces TranscriptEvents.
"""

import queue
import threading
import logging
import numpy as np
from typing import Optional

from src.asr.vosk_engine import VoskEngine
from src.nlp.dataclasses import AudioChunk, TranscriptEvent
from config.settings import pipeline_config
from src.utils.exceptions import ASRError

logger = logging.getLogger(__name__)


class ASRWorker(threading.Thread):
    """
    Worker thread that runs Vosk ASR on incoming audio chunks.
    """

    def __init__(self,
                 input_queue: queue.Queue,
                 output_queue: queue.Queue):
        """
        Initialize ASR worker.

        Args:
            input_queue: Queue containing AudioChunk objects
            output_queue: Queue to put TranscriptEvent objects
        """
        super().__init__(name="ASRWorker")
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True  # Daemon thread
        self._is_running = False
        self._engine: Optional[VoskEngine] = None

    def run(self):
        """Main loop."""
        logger.info("ASR Worker starting...")
        try:
            self._engine = VoskEngine()
        except Exception as e:
            logger.error(f"Failed to initialize Vosk Engine: {e}")
            return

        self._is_running = True

        while self._is_running:
            try:
                # Get chunk with timeout to allow checking _is_running
                chunk: AudioChunk = self.input_queue.get(timeout=1.0)

                # Convert float32 back to int16 bytes for Vosk
                # Clip to avoid overflow before casting
                # AudioChunk data is float32 [-1.0, 1.0]
                audio_int16 = (np.clip(chunk.data, -1.0, 1.0)
                               * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()

                # Process
                result = self._engine.process_audio(audio_bytes)

                if result and 'text' in result and result['text']:
                    text = result['text']
                    logger.info(f"ASR Recognized: {text}")

                    # Extract confidence from Vosk result if available
                    # Vosk provides word-level confidence in 'result' array
                    confidence = 1.0
                    if 'result' in result and result['result']:
                        # Average word confidences
                        word_confs = [w.get('conf', 1.0)
                                      for w in result['result']]
                        confidence = sum(word_confs) / \
                            len(word_confs) if word_confs else 1.0

                    event = TranscriptEvent(
                        text=text,
                        confidence=confidence,
                        is_final=True
                    )

                    # Put to output queue
                    try:
                        self.output_queue.put(event, timeout=0.5)
                    except queue.Full:
                        logger.warning("Transcript queue full, dropping event")

                self.input_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in ASR worker: {e}")

        logger.info("ASR Worker stopped.")

    def stop(self):
        """Stop the worker thread."""
        self._is_running = False
