# SignVani - Offline Speech-to-Sign Language System

SignVani is a Raspberry Pi 4B-optimized offline Speech-to-Sign Language converter that transforms spoken English into Indian Sign Language (ISL) through visual 3D avatar animations.

## Overview

SignVani implements a three-stage sequential pipeline:

1. **Audio Acquisition**: Capture speech via audio jack (earphone microphone) → Vosk offline ASR → English transcript
2. **NLP Processing**: English text → Stop-word removal → Lemmatization → SVO to SOV transformation → ISL Gloss
3. **Visual Synthesis**: ISL Gloss → HamNoSys retrieval (SQLite) → SiGML generation → Real-time WebGL avatar streaming (SSE)

## Architecture

```
Audio Input (3.5mm Jack)
    ↓
PyAudio Capture + Spectral Noise Reduction
    ↓
Vosk Offline ASR Engine
    ↓
spaCy/NLTK NLP Pipeline (SVO→SOV)
    ↓
SQLite Gloss-to-HamNoSys Mapping
    ↓
SiGML XML Generation
    ↓
SSE Stream → Frontend WebGL Avatar Renderer
```

## Key Features

- **Fully Offline**: No cloud dependencies, runs entirely on Raspberry Pi 4B
- **Low Latency**: Vosk small model (~40MB) optimized for ARM CPUs
- **Lightweight Storage**: SQLite database for gloss mappings (no video files)
- **Real-time Streaming**: Server-Sent Events (SSE) for progressive avatar rendering
- **ISL Grammar Compliant**: Proper Subject-Object-Verb sentence structure
- **Smooth Animations**: Skeletal frame blending for natural transitions

## Hardware Requirements

- **Platform**: Raspberry Pi 4B (4GB+ RAM recommended)
- **Audio Input**: 3.5mm audio jack with earphone microphone
- **Display**: HDMI output for avatar visualization
- **Storage**: 8GB+ SD card (4GB for system, 2GB for models, 2GB for data)

## Project Structure

```
SignVani/
├── signvani_service/       # FastAPI microservice
│   ├── main.py            # FastAPI app with SSE endpoints
│   ├── audio_processor.py # PyAudio + Vosk ASR
│   ├── nlp_pipeline.py    # spaCy/NLTK gloss generation
│   ├── visual_synthesizer.py # HamNoSys + SiGML rendering
│   ├── database.py        # SQLite connection manager
│   └── models.py          # Pydantic data models
├── docs/                  # Technical documentation
│   ├── ARCHITECTURE.md    # System design and data flow
│   ├── API_REFERENCE.md   # FastAPI endpoint specifications
│   ├── RASPBERRY_PI_DEPLOYMENT.md # Pi 4B setup guide
│   ├── NLP_TRANSFORMATION_RULES.md # ISL grammar rules
│   └── DATABASE_SCHEMA.md # SQLite table structures
├── data/                  # SQLite database and seed data
│   ├── signvani.db       # Main database (generated)
│   ├── seed_gloss_mappings.json # Initial ISL gloss data
│   └── init_db.py        # Database initialization script
├── tests/                 # Unit tests
│   ├── test_audio.py
│   ├── test_nlp.py
│   └── test_visual.py
├── requirements.txt       # Python dependencies
├── config.py             # Configuration settings
└── README.md             # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd SignVani
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Initialize Database

```bash
cd data
python init_db.py
```

### 3. Download Vosk Model

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d signvani_service/models/
```

### 4. Start FastAPI Service

```bash
cd signvani_service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test Audio Processing

```bash
curl -X POST http://localhost:8000/api/convert-speech \
  -F "audio=@test_audio.wav"
```

## API Endpoints

### POST `/api/convert-speech`
Upload audio file → Returns SSE stream with conversion progress

**Request**:
```bash
curl -X POST http://localhost:8000/api/convert-speech \
  -F "audio=@recording.wav"
```

**Response** (SSE Stream):
```
event: stage
data: {"stage": "transcribing", "progress": 33}

event: stage
data: {"stage": "generating_gloss", "progress": 66, "text": "I am going to market"}

event: stage
data: {"stage": "rendering_avatar", "progress": 90, "gloss": "I MARKET GO"}

event: complete
data: {"sigml": "<sigml>...</sigml>", "video_url": null, "gloss": "I MARKET GO"}
```

### POST `/api/text-to-sign`
Convert text directly to sign language (bypass audio stage)

### GET `/api/gloss/{word}`
Retrieve HamNoSys notation for specific gloss word

### GET `/api/health`
Service health check

## Performance Optimization

### Raspberry Pi 4B Specific Tuning

1. **Vosk Model Selection**: Use `vosk-model-small-en-us-0.15` (40MB) instead of large models
2. **spaCy Model**: Use `en_core_web_sm` (12MB) for minimal memory footprint
3. **SQLite Optimization**: Enable WAL mode and create indexes on `gloss_word` column
4. **Audio Buffer**: 1024 frame buffer size for real-time capture without dropouts
5. **GPU Acceleration**: OpenGL ES hardware acceleration via VideoCore for avatar rendering

### Memory Usage

- Vosk Model: ~150MB RAM during transcription
- spaCy Model: ~80MB RAM during NLP processing
- SQLite Database: ~50MB disk, <10MB RAM
- FastAPI Service: ~100MB RAM
- **Total**: ~400MB RAM (fits comfortably in 4GB Pi 4B)

## ISL Grammar Rules

SignVani converts English SVO structure to ISL SOV structure:

**English Input**: "I am going to the market"

**Processing Steps**:
1. Tokenization: ["I", "am", "going", "to", "the", "market"]
2. Stop-word removal: ["I", "going", "market"]
3. Lemmatization: ["I", "go", "market"]
4. SVO→SOV transformation: ["I", "market", "go"]
5. Gloss formatting: "I MARKET GO"

**Output**: ISL Gloss rendered as 3D avatar animation

## Database Schema

### `gloss_hamnosys_mappings` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| gloss_word | TEXT NOT NULL | ISL gloss word (uppercase) |
| hamnosys_xml | TEXT NOT NULL | HamNoSys notation in XML format |
| english_word | TEXT | Corresponding English word |
| confidence_score | REAL | Mapping confidence (0.0-1.0) |
| region | TEXT | Regional variant (e.g., "Mumbai", "Delhi") |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes**: `idx_gloss_word`, `idx_english_word`

## Development Roadmap

### Phase 1: Core Pipeline (Current)
- [x] Audio acquisition with PyAudio
- [x] Vosk ASR integration
- [x] NLP gloss generation
- [x] SQLite database schema
- [x] SSE streaming endpoint

### Phase 2: Enhanced Features
- [ ] Real-time microphone streaming (not just file upload)
- [ ] Multi-region ISL variants (Mumbai, Delhi, Bangalore)
- [ ] Emotion detection for facial expressions
- [ ] Caching layer for frequent phrases
- [ ] WebRTC for lower latency streaming

### Phase 3: Production Deployment
- [ ] Docker containerization
- [ ] Systemd service configuration
- [ ] Auto-start on Pi boot
- [ ] Logging and monitoring
- [ ] Error recovery mechanisms

## Contributing

See [docs/](docs/) folder for detailed technical documentation:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and component interaction
- [API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API documentation
- [RASPBERRY_PI_DEPLOYMENT.md](docs/RASPBERRY_PI_DEPLOYMENT.md) - Deployment guide
- [NLP_TRANSFORMATION_RULES.md](docs/NLP_TRANSFORMATION_RULES.md) - ISL grammar rules

## License

MIT License - See project root LICENSE file

## Credits

- **Vosk**: Offline speech recognition engine
- **spaCy**: Industrial-strength NLP library
- **HamNoSys**: Hamburg Notation System for sign language
- **CWASA**: CWA Sign Avatar WebGL renderer
- **ISL Dictionary**: Indian Sign Language reference data

## Support

For issues and questions, please refer to the documentation in [docs/](docs/) folder.

---

**Built with ❤️ for the deaf and hard-of-hearing community**
