"""
Pipeline Orchestrator

Coordinates the entire Speech-to-Sign pipeline:
Audio -> ASR -> NLP -> SiGML -> Output

Manages threads, queues, and graceful shutdown.
Optimized for Raspberry Pi 4 with proper signal handling.
"""

import logging
import queue
import threading
import time
import signal
import sys
from typing import Optional

from config.settings import pipeline_config, audio_config
from src.audio.audio_capture import AudioCaptureSystem as AudioCapture
from src.asr.asr_worker import ASRWorker
from src.nlp.gloss_mapper import GlossMapper
from src.sigml.generator import SiGMLGenerator
from src.sigml.avatar_player import CWASAPlayer, CWASAPlayerError
from src.nlp.dataclasses import TranscriptEvent, GlossPhrase, SiGMLOutput

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main coordinator for the SignVani pipeline.
    Optimized for Raspberry Pi 4 with graceful shutdown support.
    """

    def __init__(self, avatar_enabled: bool = True, avatar_auto_launch: bool = False):
        """
        Initialize pipeline components and queues.

        Args:
            avatar_enabled: Enable CWASA avatar rendering
            avatar_auto_launch: Auto-launch avatar player if not running
        """
        self._is_running = False
        self._shutdown_event = threading.Event()
        self._avatar_enabled = avatar_enabled

        # 1. Create Queues
        self.audio_queue = queue.Queue(
            maxsize=pipeline_config.AUDIO_QUEUE_SIZE)
        self.transcript_queue = queue.Queue(
            maxsize=pipeline_config.TRANSCRIPT_QUEUE_SIZE)

        # 2. Initialize Components
        logger.info("Initializing Audio Capture...")
        self.audio_capture = AudioCapture(
            output_queue=self.audio_queue,
            vad_enabled=audio_config.VAD_ENABLED,
            noise_filter_enabled=audio_config.NOISE_REDUCTION_ENABLED
        )

        logger.info("Initializing ASR Worker...")
        self.asr_worker = ASRWorker(
            input_queue=self.audio_queue,
            output_queue=self.transcript_queue
        )

        logger.info("Initializing NLP Engine...")
        self.gloss_mapper = GlossMapper()

        logger.info("Initializing SiGML Generator...")
        self.sigml_generator = SiGMLGenerator()

        # 3. Initialize Avatar Player (optional)
        self.avatar_player: Optional[CWASAPlayer] = None
        if self._avatar_enabled:
            logger.info("Initializing CWASA Avatar Player...")
            self.avatar_player = CWASAPlayer(auto_launch=avatar_auto_launch)
            if self.avatar_player.is_player_running():
                logger.info("CWASA Avatar Player connected")
            else:
                logger.info(
                    "CWASA Avatar Player not running (will send when available)")

        # Setup signal handlers for graceful shutdown (important for RPi)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown on RPi."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
            self.stop()

        # Register handlers for common termination signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # SIGHUP is available on Unix (RPi) but not on Windows
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)

    def start(self):
        """Start the pipeline."""
        logger.info("Starting SignVani Pipeline...")
        self._is_running = True
        self._shutdown_event.clear()

        # Start ASR Worker Thread
        self.asr_worker.start()

        # Start Audio Capture
        self.audio_capture.start()

        # Start Main Processing Loop (NLP + SiGML)
        self._process_loop()

    def _process_loop(self):
        """
        Main loop consuming transcripts and generating SiGML.
        Runs in the main thread. Optimized for RPi with proper shutdown handling.
        """
        logger.info("Pipeline ready. Listening...")

        try:
            while self._is_running and not self._shutdown_event.is_set():
                try:
                    # 1. Get Transcript (with timeout to check shutdown event)
                    event: TranscriptEvent = self.transcript_queue.get(
                        timeout=0.5)

                    if event.is_final:
                        self._handle_transcript(event)

                    self.transcript_queue.task_done()

                except queue.Empty:
                    # Check if shutdown was requested
                    if self._shutdown_event.is_set():
                        break
                    continue
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt received.")
                    break
                except Exception as e:
                    logger.error(f"Error in pipeline loop: {e}")

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received.")
        finally:
            self.stop()

    def _handle_transcript(self, event: TranscriptEvent):
        """Process a single transcript event."""
        text = event.text
        logger.info(f"Processing: '{text}'")

        try:
            # 2. NLP: Text -> Gloss
            gloss_phrase: GlossPhrase = self.gloss_mapper.process(text)
            logger.info(f"Glosses: {gloss_phrase.gloss_string}")

            # 3. SiGML: Gloss -> XML
            sigml_output: SiGMLOutput = self.sigml_generator.generate(
                gloss_phrase)

            # 4. Output (For now, just print/log)
            # In future, this would send to the Avatar Player
            self._emit_output(sigml_output)

        except Exception as e:
            logger.error(f"Failed to process transcript '{text}': {e}")

    def _emit_output(self, output: SiGMLOutput):
        """
        Emit final output to console and avatar player.

        Args:
            output: SiGMLOutput containing XML and metadata
        """
        # Console output
        print("\n" + "="*60)
        print(f"INPUT:  {output.original_text}")
        print(f"GLOSS:  {' '.join(output.glosses)}")
        print(f"SiGML:  {len(output.sigml_xml)} bytes generated")

        # Send to avatar player if enabled
        if self._avatar_enabled and self.avatar_player:
            try:
                if self.avatar_player.is_player_running():
                    self.avatar_player.send_sigml(output.sigml_xml)
                    print(f"AVATAR: ✓ Sent to CWASA player")
                else:
                    print(
                        f"AVATAR: ⚠ Player not running (launch with scripts/setup_avatar.py)")
            except CWASAPlayerError as e:
                logger.warning(f"Avatar player error: {e}")
                print(f"AVATAR: ✗ Error: {e}")

        print("="*60 + "\n")

    def stop(self):
        """Graceful shutdown with proper resource cleanup for RPi."""
        if not self._is_running:
            return

        logger.info("Stopping pipeline...")
        self._is_running = False
        self._shutdown_event.set()

        # Stop Audio capture first (stops feeding queue)
        if self.audio_capture:
            try:
                self.audio_capture.stop()
            except Exception as e:
                logger.warning(f"Error stopping audio capture: {e}")

        # Stop ASR worker with timeout
        if self.asr_worker:
            try:
                self.asr_worker.stop()
                self.asr_worker.join(
                    timeout=pipeline_config.GRACEFUL_SHUTDOWN_TIMEOUT)
                if self.asr_worker.is_alive():
                    logger.warning("ASR worker did not stop gracefully")
            except Exception as e:
                logger.warning(f"Error stopping ASR worker: {e}")

        # Drain remaining queues to prevent memory buildup
        self._drain_queues()

        logger.info("Pipeline stopped.")

    def _drain_queues(self):
        """Drain queues to free memory - important for RPi with limited RAM."""
        try:
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            while not self.transcript_queue.empty():
                self.transcript_queue.get_nowait()
        except queue.Empty:
            pass


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = PipelineOrchestrator()
    orchestrator.start()
