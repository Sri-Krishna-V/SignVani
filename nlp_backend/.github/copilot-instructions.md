# SignVani Copilot Instructions

SignVani is an offline Speech-to-Indian Sign Language translator optimized for Raspberry Pi 4.
Target: <1s latency, <500MB RAM. All processing is local—no cloud APIs.

## Architecture

**Pipeline flow** (see [orchestrator.py](src/pipeline/orchestrator.py)):
```
Mic → AudioCapture → VAD → NoiseFilter → CircularBuffer → queue.Queue
  → ASRWorker (Vosk) → TranscriptQueue → NLP (SVO→SOV) → Database → SiGML → Avatar
```

**Key patterns**:
- **Singleton** for heavy resources: `VoskEngine`, `DatabaseManager` use `_instance`/`_lock` pattern
- **Thread-safe queues**: Components communicate via `queue.Queue` with configurable sizes
- **Frozen dataclasses**: All config in [config/settings.py](config/settings.py) uses `@dataclass(frozen=True)`

## Memory Optimization (Critical for RPi4)

```python
# ALWAYS use __slots__ for data classes (saves ~50% memory)
class AudioChunk:
    __slots__ = ('data', 'timestamp', 'sample_rate')
    
# ALWAYS use np.float32 for audio data
self.data = data.astype(np.float32) if data.dtype != np.float32 else data
```

Reference: [src/nlp/dataclasses.py](src/nlp/dataclasses.py) for all core data structures.

## Configuration

Never hardcode values. Import from `config/settings.py`:
```python
from config.settings import audio_config, vosk_config, pipeline_config
# Use: audio_config.SAMPLE_RATE, pipeline_config.AUDIO_QUEUE_SIZE
```

## Exception Handling

Use domain-specific exceptions from [src/utils/exceptions.py](src/utils/exceptions.py):
```python
from src.utils.exceptions import ModelLoadError, ASRError, DatabaseError
# Hierarchy: SignVaniError → AudioError → AudioCaptureError
```

## Commands

```bash
# Setup (downloads Vosk model + NLTK data)
python scripts/setup_models.py

# Run live audio mode
python main.py

# Run text mode (skip audio/ASR)
python main.py --text "Hello I am Krishna" --no-avatar

# Tests (always from project root)
python -m tests.unit.test_nlp
python -m tests.integration.test_pipeline_phase1_2
```

## Testing Conventions

- Use `unittest` with `unittest.mock` for isolation
- Mock heavy resources: `@patch('src.asr.asr_worker.VoskEngine')`
- Integration tests verify queue-based data flow between components
- See [tests/integration/test_pipeline_phase1_2.py](tests/integration/test_pipeline_phase1_2.py) for pattern

## Database

- SQLite with connection pooling (`DatabaseManager` singleton)
- Schema: [src/database/schema.sql](src/database/schema.sql)
- Seed data: `seed_database()` from [src/database/seed_db.py](src/database/seed_db.py)
- HamNoSys mappings in [src/database/hamnosys_data.py](src/database/hamnosys_data.py)

## Code Style

- **Type hints**: Required for all function signatures
- **Docstrings**: Google style
- **Imports**: Group as stdlib → third-party → local (`from src.x import y`)
- **Lock timeouts**: Always use `acquire(timeout=N)` to prevent RPi deadlocks