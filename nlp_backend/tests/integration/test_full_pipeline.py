"""
Integration tests for the full pipeline (Phase 6).
"""
import unittest
import queue
import threading
import time
from unittest.mock import MagicMock, patch

from src.pipeline.orchestrator import PipelineOrchestrator
from src.nlp.dataclasses import TranscriptEvent


class TestPipelineIntegration(unittest.TestCase):

    @patch('src.pipeline.orchestrator.AudioCapture')
    @patch('src.pipeline.orchestrator.ASRWorker')
    @patch('src.pipeline.orchestrator.GlossMapper')
    @patch('src.pipeline.orchestrator.SiGMLGenerator')
    def test_pipeline_flow(self, MockSiGML, MockNLP, MockASR, MockAudio):
        """
        Test the flow from Transcript -> NLP -> SiGML -> Output
        We mock Audio and ASR to inject a transcript directly into the queue.
        """
        # Setup Mocks
        mock_nlp = MockNLP.return_value
        mock_sigml = MockSiGML.return_value

        # Mock NLP output
        mock_gloss_phrase = MagicMock()
        mock_gloss_phrase.gloss_string = "HELLO WORLD"
        mock_gloss_phrase.glosses = ["HELLO", "WORLD"]
        mock_nlp.process.return_value = mock_gloss_phrase

        # Mock SiGML output
        mock_sigml_output = MagicMock()
        mock_sigml_output.sigml_xml = "<sigml>...</sigml>"
        mock_sigml_output.glosses = ["HELLO", "WORLD"]
        mock_sigml_output.original_text = "Hello world"
        mock_sigml.generate.return_value = mock_sigml_output

        # Initialize Orchestrator
        orchestrator = PipelineOrchestrator()

        # Inject a transcript event directly into the queue
        event = TranscriptEvent(text="Hello world", is_final=True)
        orchestrator.transcript_queue.put(event)

        # Run _handle_transcript directly (to avoid threading issues in test)
        # In real run, _process_loop calls this.
        orchestrator._handle_transcript(event)

        # Verify interactions
        mock_nlp.process.assert_called_with("Hello world")
        mock_sigml.generate.assert_called_with(mock_gloss_phrase)

        # Verify output (we can't easily check print, but we verified the calls)


if __name__ == '__main__':
    unittest.main()
