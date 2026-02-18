# SignVani — Client App Documentation

The client is a **React 17** single-page application (Create React App) located in `client/`. It handles all user interaction, 3D avatar rendering, animation playback, and communication with the NLP backend.

---

## Routing

All routes are prefixed with `/sign-kit/` and defined in `client/src/App.js`.

| Route | Component | Description |
|---|---|---|
| `/sign-kit/home` | `Home.js` | Landing page |
| `/sign-kit/convert` | `Convert.js` | Text/speech to ISL (built-in animations) |
| `/sign-kit/convert-enhanced` | `ConvertEnhanced.js` | Text/speech to ISL (NLP backend) |
| `/sign-kit/learn-sign` | `LearnSign.js` | Interactive ISL learning |
| `/sign-kit/create-video` | `CreateVideo.js` | Create and save an ISL video |
| `/sign-kit/all-videos` | `Videos.js` | Browse all saved videos |
| `/sign-kit/video/:videoId` | `Video.js` | Play a saved video |
| `/sign-kit/feedback` | `Feedback.js` | Feedback form links |

---

## Pages

### `Home.js`

Landing page composed of three sub-components from `Components/Home/`:
- `Masthead` — Hero section with a call-to-action
- `Intro` — Project introduction and description
- `Services` — Card grid linking to each feature

---

### `Convert.js`

**Text-to-sign conversion using built-in animations only (no backend required).**

Key state:
- `inputText` — the text typed by the user
- `transcript` — speech recognition result (react-speech-recognition)
- `selectedAvatar` — `"xbot"` or `"ybot"`
- `speed` — animation playback speed (slider, 1–10)
- `paused` — animation pause toggle

User interactions:
1. Type text or click the microphone to dictate
2. Click "Convert" — calls `playString(inputText, sceneRef)` from `animationPlayer.js`
3. Slider adjusts speed; pause button toggles animation

Uses custom hooks:
- `useThreeScene(canvasRef, selectedAvatar)` — sets up Three.js scene and loads avatar
- `useAnimationEngine(sceneRef, speed, paused)` — drives the `requestAnimationFrame` loop

---

### `ConvertEnhanced.js`

**Text-to-sign conversion with NLP backend integration.** Falls back to built-in animations if the backend is unavailable.

Additional capabilities over `Convert.js`:
- **Backend health check** on mount (`GET /api/health`) — shows a status badge
- **Audio recording** using `audioRecorder.js` — captures microphone input, converts WebM → WAV, sends to `/api/speech-to-handsign`
- **Backend mode toggle** — user can switch between backend-generated and built-in animations
- **Gloss display** — shows the ISL gloss string returned by the backend (e.g., `"HELLO WORLD YOU HOW"`)
- **HamNoSys codes** — optionally displays the HamNoSys notation for each gloss

API calls:
- `POST /api/text-to-handsign` → `handsignService.js`
- `POST /api/speech-to-handsign` → `handsignService.js`
- `GET /api/health` → `apiService.js`

---

### `LearnSign.js`

**Interactive ISL learning interface.**

Features:
- Alphabet buttons (A–Z) — click any letter to see the ISL sign animated on the avatar
- Word buttons (48 predefined ISL words) — click a word to see the full sign
- Same avatar selection and speed controls as `Convert.js`

Words available include: `HELLO`, `THANK YOU`, `PLEASE`, `SORRY`, `YES`, `NO`, `HELP`, `WATER`, `FOOD`, `FAMILY`, and 38 more (see `wordsData.json`).

Animation trigger: clicking a button calls `playWord(word, sceneRef)` or `playAnimation(letter, sceneRef)` from `animationPlayer.js`.

---

### `CreateVideo.js`

**Creates and saves an ISL video record via the video API.**

Form fields:
- Title
- Description
- Creator name
- Video type (educational, informational, personal, other)
- Content input mode: text, speech, or file upload
- Public / Private toggle

On submission:
- `POST ${baseURL}/videos/create-video` (Heroku API)
- Response contains a `videoId`
- `ConfirmModal` is shown with the video ID

---

### `Videos.js`

**Video gallery page.**

Features:
- Fetches all videos: `GET ${baseURL}/videos/all-videos`
- Search by video ID
- Displays videos as `VideoCard` components with title, description, and a link to `/sign-kit/video/:id`

---

### `Video.js`

**Individual video player.**

- Fetches a single video: `GET ${baseURL}/videos/:videoId`
- Extracts `content` field from the video object
- Passes content string to `playString()` — plays back the video on the 3D avatar
- Shows video metadata (title, description, creator, type)

---

### `Feedback.js`

Links to 5 Google Forms covering:
1. Overall website feedback
2. Audio-to-sign module
3. Sign correctness (expert evaluator)
4. Sign correctness (novice user)
5. Create Video module

---

## Custom Hooks

### `useThreeScene.js` — `client/src/Hooks/useThreeScene.js`

Manages the complete Three.js scene lifecycle for a page.

**Returns a `sceneRef`** object containing:
```js
{
  scene,        // THREE.Scene
  camera,       // THREE.PerspectiveCamera
  renderer,     // THREE.WebGLRenderer
  avatar,       // Loaded THREE.Object3D (the GLTF model)
  animations,   // [] — animation frame queue
  mixer,        // THREE.AnimationMixer (if used)
}
```

**Responsibilities:**
- Create `WebGLRenderer` with Raspberry Pi–friendly settings (no antialiasing, medium precision, 1:1 pixel ratio)
- Load the selected avatar model via `GLTFLoader`
- Set up lighting, camera position, and scene background
- Register a `ResizeObserver` to handle canvas resize
- Clean up all resources on component unmount via `threeCleanup.js`

**Usage:**
```js
const sceneRef = useThreeScene(canvasRef, selectedAvatar);
```

---

### `useAnimationEngine.js` — `client/src/Hooks/useAnimationEngine.js`

Drives the animation playback loop.

**Responsibilities:**
- Runs a `requestAnimationFrame` loop
- On each frame, dequeues one frame object from `sceneRef.current.animations`
- Applies bone transformations from the frame to the Three.js skeleton
- Respects `speed` (number of frames consumed per tick) and `paused` flags
- Cancels the animation frame on unmount

**Usage:**
```js
useAnimationEngine(sceneRef, speed, paused);
```

---

## Animation System

### How Animations Are Structured

Each animation is a flat array of **frame objects**. Each frame describes what to do to skeleton bones at that moment:

```js
// A single frame
[
  ["mixamorigLeftArm", "rotation", "z", 0.5, "+"],
  ["mixamorigRightHand", "rotation", "x", -0.3, "="],
  // ...more bone transforms
]
```

Each transform is a 5-tuple:
| Index | Meaning | Example values |
|---|---|---|
| 0 | Bone name | `"mixamorigLeftArm"` |
| 1 | Transform type | `"rotation"`, `"position"`, `"scale"` |
| 2 | Axis | `"x"`, `"y"`, `"z"` |
| 3 | Value | `0.5` (radians for rotation) |
| 4 | Operation | `"+"` (add), `"="` (set) |

### Data Sources

**Built-in word animations** — `client/src/Animations/Data/wordsData.json`  
JSON object keyed by word (uppercase). Each value is an array of frames:
```json
{
  "HELLO": [
    [ ["mixamorigRightArm", "rotation", "z", 0.4, "+"], ... ],
    ...
  ]
}
```

**Built-in alphabet animations** — `client/src/Animations/Alphabets/A.js` through `Z.js`  
Each file exports a named array (e.g., `export const A = [...]`). Aggregated by `alphabets.js`.

**Backend-generated animations** — returned by `POST /api/text-to-handsign`  
The NLP backend generates keyframes from HamNoSys codes in the same 5-tuple format.

### `animationPlayer.js`

Provides the public API for queuing animations:

| Function | Description |
|---|---|
| `playString(text, sceneRef)` | Splits text into words; tries word match first, falls back to letter-by-letter |
| `playWord(word, sceneRef)` | Queues a single word animation |
| `playAnimation(letter, sceneRef)` | Queues a single alphabet animation |
| `clearAnimations(sceneRef)` | Clears the animation queue |

### `enhancedAnimationPlayer.js`

Used by `ConvertEnhanced.js` to play backend-generated animations. Accepts the `animations` array from the API response and queues all keyframes into `sceneRef.current.animations`.

---

## Services

### `apiService.js` — `client/src/Services/apiService.js`

Communicates with the NLP backend for SiGML/HamNoSys output.

Base URL: `process.env.REACT_APP_API_URL || "http://localhost:8000"`

| Function | Endpoint | Description |
|---|---|---|
| `checkHealth()` | `GET /api/health` | Check if backend is up |
| `textToSign(text)` | `POST /api/text-to-sign` | Get gloss + HamNoSys + SiGML for text |
| `speechToSign(audioBlob)` | `POST /api/speech-to-sign` | Get gloss + HamNoSys from audio |

---

### `handsignService.js` — `client/src/Services/handsignService.js`

Communicates with the NLP backend for direct animation data.

| Function | Endpoint | Description |
|---|---|---|
| `checkAvailable()` | `GET /api/health` | Check if handsign service is up |
| `textToHandsign(text)` | `POST /api/text-to-handsign` | Get keyframe animations for text |
| `speechToHandsign(audioBlob)` | `POST /api/speech-to-handsign` | Get keyframe animations from audio |

---

### `audioRecorder.js` — `client/src/Services/audioRecorder.js`

Handles browser microphone recording.

Process:
1. `navigator.mediaDevices.getUserMedia({ audio: true })`
2. `MediaRecorder` captures WebM/Opus audio
3. Raw chunks collected into a `Blob`
4. Blob converted to WAV using `Web Audio API` (`AudioContext.decodeAudioData` + manual WAV encoding)
5. WAV `Blob` returned to the caller for upload to the backend

---

## Utilities

### `threeHelpers.js` — `client/src/Utils/threeHelpers.js`

Safe bone access utilities to prevent null reference errors:

- `getBone(avatar, boneName)` — returns the bone or `null` with a warning
- `applyTransform(bone, type, axis, value, op)` — safely applies a transform tuple
- `validateBoneName(boneName)` — checks if bone exists on the avatar

### `threeCleanup.js` — `client/src/Utils/threeCleanup.js`

Comprehensive Three.js resource disposal to prevent memory leaks:

- Traverses the scene graph and disposes all geometries, materials, and textures
- Calls `renderer.dispose()` and `renderer.forceContextLoss()`
- Removes the canvas DOM element from its parent
- Clears all refs to allow garbage collection

---

## Configuration

### `client/src/Config/config.js`

```js
export const baseURL = "https://sign-kit-api.herokuapp.com/sign-kit";
```

Used only by the video management pages (`CreateVideo`, `Videos`, `Video`) to communicate with the legacy Heroku-hosted Node.js video API.

### Environment Variables

| Variable | Default | Usage |
|---|---|---|
| `REACT_APP_API_URL` | `http://localhost:8000` | NLP backend base URL (apiService, handsignService) |

Create a `client/.env` file to override:
```
REACT_APP_API_URL=http://localhost:8000
```

---

## UI Libraries

| Library | Purpose |
|---|---|
| Bootstrap 5.1.3 | CSS grid, utilities, buttons |
| React Bootstrap 2.1.2 | React-wrapped Bootstrap components |
| Font Awesome 4.7.0 | Icons (microphone, play, etc.) |
| react-input-slider 6.0.1 | Speed control slider |
