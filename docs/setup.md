# SignVani — Setup Guide

This guide covers how to run the full SignVani stack locally: the React client on port 3000 and the Python NLP backend on port 8000.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Node.js | 16+ | For the React client |
| npm | 8+ | Bundled with Node.js |
| Python | 3.12+ | For the NLP backend |
| pip | latest | `python -m pip install --upgrade pip` |
| Git | any | To clone the repo |

On **Raspberry Pi / Linux**, also install PortAudio (required by PyAudio):
```bash
sudo apt-get install portaudio19-dev python3-dev libasound2-dev
```

On **Windows**, PyAudio requires a pre-built wheel:
```powershell
pip install pipwin
pipwin install pyaudio
```

---

## Quick Start (Windows)

A convenience script at the project root starts both servers:

```bat
start-signvani.bat
```

This opens two terminal windows — one for the backend (port 8000) and one for the frontend (port 3000).

Then open: [http://localhost:3000/sign-kit/home](http://localhost:3000/sign-kit/home)

---

## Manual Setup

### 1. Clone the Repository

```bash
git clone https://github.com/spectre900/Sign-Kit-An-Avatar-based-ISL-Toolkit.git
cd SignVani
```

---

### 2. Set Up the NLP Backend

#### 2a. Create a virtual environment (recommended)

```bash
cd nlp_backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

#### 2b. Install dependencies

```bash
pip install -r requirements.txt
```

> **Windows note:** If PyAudio fails, use:
> ```powershell
> pip install pipwin && pipwin install pyaudio
> ```

#### 2c. Download models

Downloads the Vosk speech recognition model (~40MB) and NLTK corpus data (~24MB):

```bash
python scripts/setup_models.py
```

This places files in:
- `nlp_backend/models/vosk/vosk-model-small-en-in-0.4/`
- `nlp_backend/models/nltk_data/`

#### 2d. Seed the database

Populates the SQLite database with ISL gloss and HamNoSys data:

```bash
python -m src.database.seed_db
```

The database is created at `data/signvani.db`.

#### 2e. Start the API server

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

Or equivalently:
```bash
python api_server.py
```

Verify it is running:
```
http://localhost:8000/api/health
```

Expected response:
```json
{"status": "healthy", "components": {...}}
```

---

### 3. Set Up the React Client

#### 3a. Install dependencies

```bash
cd client
npm install
```

#### 3b. Configure the NLP backend URL (optional)

By default the client connects to `http://localhost:8000`. To override, create a `.env` file inside `client/`:

```
REACT_APP_API_URL=http://localhost:8000
```

If deploying to a Raspberry Pi on your local network, replace `localhost` with the Pi's IP address:
```
REACT_APP_API_URL=http://192.168.1.100:8000
```

#### 3c. Start the development server

```bash
npm start
```

The app opens automatically at [http://localhost:3000/sign-kit/home](http://localhost:3000/sign-kit/home).

---

## Verification Checklist

| Step | How to verify |
|---|---|
| Backend running | `GET http://localhost:8000/api/health` returns `"status": "healthy"` |
| Vosk model loaded | Backend startup logs show `"Loading NLP models..."` without errors |
| Database seeded | `data/signvani.db` exists and is non-empty |
| Frontend running | Browser opens `http://localhost:3000/sign-kit/home` |
| Text-to-sign works | Go to Convert page, type "Hello", click Convert |
| Backend integration | Go to Convert Enhanced page — status badge shows "Backend Connected" |
| Speech input | Click microphone on Convert page — browser asks for mic permission |

---

## Configuration Reference

All backend configuration is in `nlp_backend/config/settings.py`. Key values you may want to change:

| Setting | Location | Default | Description |
|---|---|---|---|
| Backend host | `api_server.py` line 408 | `0.0.0.0` | Interface to bind |
| Backend port | `api_server.py` line 409 | `8000` | HTTP port |
| CORS origins | `api_server.py` lines 47–50 | `localhost:3000` | Add your frontend URL |
| Vosk model | `VoskConfig.MODEL_NAME` | `vosk-model-small-en-in-0.4` | Can swap for a larger model |
| DB path | `DatabaseConfig.DB_PATH` | `data/signvani.db` | SQLite file location |
| Log level | `LoggingConfig.LOG_LEVEL` | `INFO` | Set to `DEBUG` for verbose output |

---

## Running the CLI (no server)

For quick testing without the frontend:

```bash
cd nlp_backend
python main.py --text "Hello, how are you?"
```

Additional CLI flags:
```
--text "..."       Process a text string through the pipeline
--seed-db          Seed/reseed the database
--verbose          Enable debug-level logging
```

---

## Running Tests

```bash
cd nlp_backend
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Building the Client for Production

```bash
cd client
npm run build
```

Output is in `client/build/`. This can be served with any static file server, for example nginx or `serve`:

```bash
npm install -g serve
serve -s build -l 3000
```

---

## Raspberry Pi Specific Notes

The system is tuned to run on a **Raspberry Pi 4B** (1.5GHz quad-core ARM Cortex-A72, 2–8GB RAM).

**Backend:**
- Use a virtual environment to isolate dependencies
- PyAudio is installed via the system package: `sudo apt-get install python3-pyaudio`
- The Vosk `small-en-in` model (~40MB) is used to minimize RAM usage
- SQLite journal mode is set to `DELETE` (not WAL) to reduce SD card write amplification

**Frontend:**
- The Three.js renderer runs with medium precision shaders, no antialiasing, and a 1:1 pixel ratio
- Shadow rendering is disabled on all 3D models
- These settings are hardcoded in `useThreeScene.js` and do not require configuration

**Running both together on the Pi:**
```bash
# Start backend (background)
cd nlp_backend
uvicorn api_server:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd ../client
npm start
```

Or use the provided `start-signvani.bat` equivalent for Linux by creating a shell script.
