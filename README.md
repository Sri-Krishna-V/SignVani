<div align="center">

# SignVani

### Offline Speech-to-Indian Sign Language Translator

### Optimised for Raspberry Pi 4B

**Vani** (Sanskrit: वाणी) — *voice, speech*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-17-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-r136-black?logo=threedotjs)](https://threejs.org)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204B-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com)
[![Offline](https://img.shields.io/badge/Processing-100%25%20Offline-brightgreen)](#)
[![Latency](https://img.shields.io/badge/Latency-%3C1s%20E2E-blue)](#performance)

</div>

---

SignVani converts spoken and written English into animated **Indian Sign Language (ISL)** gestures in real time, displayed through a rigged 3D avatar rendered in the browser. The entire processing pipeline — speech recognition, natural language processing, grammar transformation, gloss lookup, and animation generation — runs **fully offline** on a Raspberry Pi 4B with no cloud dependencies.

---

## Table of Contents

- [Hardware Target](#hardware-target)
- [System Architecture](#system-architecture)
- [Data Flow](#data-flow)
- [ISL Linguistic Pipeline](#isl-linguistic-pipeline)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started — Raspberry Pi 4B](#getting-started--raspberry-pi-4b)
- [Getting Started — Development](#getting-started--development)
- [API Reference](#api-reference)
- [Performance](#performance)
- [RPi4 Optimisations](#rpi4-optimisations)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [User Research](#user-research)
- [Documentation](#documentation)

---

## Hardware Target

SignVani is purpose-built and tuned for the Raspberry Pi 4B. All design decisions — FFT size, thread counts, connection pool depth, WebGL precision, render frame rate — are governed by the constraints of this platform.

| Component | Specification |
|-----------|--------------|
| **SoC** | Broadcom BCM2711 |
| **CPU** | Quad-core ARM Cortex-A72 @ 1.8 GHz (64-bit) |
| **GPU** | VideoCore VI (OpenGL ES 3.1) |
| **RAM** | 4 GB LPDDR4-3200 (recommended) |
| **Storage** | MicroSD (Class 10 / UHS-I or better) |
| **OS** | Raspberry Pi OS 64-bit (Bookworm) |
| **Audio** | USB microphone or 3.5mm input via USB audio adapter |
| **Network** | Not required at runtime (100% offline) |

---

## System Architecture

SignVani's architecture is broken into five focused diagrams rather than one dense one — each covers a single concern end to end.

### High-Level Overview

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#3B82F6', 'primaryTextColor': '#0F172A', 'primaryBorderColor': '#1E40AF', 'lineColor': '#334155', 'clusterBkg': '#F8FAFC', 'clusterBorder': '#CBD5E1', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart LR
    User(["User"])
    Client["Browser Client<br/>React · Three.js · Port 3000"]
    API["FastAPI Backend<br/>Port 8000"]
    ASR["Speech Recognition<br/>faster-whisper / Vosk"]
    NLP["NLP + Grammar Pipeline<br/>English → ISL gloss"]
    Data["SQLite + FTS5<br/>Gloss → HamNoSys"]
    Gen["Animation Generator<br/>Three.js keyframes"]
    Avatar["3D Avatar<br/>renders ISL signs"]

    User -->|text or recorded speech| Client
    Client -->|REST request| API
    API --> ASR --> NLP
    API --> NLP
    NLP --> Data --> Gen --> API
    API -->|JSON response| Client --> Avatar -->|ISL animation| User

    classDef client fill:#3B82F6,stroke:#1E40AF,color:#FFFFFF;
    classDef asr fill:#F59E0B,stroke:#B45309,color:#111827;
    classDef nlp fill:#8B5CF6,stroke:#6D28D9,color:#FFFFFF;
    classDef data fill:#EC4899,stroke:#BE185D,color:#FFFFFF;
    classDef render fill:#06B6D4,stroke:#0E7490,color:#FFFFFF;
    classDef user fill:#FDE047,stroke:#CA8A04,color:#111827;

    class User user;
    class Client,Avatar client;
    class API,NLP nlp;
    class ASR asr;
    class Data data;
    class Gen render;
```

### ASR Engine Selection

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#F59E0B', 'primaryTextColor': '#111827', 'primaryBorderColor': '#B45309', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart LR
    Env["ASR_ENGINE env var<br/>default: faster_whisper"] --> Factory["get_asr_engine()<br/>src/asr/vosk_integration.py"]
    Factory -->|faster_whisper| Whisper["WhisperASR<br/>tiny.en · int8 · greedy decode"]
    Factory -->|vosk| Vosk["VoskASR<br/>small-en-in-0.4 · Indian English"]
    Whisper --> Out["Transcript"]
    Vosk --> Out

    classDef infra fill:#EF4444,stroke:#B91C1C,color:#FFFFFF;
    classDef asr fill:#F59E0B,stroke:#B45309,color:#111827;
    classDef output fill:#10B981,stroke:#047857,color:#FFFFFF;

    class Env,Factory infra;
    class Whisper,Vosk asr;
    class Out output;
```

Both endpoints that accept audio (`/api/speech-to-handsign`, `/api/speech-to-sign`) call this same factory — the engine choice is a single environment variable, not a code path fork.

### Real-Time Audio Pipeline (Built, Not Wired In)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#10B981', 'primaryTextColor': '#0F172A', 'primaryBorderColor': '#047857', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart LR
    Mic(["Microphone"]) --> Capture["AudioCaptureSystem<br/>PyAudio · 16 kHz callback"]
    Capture --> VAD["VoiceActivityDetector<br/>RMS thresholding"]
    VAD --> Filter["SpectralSubtractor<br/>FFT-512 noise reduction"]
    Filter --> Buffer["CircularAudioBuffer<br/>bounded ring buffer"]
    Buffer --> Worker["ASRWorker /<br/>WhisperASRWorker"]
    Worker --> Orchestrator["PipelineOrchestrator"]
    Orchestrator -.-> Note["⚠ Fully implemented and tested, but PipelineOrchestrator<br/>is commented out at startup in api_server.py, and<br/>/ws/live-speech is currently a stub that never calls ASR —<br/>this chain is not on any active request path today"]

    classDef audio fill:#10B981,stroke:#047857,color:#FFFFFF;
    classDef legacy fill:#94A3B8,stroke:#475569,color:#111827;
    classDef user fill:#FDE047,stroke:#CA8A04,color:#111827;

    class Mic user;
    class Capture,VAD,Filter,Buffer,Worker,Orchestrator audio;
    class Note legacy;
```

The two live endpoints instead take an already-recorded WAV upload straight to ASR — see [Data Flow](#data-flow) below.

### Data, Lookup & Rendering Generation

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#EC4899', 'primaryTextColor': '#0F172A', 'primaryBorderColor': '#BE185D', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart LR
    Gloss["Gloss Sequence<br/>from NLP pipeline"] --> Cache["LRU Cache<br/>200 entries"]
    Cache --> DB["SQLite + FTS5<br/>gloss_mapping · HamNoSys data"]
    DB -->|HamNoSys lookup| Keyframes["HandsignGenerator<br/>HamNoSys → Three.js keyframes"]
    DB -->|HamNoSys lookup| SiGML["SiGMLGenerator<br/>HamNoSys → SiGML XML"]
    Keyframes -->|primary, active path| Browser["Browser Three.js Avatar"]
    SiGML -.->|optional, not started by default| CWASA["CWASAPlayer<br/>TCP :8052 · legacy avatar player"]

    classDef data fill:#EC4899,stroke:#BE185D,color:#FFFFFF;
    classDef render fill:#06B6D4,stroke:#0E7490,color:#FFFFFF;
    classDef legacy fill:#94A3B8,stroke:#475569,color:#111827;

    class Gloss,Cache,DB,SiGML data;
    class Keyframes,Browser render;
    class CWASA legacy;
```

### Startup & Orchestration

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#EF4444', 'primaryTextColor': '#0F172A', 'primaryBorderColor': '#B91C1C', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart TD
    Start(["./start.sh<br/>repo root"]) --> Venv["Activate nlp_backend/.venv"]
    Venv --> Backend["Launch FastAPI backend<br/>ASR_ENGINE=$ASR_ENGINE python api_server.py"]
    Backend --> Poll["Poll /api/health<br/>up to 60s"]
    Poll -->|healthy| Frontend["Launch React dev server<br/>REACT_APP_API_URL=http://localhost:8000 npm start"]
    Frontend --> Banner["Print status banner<br/>ports 3000 / 8000 · active ASR engine"]
    Banner --> Trap["trap cleanup EXIT INT TERM"]
    Trap -->|Ctrl+C| Stop["Kill BACKEND_PID + FRONTEND_PID"]

    classDef infra fill:#EF4444,stroke:#B91C1C,color:#FFFFFF;
    classDef user fill:#FDE047,stroke:#CA8A04,color:#111827;

    class Start user;
    class Venv,Backend,Poll,Frontend,Banner,Trap,Stop infra;
```

### Legacy & Optional Components

Not every dependency in this repo is part of the offline ISL pipeline:

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#94A3B8', 'primaryTextColor': '#111827', 'primaryBorderColor': '#475569', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart LR
    Pages["CreateVideo · Videos · Video pages"] -.->|requires network| Heroku["sign-kit-api.herokuapp.com<br/>legacy Node.js video API"]
    SiGML["SiGMLGenerator output"] -.->|requires network| CWASA["CWASAPlayer<br/>TCP :8052"]

    classDef client fill:#3B82F6,stroke:#1E40AF,color:#FFFFFF;
    classDef data fill:#EC4899,stroke:#BE185D,color:#FFFFFF;
    classDef legacy fill:#94A3B8,stroke:#475569,color:#111827;

    class Pages client;
    class SiGML data;
    class Heroku,CWASA legacy;
```

`CreateVideo`/`Videos`/`Video` (`client/src/Config/config.js`) call a Heroku-hosted video API and are **not** offline — everything else in this README is.

---

## Data Flow

### Text → Sign (Backend Mode)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#3B82F6', 'primaryBorderColor': '#1E40AF', 'primaryTextColor': '#0F172A', 'lineColor': '#334155', 'signalColor': '#1E40AF', 'signalTextColor': '#0F172A', 'actorBorder': '#1E40AF', 'actorBkg': '#3B82F6', 'actorTextColor': '#FFFFFF', 'activationBorderColor': '#1E40AF', 'activationBkgColor': '#93C5FD', 'noteBkgColor': '#FDE047', 'noteBorderColor': '#CA8A04', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
sequenceDiagram
    autonumber
    actor U as User
    participant C as React Client
    participant B as FastAPI Backend
    participant N as NLP Pipeline
    participant DB as SQLite + FTS5

    U->>C: Enter English text
    C->>B: POST /api/text-to-handsign
    B->>N: Tokenise, tag, and lemmatise
    Note over N: I am going to the market<br/>→ I go market
    N->>N: Reorder to ISL-friendly SOV gloss
    Note over N: I go market<br/>→ I MARKET GO
    N->>DB: Lookup HamNoSys codes
    DB-->>N: Gloss mappings
    N-->>B: Generate keyframe payload
    B-->>C: gloss + animations + duration
    C->>C: Queue animations in useAnimationEngine
    C-->>U: Render signed output on avatar
```

### Speech → Sign (Recorded Upload)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#10B981', 'primaryBorderColor': '#047857', 'primaryTextColor': '#0F172A', 'lineColor': '#334155', 'signalColor': '#047857', 'signalTextColor': '#0F172A', 'actorBorder': '#047857', 'actorBkg': '#10B981', 'actorTextColor': '#FFFFFF', 'activationBorderColor': '#047857', 'activationBkgColor': '#6EE7B7', 'noteBkgColor': '#FDE047', 'noteBorderColor': '#CA8A04', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
sequenceDiagram
    autonumber
    actor U as User
    participant C as React Client
    participant B as FastAPI Backend
    participant A as Active ASR Engine
    participant N as NLP Pipeline

    U->>C: Click record, then stop
    C->>C: Capture WebM audio (MediaRecorder)
    C->>C: Convert to 16 kHz mono WAV client-side
    C->>B: POST /api/speech-to-handsign (WAV upload)
    Note over B,A: ASR_ENGINE selects faster-whisper or Vosk
    B->>A: Normalise and transcribe uploaded WAV
    A-->>B: Transcript with confidence
    B->>N: Run ISL transformation pipeline
    N-->>B: Gloss sequence + animation payload
    B-->>C: original_text + gloss + animations
    C-->>U: Play signed response
```

This is a request/response upload, not a live streaming mic — the `/ws/live-speech` WebSocket exists for that but currently only echoes a placeholder (see [Real-Time Audio Pipeline](#real-time-audio-pipeline-built-not-wired-in)).

### Built-in Animations (No Backend)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#F59E0B', 'primaryBorderColor': '#B45309', 'primaryTextColor': '#111827', 'lineColor': '#334155', 'signalColor': '#B45309', 'signalTextColor': '#0F172A', 'actorBorder': '#B45309', 'actorBkg': '#F59E0B', 'actorTextColor': '#111827', 'activationBorderColor': '#B45309', 'activationBkgColor': '#FCD34D', 'noteBkgColor': '#FDE047', 'noteBorderColor': '#CA8A04', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
sequenceDiagram
    autonumber
    actor U as User
    participant AP as animationPlayer.js
    participant WD as wordsData.json
    participant AZ as Alphabets A-Z
    participant AE as useAnimationEngine

    U->>AP: playString("HELLO")
    AP->>WD: Lookup word-level keyframes
    alt Word animation exists
        WD-->>AP: Return stored bone transforms
    else Fallback required
        AP->>AZ: Resolve letter-by-letter signs
        AZ-->>AP: Alphabet animation frames
    end
    AP->>AE: Queue animation frames
    loop 30 fps render loop
        AE->>AE: Apply transforms to avatar skeleton
        AE->>AE: Render scene with Three.js
    end
    AE-->>U: Display local signing animation
```

---

## ISL Linguistic Pipeline

SignVani implements a 7-stage pipeline to transform raw English text into ISL-compatible gloss sequences. ISL follows **Subject-Object-Verb (SOV)** word order, the inverse of English's SVO.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#3B82F6', 'primaryBorderColor': '#1E40AF', 'primaryTextColor': '#0F172A', 'lineColor': '#334155', 'fontFamily': 'Inter, Segoe UI, Arial' }}}%%
flowchart TD
    Input["Input Sentence<br/>I am going to the market"] --> C1["1. Contraction Expansion<br/>don't → do not"]
    C1 --> C2["2. Tokenisation<br/>I · am · going · to · the · market"]
    C2 --> C3["3. POS Tagging<br/>PRP · VBZ · VBG · TO · DT · NN"]
    C3 --> C4["4. Lemmatisation<br/>going → go"]
    C4 --> C5["5. Stopword Removal<br/>I · go · market"]
    C5 --> C6["6. SVO to SOV Reordering<br/>I · MARKET · GO"]
    C6 --> C7["7. Gloss Lookup<br/>SQLite FTS5 exact and fuzzy match"]
    C7 --> Output["Output Gloss<br/>I MARKET GO"]

    Meta1["Tense Detection"] -. parallel annotations .-> C6
    Meta2["Negation Detection"] -. parallel annotations .-> C6
    Meta3["Question Classification"] -. parallel annotations .-> C6

    classDef input fill:#FDE047,stroke:#CA8A04,color:#111827;
    classDef lexical fill:#10B981,stroke:#047857,color:#FFFFFF;
    classDef grammar fill:#8B5CF6,stroke:#6D28D9,color:#FFFFFF;
    classDef output fill:#EC4899,stroke:#BE185D,color:#FFFFFF;
    classDef meta fill:#06B6D4,stroke:#0E7490,color:#FFFFFF;

    class Input input;
    class C1,C2,C3,C4,C5 lexical;
    class C6,C7 grammar;
    class Output output;
    class Meta1,Meta2,Meta3 meta;
```

**Grammar annotations** are also computed in parallel:

- **Tense detection** — `PAST` / `FUTURE` / present (default) via POS patterns
- **Negation** — detects "not", "never", "no" → `is_negated: true`
- **Question type** — `WH` (what/where/who/when/how) or `YES_NO` (sentence ends with `?`)

---

## Features

| Feature | Mode | Description |
|---------|------|-------------|
| **Text to ISL** | Backend | Type English → NLP pipeline → 3D avatar signs ISL |
| **Speech to ISL** | Backend | Record audio → faster-whisper / Vosk ASR → NLP pipeline → avatar signs |
| **Learn ISL** | Built-in | Interactive ISL alphabet A–Z and 48 common word signs |
| **Create Video** | Built-in | Compose and save ISL signing videos with unique IDs |
| **Video Gallery** | Built-in | Browse and replay all saved ISL videos |
| **Live Streaming** | WebSocket | `/ws/live-speech` endpoint exists but is currently a stub (not yet wired to ASR) |

---

## Tech Stack

### Frontend

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | React | 17.0.2 |
| 3D Rendering | Three.js (WebGL, GLTF, skeletal animation) | r136 |
| UI Components | Bootstrap + React Bootstrap | 5.x / 2.x |
| Speech Capture | Web Speech API + MediaRecorder | Browser native |
| HTTP Client | Fetch API (AbortController + timeouts) | Browser native |
| Routing | React Router DOM | 6.x |
| Build Tool | Create React App (react-scripts) | 5.x |

### NLP Backend

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | FastAPI + GZipMiddleware | 0.104.1 |
| ASGI Server | Uvicorn (single worker) | 0.24.0 |
| Speech Recognition (default) | faster-whisper (`tiny.en`, int8, CTranslate2 — offline) | 1.2.1 |
| Speech Recognition (fallback) | Vosk (`vosk-model-small-en-in-0.4`, Indian English, offline) | 0.3.45 |
| NLP | NLTK (tokenise, POS tag, lemmatise, stopwords) | 3.9+ |
| Audio Capture | PyAudio (PortAudio callback stream) | 0.2.14 |
| Audio DSP | NumPy + SciPy (spectral subtraction, FFT-512) | 2.x / 1.17+ |
| Database | SQLite with FTS5 (gloss/HamNoSys mapping) | Built-in |
| Language | Python | 3.12+ |

---

## Getting Started — Raspberry Pi 4B

### 1. System Prerequisites

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    portaudio19-dev \
    python3-dev \
    python3-pip \
    libasound2-dev \
    libatlas-base-dev \
    nodejs \
    npm
```

### 2. Clone and Install

```bash
git clone https://github.com/your-org/signvani.git
cd signvani
```

**Backend:**

```bash
cd nlp_backend
pip3 install --extra-index-url https://www.piwheels.org/simple -r requirements.txt
python3 scripts/setup_models.py      # Downloads Vosk model (~40 MB), faster-whisper tiny.en (~39 MB) + NLTK data (~24 MB)
python3 -m src.database.seed_db      # Seeds ISL gloss database
cd ..
```

**Frontend:**

```bash
cd client
npm install
npm run build        # Build static files for production
cd ..
```

### 3. Run on Boot (systemd)

Create `/etc/systemd/system/signvani-backend.service`:

```ini
[Unit]
Description=SignVani NLP Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/signvani/nlp_backend
ExecStart=/usr/bin/python3 api_server.py
Restart=on-failure
Environment=SIGNVANI_ENV=production
# ASR engine: faster_whisper (default, better accuracy) or vosk (lower latency)
Environment=ASR_ENGINE=faster_whisper

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable signvani-backend
sudo systemctl start signvani-backend
```

Serve the React build with nginx:

```bash
sudo apt-get install -y nginx
sudo cp -r client/build/* /var/www/html/
sudo systemctl restart nginx
```

### 4. Access the Application

Open `http://<raspberry-pi-ip>/sign-kit/home` in any browser on the same network.

---

## Getting Started — Development

### One-command start (recommended)

```bash
# Install deps once
cd nlp_backend && pip install -r requirements.txt && python scripts/setup_models.py && python -m src.database.seed_db && cd ..
cd client && npm install && cd ..

# Launch both services
./start.sh                        # faster-whisper (default)
ASR_ENGINE=vosk ./start.sh        # switch to Vosk
```

The script waits for the backend to pass its `/api/health` check before starting the frontend, and a single **Ctrl+C** stops both cleanly.

### Manual start

```bash
# Terminal 1 — NLP Backend
cd nlp_backend
pip install -r requirements.txt
python scripts/setup_models.py
python -m src.database.seed_db
ASR_ENGINE=faster_whisper python api_server.py   # port 8000

# Terminal 2 — React Client
cd client
npm install
npm start                                         # port 3000
```

Open [http://localhost:3000/sign-kit/home](http://localhost:3000/sign-kit/home).

### Choosing the ASR engine

| `ASR_ENGINE` | Model | ~RAM | ~Latency (RPi4) | Best for |
|---|---|---|---|---|
| `faster_whisper` **(default)** | `tiny.en` int8 CTranslate2 | ~180 MB | 1–2 s | Accuracy, file uploads |
| `vosk` | `vosk-model-small-en-in-0.4` | ~80 MB | 0.1–0.3 s | Lowest latency, live pipeline |

### Running Tests

```bash
cd nlp_backend

# Unit tests
python -m tests.unit.test_nlp

# Integration tests (Phases 1–2)
python -m tests.integration.test_pipeline_phase1_2

# All tests with coverage
pip install -r requirements-dev.txt
pytest --cov=src
```

---

## API Reference

Base URL: `http://localhost:8000`

### `GET /api/health`

Returns component status for the active ASR engine, NLP engine, and database.

```json
{
  "status": "healthy",
  "components": {
    "gloss_mapper": true,
    "sigml_generator": true,
    "handsign_generator": true
  }
}
```

### `POST /api/text-to-handsign`

Converts English text to Three.js-compatible keyframe animations.

**Request:**

```json
{ "text": "I am going to the market" }
```

**Response:**

```json
{
  "original_text": "I am going to the market",
  "gloss": "I MARKET GO",
  "total_duration": 3200,
  "animations": [
    {
      "gloss": "GO",
      "hamnosys": "hamflathand,hampalmu,hammoveo",
      "duration": 1200,
      "keyframes": [
        {
          "transformations": [
            ["mixamorigRightArm", "rotation", "z", "Math.PI/3", "+"],
            ["mixamorigRightForeArm", "rotation", "z", "Math.PI/4", "+"]
          ]
        }
      ]
    }
  ]
}
```

### `POST /api/text-to-sign`

Returns gloss string and raw SiGML XML.

**Request:** `{ "text": "Hello world" }`

**Response fields:** `original_text`, `gloss`, `glosses[]`, `tense`, `is_negated`, `question_type`, `hamnosys[]`, `sigml`, `processing_time_ms`

### `POST /api/speech-to-handsign`

Accepts a multipart WAV audio file. Transcribes using the active ASR engine (selected by `ASR_ENGINE`), then runs the same NLP pipeline as `text-to-handsign`. Input WAV is automatically normalised to 16 kHz mono.

**Request:** `multipart/form-data` — field `audio` (WAV, any sample rate / channel count)

### `POST /api/speech-to-sign`

Same as above but returns SiGML XML instead of keyframes.

### `WS /ws/live-speech`

Accepts a WebSocket connection and receives audio bytes, but currently only echoes a placeholder `"Processing audio chunk..."` message — it does not yet call an ASR engine. The real-time audio pipeline it's meant to front (`PipelineOrchestrator`) is implemented but not wired in; see [Real-Time Audio Pipeline](#real-time-audio-pipeline-built-not-wired-in).

---

## Performance

All metrics measured on **Raspberry Pi 4B (4 GB RAM)**, Raspberry Pi OS 64-bit, Python 3.12, Node.js 18.

| Metric | Target | Achieved |
|--------|--------|----------|
| End-to-end latency (text→sign) | < 1 s | ~0.4 s |
| End-to-end latency (speech→sign) | < 1 s | ~0.8 s |
| ASR Word Error Rate (Indian English) | < 10% | 6.39% |
| Idle RAM (backend + browser) | < 500 MB | ~380 MB |
| CPU load during speech processing | < 80% | ~65% |
| 3D render frame rate | 30 fps | 30 fps |
| Animation similarity score | — | 4.87 / 5 |

### User Research

SignVani was evaluated with real users. Results from published research:

| Metric | Score |
|--------|-------|
| User satisfaction | **4.44 / 5** |
| Appearance rating | 4.52 / 5 |
| Overall rating | 4.32 / 5 |
| System Usability Scale (SUS) | **81.5 / 100** (Grade B — "Good") |
| Net Promoter Score (NPS) | **+36** |
| Speech recognition WER | **6.39%** |
| Animation similarity | **4.87 / 5** |

---

## RPi4 Optimisations

Every layer of SignVani has been tuned for the ARM Cortex-A72 and VideoCore VI:

### Backend

| Area | Optimisation | Rationale |
|------|-------------|-----------|
| Audio DSP | FFT size 512 (down from 1024) | Halves spectral subtraction compute on ARM |
| Audio DSP | Pre-computed Hann window (`np.float32`) | Eliminates per-frame allocation |
| Audio DSP | In-place `np.maximum(..., out=...)` | Avoids temporary array on heap |
| Audio capture | `audio_data *= np.float32(1/32768.0)` | In-place float32; avoids float64 intermediate |
| ASR worker | Pre-allocated `_int16_buffer` + class-level `_SCALE_FACTOR` | Zero `malloc` per audio chunk |
| NLP | Pre-compiled contraction regex (14 patterns at class level) | Avoids `re.compile()` on every call |
| Data layer | `AudioChunk` caches RMS energy at construction | VAD accesses `.energy` every frame — computed once |
| Data layer | `__slots__` on all data classes (`AudioChunk`, `GlossPhrase`, `SiGMLOutput`, etc.) | ~66% reduction in per-instance memory overhead |
| Database | `PRAGMA temp_store=MEMORY` | Temp tables in RAM, not SD card |
| Database | `PRAGMA mmap_size=67108864` (64 MB) | Memory-mapped reads reduce syscalls |
| Database | `PRAGMA journal_mode=DELETE` | Avoids WAL write-ahead log for SD card longevity |
| Database | Removed per-read `UPDATE frequency` write | Eliminates WRITE+COMMIT on every cache-miss lookup |
| API server | `GZipMiddleware(minimum_size=500)` | Reduces HTTP response bandwidth |
| API server | `workers=1`, `limit_concurrency=10`, `timeout_keep_alive=5` | Prevents memory exhaustion under load |
| Queue sizes | Audio: 8 chunks (~160 KB), Transcript: 5, Gloss: 3 | Bounded memory use per pipeline stage |

### Frontend

| Area | Optimisation | Rationale |
|------|-------------|-----------|
| WebGL renderer | `precision: 'mediump'` | VideoCore VI is faster at medium precision |
| WebGL renderer | `antialias: false` | No MSAA; saves fill-rate on VideoCore VI |
| WebGL renderer | `stencil: false`, `alpha: false` | Smaller framebuffer; less GPU memory |
| WebGL renderer | `powerPreference: 'low-power'` | Signals GPU to use efficient power state |
| WebGL renderer | `setPixelRatio(1)` | 1:1 physical pixels; halves pixel fill on HiDPI |
| 3D avatar | `castShadow: false`, `receiveShadow: false` | Shadow maps are expensive on VideoCore VI |
| Animation loop | 30 fps throttle via `performance.now()` | Halves `requestAnimationFrame` invocations |
| API requests | `AbortController` — 10 s text / 15 s speech timeout | Prevents hanging on slow RPi4 processing |

---

## Configuration

All backend configuration is centralised in [`nlp_backend/config/settings.py`](nlp_backend/config/settings.py) as immutable `@dataclass(frozen=True)` classes.

```python
audio_config   = AudioConfig()    # Sample rate, FFT size, VAD thresholds
vosk_config    = VoskConfig()     # Vosk model path, alternatives, word confidence
whisper_config = WhisperConfig()  # faster-whisper model size, compute type, VAD
nlp_config     = NLPConfig()      # NLTK resources, lemmatisation, SOV transform
database_config= DatabaseConfig() # DB path, pool size, LRU cache, PRAGMAs
pipeline_config= PipelineConfig() # Queue sizes, thread timeouts, latency targets
sigml_config   = SiGMLConfig()    # XML encoding, pretty-print toggle
avatar_config  = AvatarConfig()   # CWASA player host/port
logging_config = LoggingConfig()  # Log level, rotation size, SD card safety
```

The **active ASR engine** is selected at startup via the `ASR_ENGINE` environment variable (read once, immutable at runtime):

```bash
ASR_ENGINE=faster_whisper  # default — higher accuracy
ASR_ENGINE=vosk            # fallback — lower latency
```

Key values tuned for RPi4:

```python
AudioConfig:
    SAMPLE_RATE      = 16000       # Hz
    FRAMES_PER_BUFFER= 1024        # ~64 ms per chunk
    FFT_SIZE         = 512         # Spectral subtraction (RPi4 optimal)

WhisperConfig:
    MODEL_SIZE       = 'tiny.en'   # ~39 MB, int8-quantised
    DEVICE           = 'cpu'
    COMPUTE_TYPE     = 'int8'      # CTranslate2 INT8 — fits RPi4 RAM
    BEAM_SIZE        = 1           # Greedy decode, fastest on ARM
    VAD_FILTER       = True        # Live pipeline; disabled for file uploads
    SILENCE_TIMEOUT  = 0.5         # Seconds of silence → flush utterance

DatabaseConfig:
    CONNECTION_POOL_SIZE = 2
    CACHE_SIZE           = 200     # LRU entries
    PRAGMA_TEMP_STORE    = 'MEMORY'
    PRAGMA_MMAP_SIZE     = 67108864  # 64 MB

PipelineConfig:
    AUDIO_QUEUE_SIZE     = 8       # ~160 KB bounded
    TARGET_LATENCY       = 1.0     # seconds
    MAX_MEMORY_MB        = 500
```

Frontend API URL is set via environment variable:

```bash
REACT_APP_API_URL=http://raspberrypi.local:8000
```

---

## Project Structure

```
SignVani/
├── start.sh                          # Unified startup script (launches backend + frontend)
├── client/                          # React 17 frontend
│   └── src/
│       ├── Animations/
│       │   ├── Alphabets/           # A.js – Z.js  (letter bone transforms)
│       │   ├── Data/wordsData.json  # 48 word animation keyframe definitions
│       │   ├── animationPlayer.js   # Core animation queue builder
│       │   └── defaultPose.js       # Rest-pose bone state
│       ├── Hooks/
│       │   ├── useThreeScene.js     # Three.js scene + GLTF loader lifecycle
│       │   └── useAnimationEngine.js# rAF loop · 30 fps throttle · queue processing
│       ├── Services/
│       │   ├── apiService.js        # Fetch client (AbortController timeouts)
│       │   ├── handsignService.js   # Handsign API calls
│       │   ├── audioRecorder.js     # MediaRecorder → WAV conversion
│       │   └── enhancedAnimationPlayer.js
│       ├── Pages/
│       │   ├── ConvertEnhanced.js   # Primary speech/text-to-sign page
│       │   ├── Convert.js           # Built-in animation mode
│       │   ├── LearnSign.js         # Interactive ISL learning
│       │   ├── CreateVideo.js
│       │   └── Videos.js
│       ├── Utils/
│       │   ├── threeCleanup.js      # WebGL resource disposal (prevents GPU leak)
│       │   └── threeHelpers.js      # Safe bone access validators
│       └── Models/                  # xbot.glb · ybot.glb (Mixamo rig)
│
└── nlp_backend/                     # Python FastAPI NLP backend
    ├── api_server.py                # FastAPI entry point + uvicorn launcher
    ├── config/settings.py           # All configuration (frozen dataclasses)
    └── src/
        ├── audio/
        │   ├── audio_capture.py     # PyAudio callback stream
        │   ├── audio_buffer.py      # CircularAudioBuffer
        │   ├── vad.py               # Voice Activity Detector (RMS energy)
        │   └── noise_filter.py      # Spectral subtraction (FFT-512)
        ├── asr/
        │   ├── vosk_engine.py       # Vosk singleton engine (fallback)
        │   ├── vosk_integration.py  # Vosk WAV helpers + get_asr_engine() factory
        │   ├── whisper_engine.py    # faster-whisper singleton (default)
        │   ├── whisper_integration.py # WhisperASR — mirrors VoskASR public API
        │   └── asr_worker.py        # ASRWorker (Vosk) + WhisperASRWorker (accumulate→flush)
        ├── nlp/
        │   ├── text_processor.py    # Tokenise · POS tag · lemmatise
        │   ├── grammar_transformer.py# SVO→SOV · tense · negation · question
        │   ├── gloss_mapper.py      # Orchestrates full NLP pipeline
        │   └── dataclasses.py       # __slots__ data structures (AudioChunk etc.)
        ├── database/
        │   ├── db_manager.py        # Thread-safe SQLite pool (singleton)
        │   ├── retriever.py         # LRU-cached FTS5 gloss lookup
        │   ├── schema.sql           # gloss_mapping · unknown_words · FTS5 vtable
        │   └── hamnosys_data.py     # Seed data (English gloss → HamNoSys)
        ├── sigml/
        │   ├── generator.py         # SiGML XML generator
        │   └── handsign_generator.py# HamNoSys → Three.js keyframe converter
        └── pipeline/
            └── orchestrator.py      # Thread pipeline coordinator
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/overview.md](docs/overview.md) | Project goals, problem statement, ISL pipeline, survey results |
| [docs/architecture.md](docs/architecture.md) | Full system diagrams, data flows, component relationships |
| [docs/client.md](docs/client.md) | Pages, custom hooks, animation system, services |
| [docs/nlp-backend.md](docs/nlp-backend.md) | Full API reference, NLP pipeline, module descriptions |
| [docs/setup.md](docs/setup.md) | Step-by-step installation for all platforms |

---

## Problem Statement

India has an estimated **18 million deaf and hard-of-hearing individuals** who rely on Indian Sign Language as their primary communication mode. Most hearing people have no knowledge of ISL, creating a significant daily communication barrier. Existing tools are either limited in vocabulary, require specialist hardware, or depend on cloud services.

SignVani addresses this by providing a free, browser-accessible toolkit that runs entirely on a ₹6,000 Raspberry Pi 4B — no internet connection, no subscription, no cloud.

---

<div align="center">

Built for the deaf community of India · 100% offline · Raspberry Pi 4B native

</div>
