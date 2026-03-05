# SignVani — System Architecture

## High-Level Architecture

SignVani consists of two independent processes that communicate over HTTP:

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (React App)                   │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  UI / UX  │  │ Three.js 3D  │  │  Animation Engine  │  │
│  │  (pages,  │  │   Renderer   │  │ (bone transforms)  │  │
│  │ controls) │  │  (avatar)    │  │                   │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
│                    ↑ bone keyframes                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Service Layer                        │    │
│  │  apiService.js  │  handsignService.js  │  audio   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (JSON)
                       ▼
┌─────────────────────────────────────────────────────────┐
│               NLP Backend (FastAPI, port 8000)          │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────┐  │
│  │  Vosk ASR  │  │   NLTK    │  │  SQLite + FTS5 DB  │  │
│  │ (offline)  │  │ NLP pipe  │  │  (gloss/HamNoSys)  │  │
│  └────────────┘  └───────────┘  └────────────────────┘  │
│                    ↓                                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │           SiGML / Animation Generator              │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## System Architecture Diagram

```mermaid
graph TD
    User["User (Browser)"]

    subgraph frontend [React Client - port 3000]
        Pages["Pages\n(Convert, LearnSign,\nCreateVideo, Videos)"]
        Services["Services\n(apiService.js,\nhandsignService.js,\naudioRecorder.js)"]
        Hooks["Custom Hooks\n(useThreeScene,\nuseAnimationEngine)"]
        ThreeJS["Three.js Renderer\n(WebGL)"]
        Avatar["3D Avatar\n(xbot / ybot .glb)"]
        AnimData["Built-in Animations\n(wordsData.json,\nAlphabets/A-Z.js)"]
    end

    subgraph backend [NLP Backend - port 8000]
        FastAPI["FastAPI Server\n(api_server.py)"]
        GlossMapper["GlossMapper\n(tokenize → POS → lemma\n→ SVO-SOV → gloss)"]
        VoskASR["Vosk ASR\n(vosk-model-small-en-in-0.4)"]
        SQLiteDB["SQLite Database\n(gloss_mapping, FTS5)"]
        SiGMLGen["SiGML Generator\n(HamNoSys → SiGML XML)"]
        HandsignGen["Handsign Generator\n(HamNoSys → keyframes)"]
    end

    User -->|"text input"| Pages
    User -->|"microphone"| Services
    Pages --> Services
    Services -->|"POST /api/text-to-handsign"| FastAPI
    Services -->|"POST /api/speech-to-handsign"| FastAPI
    Services -->|"POST /api/text-to-sign"| FastAPI
    Services -->|"POST /api/speech-to-sign"| FastAPI
    FastAPI --> GlossMapper
    FastAPI --> VoskASR
    VoskASR -->|"transcript"| GlossMapper
    GlossMapper --> SQLiteDB
    SQLiteDB -->|"HamNoSys codes"| SiGMLGen
    SQLiteDB -->|"HamNoSys codes"| HandsignGen
    SiGMLGen -->|"SiGML XML"| FastAPI
    HandsignGen -->|"keyframes JSON"| FastAPI
    FastAPI -->|"JSON response"| Services
    Services -->|"keyframes"| Hooks
    AnimData -->|"built-in frames"| Hooks
    Hooks --> ThreeJS
    ThreeJS --> Avatar
    Avatar -->|"rendered sign"| User
```

---

## Data Flow Diagrams

### Text-to-Sign Flow (Backend Mode)

```mermaid
sequenceDiagram
    participant U as User
    participant C as React Client
    participant B as NLP Backend
    participant DB as SQLite DB

    U->>C: Types text
    C->>B: POST /api/text-to-handsign {"text": "Hello world"}
    B->>B: Tokenize + POS tag + lemmatize
    B->>B: SVO → SOV grammar transform
    B->>DB: Lookup gloss for each lemma
    DB-->>B: HamNoSys codes per gloss
    B->>B: Generate keyframe animations
    B-->>C: JSON {gloss, glosses, animations[], total_duration}
    C->>C: Queue animations in useAnimationEngine
    C->>C: Apply bone transforms per frame
    C-->>U: 3D avatar plays ISL signs
```

### Speech-to-Sign Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as React Client
    participant B as NLP Backend
    participant V as Vosk ASR

    U->>C: Clicks "Record"
    C->>C: audioRecorder captures MediaRecorder WebM
    C->>C: Convert WebM → WAV (Web Audio API)
    C->>B: POST /api/speech-to-handsign (WAV file)
    B->>V: Transcribe WAV audio
    V-->>B: Transcript text
    B->>B: NLP pipeline (same as text-to-sign)
    B-->>C: JSON {original_text, gloss, animations[]}
    C-->>U: Avatar plays ISL signs + gloss displayed
```

### Built-in Animation Flow (No Backend)

```mermaid
sequenceDiagram
    participant U as User
    participant C as React Client
    participant AP as animationPlayer.js
    participant AE as useAnimationEngine

    U->>C: Types text (Convert page, traditional mode)
    C->>AP: playString(text)
    AP->>AP: Check wordsData.json for whole-word match
    AP->>AP: Fall back to letter-by-letter if no match
    AP->>AE: Push frames to animations queue (ref)
    loop requestAnimationFrame
        AE->>AE: Dequeue next frame
        AE->>AE: Apply bone transforms to Three.js skeleton
        AE->>C: Re-render scene
    end
    C-->>U: Avatar animates
```

---

## Component Relationships

```mermaid
graph LR
    subgraph pages [Pages]
        Convert["Convert.js"]
        ConvertE["ConvertEnhanced.js"]
        LearnSign["LearnSign.js"]
        Video["Video.js"]
        CreateVideo["CreateVideo.js"]
        Videos["Videos.js"]
    end

    subgraph hooks [Custom Hooks]
        useThree["useThreeScene.js\n(scene, camera, renderer,\nmodel loading)"]
        useAnim["useAnimationEngine.js\n(requestAnimationFrame loop,\nqueue processing)"]
    end

    subgraph services [Services]
        apiSvc["apiService.js\n(NLP backend calls)"]
        handsignSvc["handsignService.js\n(handsign API calls)"]
        audioRec["audioRecorder.js\n(WebM → WAV capture)"]
        animPlayer["animationPlayer.js\n(queue builder)"]
        enhancedPlayer["enhancedAnimationPlayer.js\n(backend animation runner)"]
    end

    subgraph animdata [Animation Data]
        wordsJson["wordsData.json\n(48 word animations)"]
        alphabets["Alphabets/A-Z.js\n(26 letter animations)"]
    end

    Convert --> useThree
    Convert --> useAnim
    Convert --> animPlayer
    ConvertE --> useThree
    ConvertE --> useAnim
    ConvertE --> apiSvc
    ConvertE --> handsignSvc
    ConvertE --> audioRec
    ConvertE --> enhancedPlayer
    LearnSign --> useThree
    LearnSign --> useAnim
    LearnSign --> animPlayer
    Video --> useThree
    Video --> useAnim
    Video --> animPlayer
    animPlayer --> wordsJson
    animPlayer --> alphabets
```

---

## Directory Structure

```
SignVani/
├── client/                          # React frontend
│   └── src/
│       ├── Animations/
│       │   ├── Alphabets/           # A.js – Z.js (letter bone transforms)
│       │   ├── Data/
│       │   │   └── wordsData.json   # 48 word animation definitions
│       │   ├── Utils/
│       │   │   └── wordLoader.js
│       │   ├── alphabets.js
│       │   ├── animationPlayer.js   # Core animation queue builder
│       │   ├── defaultPose.js
│       │   └── words.js
│       ├── Components/
│       │   ├── Home/                # Masthead, Intro, Services
│       │   ├── CreateVideo/         # ConfirmModal
│       │   ├── Videos/              # VideoCard
│       │   ├── Navbar.js
│       │   └── Footer.js
│       ├── Config/
│       │   └── config.js            # Legacy video API base URL
│       ├── Hooks/
│       │   ├── useThreeScene.js     # Three.js scene lifecycle hook
│       │   └── useAnimationEngine.js # rAF loop + queue hook
│       ├── Models/                  # .glb avatar files (xbot, ybot)
│       ├── Pages/
│       │   ├── Home.js
│       │   ├── Convert.js
│       │   ├── ConvertEnhanced.js
│       │   ├── LearnSign.js
│       │   ├── CreateVideo.js
│       │   ├── Videos.js
│       │   ├── Video.js
│       │   └── Feedback.js
│       ├── Services/
│       │   ├── apiService.js
│       │   ├── handsignService.js
│       │   ├── enhancedAnimationPlayer.js
│       │   └── audioRecorder.js
│       ├── Utils/
│       │   ├── threeHelpers.js      # Safe bone access utilities
│       │   └── threeCleanup.js      # WebGL resource disposal
│       └── App.js                   # Router + route definitions
│
└── nlp_backend/                     # Python NLP backend
    ├── api_server.py                # FastAPI entry point
    ├── main.py                      # CLI entry point
    ├── config/
    │   └── settings.py              # All configuration (frozen dataclasses)
    ├── src/
    │   ├── pipeline/
    │   │   └── orchestrator.py      # Thread-based pipeline coordinator
    │   ├── audio/
    │   │   ├── audio_capture.py
    │   │   ├── audio_buffer.py
    │   │   ├── vad.py
    │   │   └── noise_filter.py
    │   ├── asr/
    │   │   ├── vosk_engine.py
    │   │   ├── asr_worker.py
    │   │   └── vosk_integration.py
    │   ├── nlp/
    │   │   ├── text_processor.py
    │   │   ├── grammar_transformer.py
    │   │   ├── gloss_mapper.py
    │   │   └── dataclasses.py
    │   ├── database/
    │   │   ├── db_manager.py
    │   │   ├── retriever.py
    │   │   ├── seed_db.py
    │   │   ├── schema.sql
    │   │   ├── hamnosys_data.py
    │   │   └── hamnosys_symbols.py
    │   └── sigml/
    │       ├── generator.py
    │       ├── handsign_generator.py
    │       └── avatar_player.py
    ├── scripts/
    │   ├── setup_models.py
    │   └── setup_avatar.py
    └── tests/
        ├── unit/
        └── integration/
```

---

## Deployment Topology

### Local Development

```
localhost:3000   ←→   localhost:8000
  React App           FastAPI Server
  (npm start)         (uvicorn)
```

The React app reads `REACT_APP_API_URL` at build time. If not set, it defaults to `http://localhost:8000`.

### Raspberry Pi 4 Deployment

Both processes run on the same Raspberry Pi 4 device:

```
RPi4 (LAN/WiFi)
├── port 3000 — React dev server (or static build served by nginx)
├── port 8000 — FastAPI backend (uvicorn)
└── port 8052 — CWASA SiGML Avatar Player (optional, TCP socket)
```

The `start-signvani.bat` script at the project root launches both services together.

### Legacy Cloud Deployment

The original video API (for `CreateVideo`/`Videos`/`Video` pages) uses a Heroku-hosted Node.js API:
- Base URL: `https://sign-kit-api.herokuapp.com/sign-kit`
- Configured in `client/src/Config/config.js`
