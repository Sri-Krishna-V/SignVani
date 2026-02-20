# SignVani Copilot Instructions

SignVani converts spoken English → Indian Sign Language (ISL) using offline processing optimized for Raspberry Pi 4B. Target: <1s latency, <500MB RAM, no cloud APIs.

## Architecture

Two independently runnable services + a shared domain (ISL grammar):

```
[client/]  React + Three.js 3D avatar (port 3000)
    ↕  REST + WebSocket  (REACT_APP_API_URL → http://localhost:8000)
[nlp_backend/]  FastAPI pipeline (port 8000)
    └── Audio → VAD → NoiseFilter → CircularBuffer → queue.Queue
         → ASRWorker (Vosk) → NLP (SVO→SOV) → SQLite → SiGML → SSE/WS → Avatar
```

Full pipeline: [nlp_backend/src/pipeline/orchestrator.py](nlp_backend/src/pipeline/orchestrator.py)  
API layer: [nlp_backend/api_server.py](nlp_backend/api_server.py)  
Frontend routing: [client/src/App.js](client/src/App.js) — all routes under `/sign-kit/` prefix

## Dev Workflow

```bat
# Start both services (Windows)
start-signvani.bat

# Or individually:
cd nlp_backend && python api_server.py          # port 8000
cd client && npm start                          # port 3000
```

One-time setup (nlp_backend):
```bash
pip install -r nlp_backend/requirements.txt
python nlp_backend/scripts/setup_models.py      # downloads Vosk model + NLTK data
```

On Windows, install PyAudio via `pipwin install pyaudio` (not pip directly).

Tests (run from `nlp_backend/` as root):
```bash
python -m tests.unit.test_nlp
python -m tests.integration.test_pipeline_phase1_2
```

## Backend Patterns (nlp_backend/)

**Config** — always import from `config/settings.py`, never hardcode:
```python
from config.settings import audio_config, vosk_config, pipeline_config
# audio_config.SAMPLE_RATE, pipeline_config.AUDIO_QUEUE_SIZE, etc.
```
All config uses `@dataclass(frozen=True)` for immutability.

**Memory optimization** (critical for RPi4) — use `__slots__` on all data classes and `np.float32` for audio arrays. Reference: [nlp_backend/src/nlp/dataclasses.py](nlp_backend/src/nlp/dataclasses.py)

**Singletons** — `VoskEngine` and `DatabaseManager` use `_instance`/`_lock` double-checked locking. Never instantiate them directly; use their factory methods.

**Inter-component communication** — strictly via `queue.Queue` with bounded sizes (`pipeline_config.AUDIO_QUEUE_SIZE`). No shared mutable state between threads.

**Exceptions** — use domain hierarchy from [nlp_backend/src/utils/exceptions.py](nlp_backend/src/utils/exceptions.py):
`SignVaniError → AudioError → AudioCaptureError` / `ASRError` / `DatabaseError`

**ISL NLP rule** — English is SVO; ISL is SOV. The NLP pipeline strips stop-words, lemmatizes, then reorders:
- Input: "I am going to the market" → Output gloss: `"I MARKET GO"`
- Implemented in [nlp_backend/src/nlp/gloss_mapper.py](nlp_backend/src/nlp/gloss_mapper.py)

**Database** — SQLite with WAL mode. Schema: [nlp_backend/src/database/schema.sql](nlp_backend/src/database/schema.sql). Seed data in [nlp_backend/src/database/hamnosys_data.py](nlp_backend/src/database/hamnosys_data.py). Access only through `DatabaseManager` singleton.

## Frontend Patterns (client/)

**3D Avatar** — Two avatar models (`xbot`, `ybot` as `.glb`). Scene lifecycle via `useThreeScene` hook; bone animation queue via `useAnimationEngine` hook. Animation frames are arrays of `[boneName, action, axis, limit, sign]` tuples.

**Animation data structure** — two separate formats for words vs. alphabets:

- **Words** → [client/src/Animations/Data/wordsData.json](client/src/Animations/Data/wordsData.json)  
  JSON keyframe format. Each entry has a `description` and a `keyframes` array. Each keyframe lists `transformations`, each of which is a 5-tuple. New words are auto-discovered — no changes to `words.js` needed.
  ```json
  "HELLO": {
    "description": "Wave with right hand",
    "keyframes": [
      {
        "transformations": [
          ["mixamorigRightArm",     "rotation", "z", "Math.PI/3", "+"],
          ["mixamorigRightForeArm", "rotation", "z", "Math.PI/4", "+"]
        ]
      },
      {
        "transformations": [
          ["mixamorigRightArm",     "rotation", "z", "0",         "-"],
          ["mixamorigRightForeArm", "rotation", "z", "0",         "-"]
        ]
      }
    ]
  }
  ```
  The `value` field accepts string `Math.PI` expressions (e.g. `"Math.PI/2"`, `"-Math.PI/3"`) — evaluated safely by `wordLoader.js`.

- **Alphabets** → individual JS files in [client/src/Animations/Alphabets/](client/src/Animations/Alphabets/), one per letter.  
  Each exports a function `(ref) => {}` that pushes tuples directly using JS `Math.PI` literals. New alphabet files **must** be manually imported and re-exported in `alphabets.js`.
  ```js
  export const A = (ref) => {
    let animations = [];
    animations.push(["mixamorigRightHand", "rotation", "x", -Math.PI/2, "-"]);
    // ... more bone tuples ...
    ref.animations.push(animations);  // one frame
    if (!ref.pending) { ref.pending = true; ref.animate(); }
  };
  ```

**Tuple schema** — `[boneName, transformType, axis, limit, direction]`  
- `boneName`: Mixamo rig name, e.g. `mixamorigRightArm`, `mixamorigLeftHandIndex1`  
- `transformType`: always `"rotation"` (occasionally `"position"`)  
- `axis`: `"x"` | `"y"` | `"z"`  
- `limit`: target radian value (number for JS files, string for JSON)  
- `direction`: `"+"` → bone rotates toward positive limit; `"-"` → toward negative limit

Multi-keyframe words animate sequentially (each keyframe in `wordsData.json` maps to one entry in `ref.animations`). Alphabets use a single flat frame.

**Backend integration** — all API calls go through [client/src/Services/apiService.js](client/src/Services/apiService.js). The backend URL is configured via `REACT_APP_API_URL` env var (default: `http://localhost:8000`). The primary enhanced page is `/sign-kit/convert-enhanced`.

**Three.js cleanup** — always use [client/src/Utils/threeCleanup.js](client/src/Utils/threeCleanup.js) helpers when unmounting components to prevent GPU memory leaks.

## API Endpoints (port 8000)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Check Vosk/spaCy/DB status |
| POST | `/api/text-to-sign` | JSON `{text}` → gloss + HamNoSys |
| POST | `/api/speech-to-sign` | Multipart `audio` WAV → transcript + gloss |
| WS | `/ws/stream` | Real-time audio streaming |

Fallback mock ASR activates automatically in `DEBUG` mode when Vosk model is absent.
