# SignVani — Indian Sign Language Toolkit

SignVani is a browser-based toolkit for **Indian Sign Language (ISL)** that converts spoken and written English into animated ISL gestures, displayed through a 3D avatar. It also provides tools for learning ISL and creating shareable ISL videos.

> **Vani** (Sanskrit: वाणी) means *voice* or *speech*.

---

## Features

- **Text to ISL** — Type English text and watch a 3D avatar sign it in ISL
- **Speech to ISL** — Speak into the microphone; the system transcribes and animates the signs
- **Learn ISL** — Interactive alphabet (A–Z) and 48 common word signs
- **Create Video** — Compose an ISL video from text or speech and save it with a unique ID
- **Video Gallery** — Browse and replay saved ISL videos
- **NLP Backend** — Python pipeline for SVO→SOV grammar transformation, gloss mapping, and HamNoSys generation

---

## Quick Start

### Windows (both servers at once)

```bat
start-signvani.bat
```

### Manual

```bash
# Terminal 1 — NLP Backend (Python)
cd nlp_backend
pip install -r requirements.txt
python scripts/setup_models.py   # downloads Vosk model + NLTK data (~64MB, first run only)
python -m src.database.seed_db   # seeds the ISL gloss database (first run only)
uvicorn api_server:app --host 0.0.0.0 --port 8000

# Terminal 2 — React Client
cd client
npm install
npm start
```

Open [http://localhost:3000/sign-kit/home](http://localhost:3000/sign-kit/home).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 17, Three.js 0.136, Bootstrap 5 |
| 3D Rendering | Three.js (WebGL, GLTF avatars, bone animations) |
| NLP Backend | Python 3.12, FastAPI, Vosk ASR, NLTK, SQLite |
| Speech Input | Web Speech API (browser), Vosk (backend, offline) |

---

## Documentation

| Document | Description |
|---|---|
| [Overview](./docs/overview.md) | Project goals, features, ISL pipeline, survey results, development status |
| [Architecture](./docs/architecture.md) | System diagrams, data flow, component relationships, directory structure |
| [Client App](./docs/client.md) | Pages, custom hooks, animation system, services, configuration |
| [NLP Backend](./docs/nlp-backend.md) | API reference, NLP pipeline, module descriptions, performance targets |
| [Setup Guide](./docs/setup.md) | Step-by-step installation for all platforms, including Raspberry Pi |

---

## Project Structure

```
SignVani/
├── client/          # React 17 frontend
├── nlp_backend/     # Python FastAPI NLP backend
├── docs/            # Project documentation
├── data/            # SQLite database (generated)
└── start-signvani.bat  # Windows launcher
```

---

## Survey Results

| Metric | Score |
|---|---|
| User satisfaction | 4.44 / 5 |
| SUS (usability) | 81.5 / 100 |
| Net Promoter Score | +36 |
| Speech recognition WER | 6.39% |
| Animation accuracy | 4.87 / 5 |
