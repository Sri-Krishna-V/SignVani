# SignVani

**Speech-to-Indian Sign Language Translator for Raspberry Pi 4**

SignVani is an offline, low-latency system that translates spoken English into Indian Sign Language (ISL) using HamNoSys notation and SiGML output for 3D avatar rendering.

## Features

- **Fully Offline**: No cloud APIs required - runs entirely on Raspberry Pi 4
- **Low Latency**: Target <1s end-to-end processing time
- **Resource Efficient**: Optimized for ARM Cortex-A72 with MicroPython-style efficiency
- **Real-time Processing**: Audio capture → ASR → NLP → Database → SiGML pipeline

## Architecture

```
Audio Input → Noise Reduction → Vosk ASR → NLP Processing → SQLite Lookup → SiGML Output
   (PyAudio)    (Spectral Sub)   (Offline)  (SVO→SOV)      (Gloss→HamNoSys)
```

## Hardware Requirements

- **Raspberry Pi 4 Model B** (4GB RAM recommended)
- **Microphone**: USB or 3.5mm audio input
- **Operating System**: Raspberry Pi OS (64-bit)

## Software Stack

- **ASR**: Vosk (offline speech recognition)
- **Audio Processing**: PyAudio + scipy (spectral subtraction)
- **NLP**: NLTK (lightweight tokenization and lemmatization)
- **Database**: SQLite (English gloss → HamNoSys mapping)
- **Output**: SiGML XML generation

## Installation

### Prerequisites

On **Windows** (for development):
```bash
# Install PyAudio using pipwin (easier on Windows)
pip install pipwin
pipwin install pyaudio

# Install other dependencies
pip install -r requirements.txt
```

On **Linux/Raspberry Pi OS**:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev libasound2-dev

# Install Python dependencies
pip3 install -r requirements.txt
```

### Download Models

```bash
# Auto-download Vosk model and NLTK data
python scripts/setup_models.py
```

This will download:
- **Vosk model**: `vosk-model-small-en-in-0.4` (~40MB) - Indian English ASR
- **NLTK data**: punkt, wordnet, stopwords (~24MB total)

### Install SignVani

```bash
# Development mode (editable install)
pip install -e .

# Or production mode
pip install .
```

## Usage

### Run SignVani

```bash
# Using Python module
python main.py

# Or if installed as package
signvani
```

### Configuration

Edit `config/settings.py` to customize:
- Audio parameters (sample rate, buffer size)
- Vosk model path
- NLP settings (tokenization, grammar transformation)
- Database settings (cache size, connection pool)
- Pipeline settings (queue sizes, timeouts)

## Project Structure

```
sign-vani/
├── config/              # Configuration settings
├── src/
│   ├── audio/          # Audio capture and preprocessing
│   ├── asr/            # Vosk ASR engine
│   ├── nlp/            # NLP and grammar transformation
│   ├── database/       # SQLite database layer
│   ├── sigml/          # SiGML generation
│   ├── utils/          # Utility functions and exceptions
│   └── pipeline/       # Pipeline orchestration
├── models/
│   ├── vosk/           # Vosk ASR models
│   └── nltk_data/      # NLTK corpus data
├── data/               # SQLite database
├── tests/              # Unit, integration, and performance tests
├── scripts/            # Setup and deployment scripts
└── assets/             # Test audio files
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Performance Targets

- **End-to-end latency**: <1 second
- **Memory footprint**: <500MB (excluding OS)
- **CPU usage**: <80% on Raspberry Pi 4
- **ASR accuracy**: >80% for Indian English

## Architecture Details

### Thread Pipeline

```
Main Thread (Control)
├─► Audio Thread: PyAudio → VAD → Noise Filter → Queue[AudioChunk]
├─► ASR Thread: Vosk Processing → Queue[TranscriptEvent]
├─► NLP Thread: Tokenize → SVO→SOV Transform → Queue[GlossPhrase]
└─► DB Thread: SQLite Lookup → SiGML Generation
```

### Grammar Transformation

SignVani transforms English Subject-Verb-Object (SVO) word order to Indian Sign Language's Subject-Object-Verb (SOV) structure:

- **Input**: "I eat apple"
- **Output**: "I apple eat"

### Database Schema

SQLite database stores English gloss to HamNoSys notation mappings:

- **english_gloss**: Uppercase sign name (e.g., "HELLO")
- **hamnosys_string**: HamNoSys notation for the sign
- **frequency**: Usage count for LRU caching
- **Full-text search**: FTS5 for fuzzy matching unknown words

## Deployment to Raspberry Pi 4

```bash
# Transfer project to RPi4
scp -r sign-vani/ pi@raspberrypi:~/

# SSH into RPi4
ssh pi@raspberrypi

# Run deployment script
cd sign-vani
bash scripts/deploy_rpi.sh
```

The deployment script will:
1. Install system dependencies
2. Install Python packages
3. Download models
4. Initialize database
5. Create systemd service for auto-start

## Optimization Philosophy

SignVani follows **MicroPython-style efficiency** principles:

- **Memory**: Use `__slots__` for data classes, `float32` instead of `float64`
- **Generators**: Prefer streaming over loading full data into memory
- **Threading**: Non-blocking pipeline with queue-based communication
- **Caching**: LRU cache for frequently accessed data
- **Database**: Optimized indexes and query patterns for embedded systems

## Roadmap

### Phase 1 ✅ (Current)
- [x] Project scaffolding
- [ ] Audio subsystem (PyAudio + noise reduction)
- [ ] ASR integration (Vosk)
- [ ] Database layer (SQLite)

### Phase 2
- [ ] NLP engine (SVO→SOV transformation)
- [ ] SiGML generation
- [ ] Pipeline integration

### Phase 3
- [ ] RPi4 deployment and optimization
- [ ] Performance profiling and tuning
- [ ] Load testing

### Future Enhancements
- [ ] Additional ISL grammar rules (tense, classifiers, spatial agreement)
- [ ] Real HamNoSys data integration
- [ ] Expanded vocabulary (100+ signs)
- [ ] Fingerspelling for unknown words
- [ ] Avatar player integration

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Vosk**: Open-source speech recognition toolkit
- **NLTK**: Natural Language Toolkit
- **HamNoSys**: Hamburg Notation System for sign languages
- **SiGML**: Signing Gesture Markup Language

## Contact

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ for the deaf community**
