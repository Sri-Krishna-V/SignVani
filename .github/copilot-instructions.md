# SignVani Copilot Instructions

SignVani is an offline, low-latency Speech-to-Indian Sign Language translator for Raspberry Pi 4.
Focus on memory efficiency, low latency, and thread safety.

## Architecture & Patterns

- **Offline-First**: No cloud APIs. All processing is local.
- **Pipeline**: Audio Capture -> VAD -> Noise Filter -> Buffer -> ASR Worker -> NLP -> Database -> SiGML.
- **Memory Optimization**:
  - Use `__slots__` for data classes (e.g., `src/nlp/dataclasses.py`).
  - Use `np.float32` for audio data to save memory.
  - Avoid heavy libraries where lightweight alternatives exist.
- **Thread Safety**:
  - Use `queue.Queue` for inter-thread communication.
  - Implement Singleton pattern for heavy resources like `VoskEngine` (`src/asr/vosk_engine.py`).
  - Ensure thread-safe access to shared buffers (`CircularAudioBuffer`).
- **Configuration**:
  - Use `config/settings.py` with frozen dataclasses (`@dataclass(frozen=True)`).
  - Do not hardcode values; reference `audio_config`, `vosk_config`, etc.

## Development Workflow

- **Setup**: Run `python scripts/setup_models.py` to download Vosk and NLTK models.
- **Running**: Execute `python main.py` to start the application.
- **Testing**:
  - Unit Tests: `python -m tests.unit.test_audio`, `python -m tests.unit.test_asr`
  - Integration: `python -m tests.integration.test_pipeline_phase1_2`
  - Always run tests from the project root.

## Key Files

- `src/nlp/dataclasses.py`: Core data structures (`AudioChunk`, `TranscriptEvent`).
- `config/settings.py`: Central configuration.
- `src/asr/vosk_engine.py`: ASR implementation.
- `src/audio/audio_capture.py`: Audio capture logic.

## Coding Standards

- **Type Hints**: Use `typing` module for all function signatures.
- **Docstrings**: Follow Google style docstrings.
- **Imports**: Group imports: standard library, third-party, local application.
- **Error Handling**: Use custom exceptions from `src/utils/exceptions.py`.
