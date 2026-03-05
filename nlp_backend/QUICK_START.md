# Quick Start Guide

## Activate Virtual Environment
```bash
cd /home/labs/Desktop/SignVani
source .venv/bin/activate
```

## Run Tests
```bash
# Audio subsystem
python -m tests.unit.test_audio

# ASR subsystem  
python -m tests.unit.test_asr

# Full integration (audio + ASR)
python -m tests.integration.test_pipeline_phase1_2
```

## Project Status
- ✅ Phase 0: Scaffolding
- ✅ Phase 1: Audio Subsystem
- ✅ Phase 2: ASR Integration
- ⏳ Phase 3: Database Layer
- ⏳ Phase 4: NLP Engine
- ⏳ Phase 5: SiGML Generation
- ⏳ Phase 6: Pipeline Integration

## Key Directories
- `src/` - Source code
- `config/` - Configuration settings
- `models/` - Downloaded Vosk model & NLTK data
- `tests/` - Test suite
- `docs/` - Documentation

## Dependencies
- Vosk 0.3.45 (Offline ASR)
- PyAudio 0.2.14 (Audio I/O)
- NumPy 2.4.0 (Numerical computing)
- SciPy 1.16.3 (Signal processing)
- NLTK 3.9.2 (NLP)

## Documentation
- `docs/ARCHITECTURE.md` - System design
- `docs/SETUP.md` - Installation guide
- `docs/API.md` - API reference
- `docs/STATUS.md` - Project progress
