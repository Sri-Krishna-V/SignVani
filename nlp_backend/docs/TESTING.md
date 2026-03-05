# Testing Guide

We use `unittest` for testing. Tests are located in the `tests/` directory.

## Running Tests

### Unit Tests

Run unit tests to verify individual components.

**Audio Subsystem**:

```bash
python -m tests.unit.test_audio
```

*Verifies VAD logic, Noise Filter calibration, and Buffer overflow handling.*

**ASR Subsystem**:

```bash
python -m tests.unit.test_asr
```

*Verifies VoskEngine initialization and ASRWorker logic.*

### Integration Tests

Run integration tests to verify the interaction between subsystems.

**Phase 1 & 2 Pipeline (Audio + ASR)**:

```bash
python -m tests.integration.test_pipeline_phase1_2
```

*Simulates audio capture and verifies that the ASR worker produces transcripts. Also verifies that the real Vosk model can be loaded.*

## Test Coverage

* **Audio**: VAD (Silence/Speech), Noise Filter (Shape/Calibration), Buffer (Overflow).
* **ASR**: Engine Singleton, Worker Queue Processing.
* **Integration**: End-to-end flow from AudioChunk to TranscriptEvent.
