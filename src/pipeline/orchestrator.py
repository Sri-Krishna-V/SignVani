"""
Pipeline Orchestrator

Coordinates the entire Speech-to-Sign pipeline:
Audio -> ASR -> NLP -> SiGML -> Output

Manages threads, queues, and graceful shutdown.
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
from src.nlp.dataclasses import TranscriptEvent, GlossPhrase, SiGMLOutput

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main coordinator for the SignVani pipeline.
    """

    def __init__(self):
        """Initialize pipeline components and queues."""
        self._is_running = False
        
        # 1. Create Queues
        self.audio_queue = queue.Queue(maxsize=pipeline_config.AUDIO_QUEUE_SIZE)
        self.transcript_queue = queue.Queue(maxsize=pipeline_config.TRANSCRIPT_QUEUE_SIZE)
        
        # 2. Initialize Components
        logger.info("Initializing Audio Capture...")
        self.audio_capture = AudioCapture(
            sample_rate=audio_config.SAMPLE_RATE,
            chunk_size=audio_config.FRAMES_PER_BUFFER,
            output_queue=self.audio_queue
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

    def start(self):
        """Start the pipeline."""
        logger.info("Starting SignVani Pipeline...")
        self._is_running = True
        
        # Start ASR Worker Thread
        self.asr_worker.start()
        
        # Start Audio Capture
        self.audio_capture.start()
        
        # Start Main Processing Loop (NLP + SiGML)
        self._process_loop()

    def _process_loop(self):
        """
        Main loop consuming transcripts and generating SiGML.
        Runs in the main thread.
        """
        logger.info("Pipeline ready. Listening...")
        
        try:
            while self._is_running:
                try:
                    # 1. Get Transcript
                    event: TranscriptEvent = self.transcript_queue.get(timeout=0.5)
                    
                    if event.is_final:
                        self._handle_transcript(event)
                    
                    self.transcript_queue.task_done()
                    
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt received.")
                    self.stop()
                except Exception as e:
                    logger.error(f"Error in pipeline loop: {e}")
                    
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received.")
            self.stop()
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
            sigml_output: SiGMLOutput = self.sigml_generator.generate(gloss_phrase)
            
            # 4. Output (For now, just print/log)
            # In future, this would send to the Avatar Player
            self._emit_output(sigml_output)
            
        except Exception as e:
            logger.error(f"Failed to process transcript '{text}': {e}")

    def _emit_output(self, output: SiGMLOutput):
        """Emit final output."""
        print("\n" + "="*40)
        print(f"INPUT:  {output.original_text}")
        print(f"GLOSS:  {' '.join(output.glosses)}")
        print(f"SiGML:  {len(output.sigml_xml)} bytes generated")
        print("="*40 + "\n")

    def stop(self):
        """Graceful shutdown."""
        if not self._is_running:
            return
            
        logger.info("Stopping pipeline...")
        self._is_running = False
        
        # Stop Audio
        if self.audio_capture:
            self.audio_capture.stop()
            
        # Stop ASR
        if self.asr_worker:
            self.asr_worker.stop()
            self.asr_worker.join(timeout=2.0)
            
        logger.info("Pipeline stopped.")
        sys.exit(0)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = PipelineOrchestrator()
    orchestrator.start()
