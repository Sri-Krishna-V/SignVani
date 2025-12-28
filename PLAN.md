# SignVani Implementation Plan for GitHub Copilot

> **Context**: This is a production-ready Speech-to-Indian Sign Language (ISL) translation system for Raspberry Pi 4. You are assisting with implementation of an offline, edge-computing solution that converts spoken English to ISL visual output via HamNoSys encoding and SiGML animation.

---

## Project Metadata

**Target Platform**: Raspberry Pi 4 Model B (4GB RAM, ARM Cortex-A72)  
**OS**: Raspberry Pi OS 64-bit (Debian-based)  
**Development Environment**: Windows (initial development), deploy to RPi4 in Phase 7  
**Performance Target**: <1000ms end-to-end latency  
**Constraint**: Strictly offline (no cloud APIs)  
**Python Version**: 3.9+  
**Optimization Philosophy**: Memory-efficient with `__slots__`, generators, ARM-specific optimizations

---

## Architecture Overview

```
Audio Input (USB Mic) 
    ↓
[Audio Capture] PyAudio 16kHz mono
    ↓
[Voice Activity Detection] Energy threshold
    ↓
[Noise Filter] Spectral subtraction (scipy.fft)
    ↓
[ASR Engine] Vosk offline (Indian English model)
    ↓
[NLP Processing] Tokenization, Lemmatization, POS Tagging
    ↓
[Grammar Transform] SVO→SOV (rule-based)
    ↓
[Gloss Mapping] English→ISL gloss (uppercase convention)
    ↓
[Database Lookup] SQLite (gloss→HamNoSys, <1ms with LRU cache)
    ↓
[SiGML Generation] HamNoSys→XML
    ↓
Output (Console/Avatar)
```

---

## Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Audio Capture** | PyAudio 0.2.14 | Non-blocking streaming, RPi4 compatible |
| **ASR** | Vosk 0.3.45 (offline) | ~150MB model, <200ms latency, no cloud dependency |
| **Noise Reduction** | Spectral Subtraction (scipy.fft) | <50ms per chunk, CPU-friendly |
| **NLP** | NLTK 3.8.1 + spaCy 3.5.0 | Lightweight, <10ms transformation |
| **Grammar** | Rule-based POS parser | Deterministic, <1ms performance |
| **Database** | SQLite + FTS5 | <1ms exact match, fuzzy search for unknown words |
| **Sign Encoding** | HamNoSys (string-based) | 486 bytes/sign vs 150KB video |
| **Sign Rendering** | SiGML→Avatar (OpenGL ES) | Leverages Pi VideoCore GPU |

---

## Resource Budget

```
Memory (4GB total):
├─ Raspberry Pi OS: ~400MB
├─ Python Runtime: ~80MB
├─ Vosk Model: ~150-200MB
├─ NLTK Data: ~24MB
├─ SQLite Cache: ~50MB
├─ Buffers: ~100MB
└─ Available: ~3GB headroom ✓

Latency (<1000ms target):
├─ Audio Buffering: ~64ms
├─ Vosk ASR: ~200ms
├─ Noise Reduction: ~30-50ms
├─ NLP: ~10-15ms
├─ DB Lookup: <1ms
├─ SiGML Gen: <5ms
└─ Total: ~310-335ms ✓

CPU (ARM Cortex-A72 @ 1.5GHz):
└─ Peak load: 40-60% during transcription ✓
```

---

## Directory Structure

```
SignVani/
├── config/
│   ├── settings.py              # Frozen dataclasses (sample rates, buffers, paths)
│   ├── logging_config.py        # SD card-friendly logging (rotation)
│   └── constants.py             # Immutable constants
│
├── src/
│   ├── audio/
│   │   ├── audio_capture.py     # PyAudio non-blocking stream + queue
│   │   ├── noise_filter.py      # Spectral subtraction (scipy.fft, float32)
│   │   ├── vad.py               # Voice Activity Detection (energy threshold)
│   │   └── audio_buffer.py      # Circular buffer with __slots__
│   │
│   ├── asr/
│   │   ├── vosk_engine.py       # Vosk wrapper (thread-safe, singleton)
│   │   └── asr_worker.py        # Worker thread (consumes audio queue)
│   │
│   ├── nlp/
│   │   ├── text_processor.py    # Tokenize, clean, lemmatize
│   │   ├── grammar_transformer.py  # SVO→SOV rule-based (POS-driven)
│   │   ├── gloss_mapper.py      # English word→ISL gloss conversion
│   │   └── dataclasses.py       # ProcessedText, GlossPhrase (with __slots__)
│   │
│   ├── database/
│   │   ├── db_manager.py        # SQLite connection pool (thread-safe)
│   │   ├── schema.sql           # Table definitions with indexes
│   │   ├── seed_db.py           # Populate gloss→HamNoSys mappings
│   │   └── retriever.py         # Query methods with LRU caching
│   │
│   ├── sigml/
│   │   ├── generator.py         # HamNoSys→SiGML XML converter
│   │   └── avatar_player.py     # Avatar rendering (future)
│   │
│   ├── utils/
│   │   ├── thread_pool.py       # Priority queues, graceful shutdown
│   │   ├── profiler.py          # Latency tracking decorator
│   │   ├── exceptions.py        # Custom exception hierarchy
│   │   └── logging_utils.py     # Structured logging
│   │
│   └── pipeline/
│       ├── orchestrator.py      # Main pipeline coordinator
│       ├── event_bus.py         # Pub/sub for inter-thread communication
│       └── state_manager.py     # Pipeline state tracking
│
├── models/
│   ├── vosk/                    # vosk-model-small-en-in-0.4 (~40MB)
│   └── nltk_data/               # punkt, wordnet, stopwords (~24MB)
│
├── data/
│   └── signvani.db              # SQLite database (indexed)
│
├── tests/
│   ├── unit/                    # Unit tests per module
│   ├── integration/             # End-to-end pipeline tests
│   └── performance/             # Latency and memory benchmarks
│
├── scripts/
│   ├── setup_models.py          # Auto-download Vosk + NLTK data
│   ├── benchmark.py             # Performance profiling
│   └── deploy_rpi.sh            # RPi4 deployment automation
│
├── assets/
│   └── test_audio/              # Sample WAV files (16kHz mono)
│
├── main.py                      # Entry point
├── requirements.txt             # Production dependencies
└── README.md
```

---

## Implementation Instructions by Phase

### Phase 0: Project Scaffolding (Days 1-2)

**Goal**: Create directory structure and configuration system.

#### File: `config/settings.py`

```python
"""
Configuration management using frozen dataclasses.
All settings are immutable to prevent runtime modification.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AudioConfig:
    """Audio capture configuration optimized for ISL."""
    sample_rate: int = 16000  # Hz - optimal for Vosk
    channels: int = 1  # Mono
    chunk_size: int = 1024  # frames (~64ms @ 16kHz)
    format: str = "int16"  # PyAudio format
    device_index: Optional[int] = None  # None = auto-detect USB mic
    vad_threshold: float = 0.02  # Energy threshold for voice detection
    noise_profile_duration: int = 2  # seconds to learn noise profile

@dataclass(frozen=True)
class VoskConfig:
    """Vosk ASR engine configuration."""
    model_path: str = "models/vosk/vosk-model-small-en-in-0.4"
    max_alternatives: int = 1  # Memory optimization
    words_list: bool = False  # Disable extra features
    sample_rate: int = 16000  # Must match AudioConfig

@dataclass(frozen=True)
class NLPConfig:
    """NLP processing configuration."""
    use_spacy: bool = False  # Use NLTK by default (lighter)
    spacy_model: str = "en_core_web_sm"
    stopwords_file: Optional[str] = None  # None = NLTK default
    lemmatize: bool = True
    remove_punctuation: bool = True

@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "data/signvani.db"
    connection_pool_size: int = 3  # Thread-safe pooling
    lru_cache_size: int = 100  # Most common glosses
    query_timeout: float = 0.5  # seconds
    enable_fts5: bool = True  # Full-text search for unknown words

@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline orchestration configuration."""
    audio_queue_size: int = 10
    transcript_queue_size: int = 5
    gloss_queue_size: int = 3
    watchdog_timeout: float = 5.0  # seconds
    num_workers: int = 4  # ASR, NLP, DB, UI threads
    graceful_shutdown_timeout: float = 10.0  # seconds

@dataclass(frozen=True)
class AppConfig:
    """Master application configuration."""
    audio: AudioConfig = AudioConfig()
    vosk: VoskConfig = VoskConfig()
    nlp: NLPConfig = NLPConfig()
    database: DatabaseConfig = DatabaseConfig()
    pipeline: PipelineConfig = PipelineConfig()
    log_level: str = "INFO"
    log_file: str = "logs/signvani.log"
    log_rotation: str = "100 MB"  # SD card friendly
```

**Instructions for Copilot**:

- Use frozen dataclasses for all configuration
- No mutable global state
- Provide validation methods for critical settings (e.g., sample_rate must match Vosk)

---

#### File: `requirements.txt`

```
# Core Audio & ASR
vosk==0.3.45
PyAudio==0.2.14

# Numerics & Signal Processing
numpy==1.24.3
scipy==1.10.1

# NLP
nltk==3.8.1
spacy==3.5.0

# Utilities
pydantic==2.0.0
loguru==0.7.0

# Development
pytest==7.4.0
pytest-cov==4.1.0
pytest-timeout==2.1.0
memory-profiler==0.61.0
```

**Installation Notes**:

- **Windows**: `pip install pipwin && pipwin install pyaudio`
- **RPi4**: `sudo apt-get install portaudio19-dev libatlas-base-dev` first

---

#### File: `scripts/setup_models.py`

```python
"""
Automated model downloader for Vosk and NLTK.
Downloads models with checksum verification.
"""
import os
import urllib.request
import zipfile
import nltk
from pathlib import Path

VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
VOSK_MODEL_DIR = Path("models/vosk")
NLTK_DATA_DIR = Path("models/nltk_data")

def download_vosk_model():
    """Download and extract Vosk Indian English model (~40MB)."""
    print("Downloading Vosk model...")
    VOSK_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = VOSK_MODEL_DIR / "model.zip"
    
    urllib.request.urlretrieve(VOSK_MODEL_URL, zip_path)
    
    print("Extracting Vosk model...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(VOSK_MODEL_DIR)
    
    zip_path.unlink()  # Delete zip file
    print("✓ Vosk model ready")

def download_nltk_data():
    """Download NLTK data packages (~24MB total)."""
    print("Downloading NLTK data...")
    NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    nltk.data.path.append(str(NLTK_DATA_DIR))
    
    nltk.download('punkt', download_dir=str(NLTK_DATA_DIR))
    nltk.download('wordnet', download_dir=str(NLTK_DATA_DIR))
    nltk.download('stopwords', download_dir=str(NLTK_DATA_DIR))
    nltk.download('averaged_perceptron_tagger', download_dir=str(NLTK_DATA_DIR))
    
    print("✓ NLTK data ready")

if __name__ == "__main__":
    download_vosk_model()
    download_nltk_data()
    print("\n✓ All models downloaded successfully!")
```

**Instructions for Copilot**:

- Use pathlib for cross-platform paths
- Add checksum verification for production
- Handle network errors gracefully

---

### Phase 1: Audio Subsystem (Days 3-5)

**Goal**: Implement audio capture, VAD, and noise reduction with <100ms latency.

#### File: `src/audio/audio_buffer.py`

```python
"""
Circular audio buffer with thread-safe operations.
Uses __slots__ for memory efficiency.
"""
import numpy as np
import threading
from typing import Optional

class CircularAudioBuffer:
    """Thread-safe circular buffer for audio chunks."""
    __slots__ = ('buffer', 'write_pos', 'read_pos', 'size', 'lock', 'capacity')
    
    def __init__(self, capacity: int = 60):
        """
        Initialize buffer.
        
        Args:
            capacity: Number of seconds to buffer @ 16kHz
        """
        self.capacity = capacity * 16000  # samples
        self.buffer = np.zeros(self.capacity, dtype=np.int16)
        self.write_pos = 0
        self.read_pos = 0
        self.size = 0
        self.lock = threading.Lock()
    
    def write(self, chunk: np.ndarray) -> bool:
        """
        Write audio chunk to buffer.
        
        Args:
            chunk: Audio data (numpy array)
        
        Returns:
            True if successful, False if overflow (oldest data dropped)
        """
        with self.lock:
            chunk_size = len(chunk)
            
            # Handle overflow by dropping oldest data
            if self.size + chunk_size > self.capacity:
                overflow = (self.size + chunk_size) - self.capacity
                self.read_pos = (self.read_pos + overflow) % self.capacity
                self.size -= overflow
            
            # Write chunk (may wrap around)
            end_pos = self.write_pos + chunk_size
            if end_pos <= self.capacity:
                self.buffer[self.write_pos:end_pos] = chunk
            else:
                # Wrap around
                first_part = self.capacity - self.write_pos
                self.buffer[self.write_pos:] = chunk[:first_part]
                self.buffer[:chunk_size - first_part] = chunk[first_part:]
            
            self.write_pos = end_pos % self.capacity
            self.size += chunk_size
            
            return True
    
    def read(self, num_samples: int) -> Optional[np.ndarray]:
        """
        Read audio samples from buffer.
        
        Args:
            num_samples: Number of samples to read
        
        Returns:
            Audio data or None if insufficient data
        """
        with self.lock:
            if self.size < num_samples:
                return None
            
            # Read samples (may wrap around)
            end_pos = self.read_pos + num_samples
            if end_pos <= self.capacity:
                result = self.buffer[self.read_pos:end_pos].copy()
            else:
                # Wrap around
                first_part = self.capacity - self.read_pos
                result = np.concatenate([
                    self.buffer[self.read_pos:],
                    self.buffer[:num_samples - first_part]
                ])
            
            self.read_pos = end_pos % self.capacity
            self.size -= num_samples
            
            return result
```

**Instructions for Copilot**:

- Use `__slots__` for all data classes to reduce memory overhead
- Thread-safe operations with `threading.Lock`
- Circular buffer logic handles wraparound correctly

---

#### File: `src/audio/vad.py`

```python
"""
Voice Activity Detection using energy threshold.
Distinguishes speech from silence/noise.
"""
import numpy as np
from collections import deque

class SimpleVAD:
    """Energy-based Voice Activity Detector."""
    __slots__ = ('threshold', 'smoothing_window', 'energy_history')
    
    def __init__(self, threshold: float = 0.02, window_size: int = 3):
        """
        Initialize VAD.
        
        Args:
            threshold: Energy threshold (0-1 range)
            window_size: Median filter window for smoothing
        """
        self.threshold = threshold
        self.smoothing_window = window_size
        self.energy_history = deque(maxlen=window_size)
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Determine if audio chunk contains speech.
        
        Args:
            audio_chunk: Audio data (numpy array, int16)
        
        Returns:
            True if speech detected, False if silence/noise
        """
        # Normalize to [-1, 1] range
        normalized = audio_chunk.astype(np.float32) / 32768.0
        
        # Compute RMS energy
        energy = np.sqrt(np.mean(normalized ** 2))
        
        # Smoothing: median filter over last N frames
        self.energy_history.append(energy)
        smoothed_energy = np.median(list(self.energy_history))
        
        return smoothed_energy > self.threshold
    
    def update_threshold(self, silence_chunk: np.ndarray):
        """
        Adaptive threshold update based on silence periods.
        
        Args:
            silence_chunk: Confirmed silence audio
        """
        normalized = silence_chunk.astype(np.float32) / 32768.0
        silence_energy = np.sqrt(np.mean(normalized ** 2))
        
        # Set threshold as 2x silence energy
        self.threshold = silence_energy * 2.0
```

**Instructions for Copilot**:

- Use RMS energy for speech detection
- Implement 3-frame median filter to reduce jitter
- Adaptive threshold learning during silence periods

---

#### File: `src/audio/noise_filter.py`

```python
"""
Spectral subtraction noise reduction.
Reduces background noise without heavy computational cost.
"""
import numpy as np
from scipy.fft import rfft, irfft

class SpectralSubtraction:
    """Spectral subtraction noise filter."""
    __slots__ = ('alpha', 'beta', 'noise_profile', 'fft_size', 'sample_rate')
    
    def __init__(self, alpha: float = 2.0, beta: float = 0.01, 
                 fft_size: int = 1024, sample_rate: int = 16000):
        """
        Initialize spectral subtraction filter.
        
        Args:
            alpha: Over-subtraction factor (higher = more aggressive)
            beta: Spectral floor (prevents zero division)
            fft_size: FFT window size (1024 = ~64ms @ 16kHz)
            sample_rate: Audio sample rate
        """
        self.alpha = alpha
        self.beta = beta
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.noise_profile = None  # Updated during silence
    
    def filter(self, chunk: np.ndarray) -> np.ndarray:
        """
        Apply spectral subtraction to audio chunk.
        
        Args:
            chunk: Audio data (numpy array, int16)
        
        Returns:
            Filtered audio (same shape and dtype)
        """
        # Convert to float32 for efficiency
        audio_float = chunk.astype(np.float32)
        
        # FFT
        spectrum = rfft(audio_float, n=self.fft_size)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        
        # Spectral subtraction
        if self.noise_profile is not None:
            # Subtract alpha * noise_magnitude
            clean_magnitude = magnitude - self.alpha * self.noise_profile
            
            # Apply spectral floor
            clean_magnitude = np.maximum(clean_magnitude, self.beta * magnitude)
        else:
            # No noise profile yet, pass through
            clean_magnitude = magnitude
        
        # Reconstruct signal
        clean_spectrum = clean_magnitude * np.exp(1j * phase)
        clean_audio = irfft(clean_spectrum, n=len(audio_float))
        
        # Convert back to int16
        return np.clip(clean_audio, -32768, 32767).astype(np.int16)
    
    def update_noise_profile(self, silence_chunk: np.ndarray):
        """
        Update noise profile during silence periods.
        
        Args:
            silence_chunk: Confirmed silence audio
        """
        audio_float = silence_chunk.astype(np.float32)
        spectrum = rfft(audio_float, n=self.fft_size)
        noise_magnitude = np.abs(spectrum)
        
        if self.noise_profile is None:
            # Initialize
            self.noise_profile = noise_magnitude
        else:
            # Rolling average (0.9 old + 0.1 new)
            self.noise_profile = 0.9 * self.noise_profile + 0.1 * noise_magnitude
```

**Instructions for Copilot**:

- Use `scipy.fft.rfft` (real FFT) for efficiency
- Work with float32 to reduce memory bandwidth
- Implement rolling average for noise profile updates

---

#### File: `src/audio/audio_capture.py`

```python
"""
Non-blocking audio capture using PyAudio.
Feeds audio queue for ASR processing.
"""
import pyaudio
import queue
import threading
import numpy as np
from typing import Optional
from .vad import SimpleVAD
from .noise_filter import SpectralSubtraction
from ..nlp.dataclasses import AudioChunk

class AudioCapture:
    """Non-blocking audio capture with preprocessing."""
    
    def __init__(self, config, audio_queue: queue.Queue):
        """
        Initialize audio capture.
        
        Args:
            config: AudioConfig instance
            audio_queue: Queue to push AudioChunk objects
        """
        self.config = config
        self.audio_queue = audio_queue
        
        self.vad = SimpleVAD(threshold=config.vad_threshold)
        self.noise_filter = SpectralSubtraction(fft_size=config.chunk_size)
        
        self.pyaudio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.running = False
    
    def _callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback (runs in separate thread)."""
        # Convert to numpy
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Voice Activity Detection
        is_speech = self.vad.is_speech(audio_data)
        
        if is_speech:
            # Apply noise filtering
            filtered = self.noise_filter.filter(audio_data)
            
            # Push to queue
            chunk = AudioChunk(
                data=filtered,
                timestamp=time_info['current_time'],
                sample_rate=self.config.sample_rate
            )
            
            try:
                self.audio_queue.put_nowait(chunk)
            except queue.Full:
                # Log warning: queue full, dropping frame
                pass
        else:
            # Update noise profile during silence
            self.noise_filter.update_noise_profile(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def start(self):
        """Start audio capture stream."""
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self.config.device_index,
            frames_per_buffer=self.config.chunk_size,
            stream_callback=self._callback
        )
        
        self.running = True
        self.stream.start_stream()
    
    def stop(self):
        """Stop audio capture stream."""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()
```

**Instructions for Copilot**:

- Use PyAudio callback mode (non-blocking)
- VAD runs first, noise filter only on speech
- Use `put_nowait` to avoid blocking if queue full

---

#### File: `src/nlp/dataclasses.py`

```python
"""
Lightweight data classes with __slots__ for memory efficiency.
"""
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

@dataclass
class AudioChunk:
    """Audio data chunk."""
    __slots__ = ('data', 'timestamp', 'sample_rate')
    data: np.ndarray
    timestamp: float
    sample_rate: int

@dataclass
class TranscriptEvent:
    """ASR transcript event."""
    __slots__ = ('text', 'confidence', 'timestamp', 'is_final')
    text: str
    confidence: float
    timestamp: float
    is_final: bool

@dataclass
class ProcessedText:
    """Processed text after NLP."""
    __slots__ = ('tokens', 'pos_tags', 'original', 'timestamp')
    tokens: List[str]
    pos_tags: List[Tuple[str, str]]
    original: str
    timestamp: float

@dataclass
class GlossPhrase:
    """ISL gloss phrase."""
    __slots__ = ('glosses', 'original_text', 'timestamp')
    glosses: List[str]  # Uppercase ISL glosses
    original_text: str
    timestamp: float
```

**Instructions for Copilot**:

- Always use `__slots__` for data classes to reduce memory overhead
- Keep dataclasses simple (no methods, just data)

---

### Phase 2: ASR Integration (Days 6-8)

**Goal**: Integrate Vosk offline ASR with <200ms latency.

#### File: `src/asr/vosk_engine.py`

```python
"""
Vosk offline speech recognition engine wrapper.
Thread-safe singleton implementation.
"""
import json
from vosk import Model, KaldiRecognizer
import threading
from typing import Optional

class VoskEngine:
    """Thread-safe Vosk ASR engine."""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config):
        """Initialize Vosk model (called once)."""
        if self._initialized:
            return
        
        self.config = config
        self.model = Model(config.model_path)
        self.recognizer = KaldiRecognizer(
            self.model, 
            config.sample_rate
        )
        
        # Optimization: disable extra features
        self.recognizer.SetMaxAlternatives(config.max_alternatives)
        self.recognizer.SetWords(config.words_list)
        
        self._initialized = True
    
    def process_chunk(self, audio_chunk) -> Optional[str]:
        """
        Process audio chunk and return transcript if ready.
        
        Args:
            audio_chunk: AudioChunk object
        
        Returns:
            Transcript string if final, None if partial/accumulating
        """
        # Feed audio bytes to recognizer
        audio_bytes = audio_chunk.data.tobytes()
        
        if self.recognizer.AcceptWaveform(audio_bytes):
            # Final result available
            result = json.loads(self.recognizer.Result())
            return result.get('text', '')
        else:
            # Still accumulating (partial result)
            return None
    
    def reset(self):
        """Reset recognizer state between utterances."""
        self.recognizer = KaldiRecognizer(
            self.model,
            self.config.sample_rate
        )
        self.recognizer.SetMaxAlternatives(self.config.max_alternatives)
        self.recognizer.SetWords(self.config.words_list)
    
    def get_final_result(self) -> str:
        """Get final result and reset."""
        result = json.loads(self.recognizer.FinalResult())
        self.reset()
        return result.get('text', '')
```

**Instructions for Copilot**:

- Use singleton pattern for model (expensive to load multiple times)
- Thread-safe with `threading.Lock`
- Parse JSON results from Vosk

---

#### File: `src/asr/asr_worker.py`

```python
"""
ASR worker thread that consumes audio queue.
"""
import queue
import threading
from .vosk_engine import VoskEngine
from ..nlp.dataclasses import TranscriptEvent

class ASRWorker(threading.Thread):
    """Worker thread for ASR processing."""
    
    def __init__(self, audio_queue: queue.Queue, 
                 transcript_queue: queue.Queue, config):
        """
        Initialize ASR worker.
        
        Args:
            audio_queue: Input queue (AudioChunk objects)
            transcript_queue: Output queue (TranscriptEvent objects)
            config: VoskConfig instance
        """
        super().__init__(daemon=True, name="ASRWorker")
        self.audio_queue = audio_queue
        self.transcript_queue = transcript_queue
        self.config = config
        
        self.vosk = VoskEngine(config)
        self.running = False
    
    def run(self):
        """Main worker loop."""
        self.running = True
        
        while self.running:
            try:
                # Get audio chunk with timeout
                chunk = self.audio_queue.get(timeout=1.0)
                
                # Process with Vosk
                transcript = self.vosk.process_chunk(chunk)
                
                if transcript:
                    # Final transcript ready
                    event = TranscriptEvent(
                        text=transcript,
                        confidence=0.95,  # Vosk doesn't provide confidence
                        timestamp=chunk.timestamp,
                        is_final=True
                    )
                    
                    # Push to transcript queue
                    self.transcript_queue.put(event)
                    
                    # Reset for next utterance
                    self.vosk.reset()
                
            except queue.Empty:
                # No audio available, continue
                continue
            except Exception as e:
                # Log error and continue
                print(f"ASR error: {e}")
                continue
    
    def stop(self):
        """Stop worker thread."""
        self.running = False
```

**Instructions for Copilot**:

- Worker thread runs in daemon mode
- Use timeout on queue.get to allow graceful shutdown
- Error handling: log and continue (don't crash)

---

### Phase 3: Database Layer (Days 9-10)

**Goal**: SQLite database with <1ms lookup latency using LRU cache.

#### File: `src/database/schema.sql`

```sql
-- Gloss-to-HamNoSys mapping table
CREATE TABLE IF NOT EXISTS gloss_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    english_gloss TEXT NOT NULL UNIQUE,
    hamnosys_string TEXT NOT NULL,
    frequency INTEGER DEFAULT 0,  -- Usage frequency for cache prioritization
    category TEXT,  -- 'action', 'noun', 'adjective', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by gloss
CREATE INDEX IF NOT EXISTS idx_gloss_frequency 
ON gloss_mapping(english_gloss, frequency DESC);

-- Full-text search for fuzzy matching (unknown words)
CREATE VIRTUAL TABLE IF NOT EXISTS gloss_fts 
USING fts5(english_gloss, hamnosys_string, content=gloss_mapping);

-- Trigger to keep FTS table in sync
CREATE TRIGGER IF NOT EXISTS gloss_fts_sync_insert 
AFTER INSERT ON gloss_mapping BEGIN
    INSERT INTO gloss_fts(rowid, english_gloss, hamnosys_string)
    VALUES (new.id, new.english_gloss, new.hamnosys_string);
END;

CREATE TRIGGER IF NOT EXISTS gloss_fts_sync_update 
AFTER UPDATE ON gloss_mapping BEGIN
    UPDATE gloss_fts 
    SET english_gloss = new.english_gloss, 
        hamnosys_string = new.hamnosys_string
    WHERE rowid = new.id;
END;

-- Table to log unknown words for future training
CREATE TABLE IF NOT EXISTS unknown_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unknown_frequency 
ON unknown_words(occurrence_count DESC);
```

**Instructions for Copilot**:

- Use FTS5 (full-text search) for fuzzy matching
- Index on frequency for cache prioritization
- Triggers keep FTS table synchronized

---

#### File: `src/database/seed_db.py`

```python
"""
Seed database with initial gloss mappings.
Uses placeholder HamNoSys data (real data provided by linguistics team).
"""
import sqlite3
from pathlib import Path

# Placeholder HamNoSys strings (real data to be provided)
INITIAL_GLOSSES = {
    'HELLO': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmd,hamshoulders,hamplus',
    'THANK-YOU': 'hamflathand,hamthumboutmod,hamextfingerul,hampalmd,hamchest,hamlrat,hamtouch',
    'STUDENT': 'hamflathand,hampalmu,hamlrat,hamtouch,hamhead',
    'GO': 'hamindex,hampalmd,hamlrat',
    'HOME': 'hammiddle,hampalmu,hamchest',
    'NAME': 'hamflathand,hamextfingerl,hampalmd,hamshoulders',
    'WELCOME': 'hamflathand,hamextfingeru,hampalmu,hamchest',
    'GOOD': 'hamthumboutmod,hamextfingeru,hampalmd,hamchest',
    'BAD': 'hamfinger2,hamthumbacross,hamextfingerl,hampalmu',
    'HELP': 'hamflathand,hamextfingeru,hampalml,hamshoulders',
    'WANT': 'hamfinger2,hamthumboutmod,hamextfingerul,hampalmu',
    'EAT': 'hamfinger2,hamthumboutmod,hamextfingerul,hampalmd,hammouth',
    'DRINK': 'hammiddle,hamthumbacross,hamextfingeru,hampalml,hammouth',
    'LEARN': 'hamflathand,hamextfingerl,hampalmu,hamhead',
    'TEACH': 'hamflathand,hamextfingeru,hampalmd,hamshoulders',
    'WORK': 'hamfist,hamextfingerd,hampalmd,hamchest',
    'PLAY': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmu',
    'HAPPY': 'hamflathand,hamextfingeru,hampalmd,hamchest,hamsmile',
    'SAD': 'hamflathand,hamextfingerd,hampalmd,hamchest,hamfrown',
    'SORRY': 'hamfist,hamextfingeru,hampalmd,hamchest,hamrepeat',
}

def seed_database(db_path: str = "data/signvani.db"):
    """
    Seed database with initial gloss mappings.
    
    Args:
        db_path: Path to SQLite database
    """
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema = f.read()
    
    # Create tables
    cursor.executescript(schema)
    
    # Insert gloss mappings
    for gloss, hamnosys in INITIAL_GLOSSES.items():
        cursor.execute("""
            INSERT OR IGNORE INTO gloss_mapping 
            (english_gloss, hamnosys_string, frequency, category)
            VALUES (?, ?, 10, 'common')
        """, (gloss, hamnosys))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database seeded with {len(INITIAL_GLOSSES)} glosses")

if __name__ == "__main__":
    seed_database()
```

**Instructions for Copilot**:

- Placeholder HamNoSys strings (replace with real data later)
- Use `INSERT OR IGNORE` to avoid duplicates
- Category='common' for initial glosses (high frequency)

---

#### File: `src/database/retriever.py`

```python
"""
Fast gloss retrieval with LRU caching.
"""
import sqlite3
from functools import lru_cache
from typing import Optional
import threading

class GlossRetriever:
    """Thread-safe gloss retriever with caching."""
    
    def __init__(self, db_path: str, cache_size: int = 100):
        """
        Initialize retriever.
        
        Args:
            db_path: Path to SQLite database
            cache_size: LRU cache size
        """
        self.db_path = db_path
        self.cache_size = cache_size
        self.lock = threading.Lock()
        
        # Connection pool (thread-local storage)
        self.local = threading.local()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    @lru_cache(maxsize=100)
    def get_hamnosys(self, gloss: str) -> Optional[str]:
        """
        Get HamNoSys string for gloss (exact match).
        
        Args:
            gloss: ISL gloss (uppercase)
        
        Returns:
            HamNoSys string or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        result = cursor.execute("""
            SELECT hamnosys_string FROM gloss_mapping
            WHERE english_gloss = ?
        """, (gloss,)).fetchone()
        
        if result:
            # Update frequency for cache prioritization
            cursor.execute("""
                UPDATE gloss_mapping 
                SET frequency = frequency + 1
                WHERE english_gloss = ?
            """, (gloss,))
            conn.commit()
            
            return result['hamnosys_string']
        
        return None
    
    def fuzzy_lookup(self, gloss: str, threshold: float = 0.5) -> Optional[str]:
        """
        Fuzzy match using FTS5 for unknown words.
        
        Args:
            gloss: ISL gloss (uppercase)
            threshold: Similarity threshold (0-1)
        
        Returns:
            Best matching HamNoSys string or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # FTS5 search
        result = cursor.execute("""
            SELECT m.hamnosys_string, 
                   rank
            FROM gloss_fts f
            JOIN gloss_mapping m ON f.rowid = m.id
            WHERE gloss_fts MATCH ?
            ORDER BY rank
            LIMIT 1
        """, (gloss,)).fetchone()
        
        if result:
            return result['hamnosys_string']
        
        return None
    
    def log_unknown_word(self, word: str):
        """
        Log unknown word for future training.
        
        Args:
            word: Unknown word
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO unknown_words (word, occurrence_count)
            VALUES (?, 1)
            ON CONFLICT(word) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                last_seen = CURRENT_TIMESTAMP
        """, (word,))
        conn.commit()
```

**Instructions for Copilot**:

- Use `functools.lru_cache` for fast repeated lookups
- Thread-local storage for database connections
- FTS5 for fuzzy matching (handles typos, variations)

---

### Phase 4: NLP Engine (Days 11-13)

**Goal**: Text processing and SVO→SOV grammar transformation with <15ms latency.

#### File: `src/nlp/text_processor.py`

```python
"""
Text preprocessing: tokenization, lemmatization, POS tagging.
"""
import string
import nltk
from typing import List, Tuple

class TextProcessor:
    """Lightweight NLP text processor."""
    
    def __init__(self, nltk_data_dir: str = "models/nltk_data"):
        """Initialize processor."""
        nltk.data.path.append(nltk_data_dir)
        
        # Load NLTK resources
        self.tokenizer = nltk.tokenize.word_tokenize
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
        # Punctuation to remove
        self.punctuation = set(string.punctuation)
    
    def process(self, text: str) -> List[str]:
        """
        Process text: lowercase, tokenize, lemmatize.
        
        Args:
            text: Raw input text
        
        Returns:
            List of processed tokens
        """
        # Lowercase
        text = text.lower()
        
        # Tokenize
        tokens = self.tokenizer(text)
        
        # Remove punctuation
        tokens = [t for t in tokens if t not in self.punctuation]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        
        return tokens
    
    def get_pos_tags(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """
        Get Part-of-Speech tags.
        
        Args:
            tokens: List of tokens
        
        Returns:
            List of (token, POS_tag) tuples
        """
        return nltk.pos_tag(tokens)
    
    def filter_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords (except subject pronouns for ISL).
        
        Args:
            tokens: List of tokens
        
        Returns:
            Filtered tokens
        """
        # Keep subject pronouns (I, you, he, she, etc.)
        subject_pronouns = {'i', 'you', 'he', 'she', 'we', 'they'}
        
        return [t for t in tokens 
                if t not in self.stopwords or t in subject_pronouns]
```

**Instructions for Copilot**:

- Use NLTK for lightweight NLP (avoid spaCy unless needed)
- Keep subject pronouns (important for ISL grammar)
- Target: <5ms for typical sentence

---

#### File: `src/nlp/grammar_transformer.py`

```python
"""
SVO→SOV grammar transformation for Indian Sign Language.
Rule-based approach (no ML needed).
"""
from typing import List, Tuple
from .text_processor import TextProcessor

class GrammarTransformer:
    """Rule-based SVO→SOV transformer."""
    
    def __init__(self, text_processor: TextProcessor):
        """Initialize transformer."""
        self.text_processor = text_processor
        
        # Auxiliary verbs (skip these in reordering)
        self.aux_verbs = {
            'is', 'am', 'are', 'was', 'were',
            'have', 'has', 'had',
            'do', 'does', 'did',
            'will', 'would', 'shall', 'should',
            'can', 'could', 'may', 'might', 'must'
        }
        
        # Verb suffixes for heuristic detection
        self.verb_suffixes = {'-ing', '-ed', '-es', '-s', '-en'}
    
    def transform_svo_to_sov(self, text: str) -> str:
        """
        Transform English SVO to ISL SOV.
        
        Examples:
            "I eat apple" → "I apple eat"
            "She goes home" → "She home go"
            "What is your name?" → "Your name what?"
        
        Args:
            text: English text (SVO order)
        
        Returns:
            Transformed text (SOV order)
        """
        # Get tokens and POS tags
        tokens = self.text_processor.process(text)
        pos_tags = self.text_processor.get_pos_tags(tokens)
        
        # Identify subject, verb, object
        subject, verb, obj = self._parse_svo(tokens, pos_tags)
        
        # Reorder: Subject Object Verb
        if subject and verb:
            if obj:
                # Complete SVO → SOV
                result = subject + obj + verb
            else:
                # SV → SV (no object)
                result = subject + verb
        else:
            # Fallback: keep original order
            result = tokens
        
        return ' '.join(result).upper()  # ISL convention: uppercase
    
    def _parse_svo(self, tokens: List[str], pos_tags: List[Tuple[str, str]]) \
            -> Tuple[List[str], List[str], List[str]]:
        """
        Parse tokens into Subject, Verb, Object components.
        
        Args:
            tokens: List of tokens
            pos_tags: List of (token, POS) tuples
        
        Returns:
            (subject_tokens, verb_tokens, object_tokens)
        """
        subject = []
        verb = []
        obj = []
        
        current_component = subject  # Start with subject
        
        for token, pos in pos_tags:
            # Skip auxiliary verbs
            if token in self.aux_verbs:
                continue
            
            # Check if verb
            if self._is_verb(token, pos):
                current_component = verb
                verb.append(token)
            elif current_component is verb:
                # After verb → object
                current_component = obj
                obj.append(token)
            else:
                # Before verb → subject
                current_component.append(token)
        
        return subject, verb, obj
    
    def _is_verb(self, token: str, pos_tag: str) -> bool:
        """
        Check if token is a verb.
        
        Args:
            token: Token
            pos_tag: POS tag (VB, VBZ, VBG, etc.)
        
        Returns:
            True if verb
        """
        # POS tag starts with VB
        if pos_tag.startswith('VB'):
            return True
        
        # Heuristic: ends with verb suffix
        for suffix in self.verb_suffixes:
            if token.endswith(suffix):
                return True
        
        return False
```

**Instructions for Copilot**:

- Rule-based parsing (no ML overhead)
- Skip auxiliary verbs (they're redundant in ISL)
- Target: <10ms for typical sentence

---

#### File: `src/nlp/gloss_mapper.py`

```python
"""
Map English words to ISL glosses.
Handles unknown words with fingerspelling fallback.
"""
from typing import List
from .grammar_transformer import GrammarTransformer
from ..database.retriever import GlossRetriever
from .dataclasses import GlossPhrase

class GlossMapper:
    """Map English text to ISL glosses."""
    
    def __init__(self, grammar_transformer: GrammarTransformer,
                 gloss_retriever: GlossRetriever):
        """Initialize mapper."""
        self.grammar_transformer = grammar_transformer
        self.retriever = gloss_retriever
    
    def text_to_gloss(self, text: str, timestamp: float) -> GlossPhrase:
        """
        Convert English text to ISL gloss phrase.
        
        Args:
            text: English text
            timestamp: Timestamp from audio
        
        Returns:
            GlossPhrase with ordered glosses
        """
        # Transform grammar (SVO→SOV)
        transformed = self.grammar_transformer.transform_svo_to_sov(text)
        
        # Tokenize
        tokens = transformed.split()
        
        # Map each token to gloss
        glosses = []
        for token in tokens:
            gloss = self.retriever.get_hamnosys(token)
            
            if gloss is None:
                # Try fuzzy match
                gloss = self.retriever.fuzzy_lookup(token)
            
            if gloss is None:
                # Fallback: fingerspelling
                gloss = self._fingerspell(token)
                self.retriever.log_unknown_word(token)
            
            glosses.append(gloss)
        
        return GlossPhrase(
            glosses=glosses,
            original_text=text,
            timestamp=timestamp
        )
    
    def _fingerspell(self, word: str) -> str:
        """
        Generate fingerspelling representation.
        
        Args:
            word: Unknown word
        
        Returns:
            Fingerspelling string (e.g., "H-E-L-L-O")
        """
        return '-'.join(word.upper())
```

**Instructions for Copilot**:

- Three-tier fallback: exact → fuzzy → fingerspelling
- Log unknown words for future training
- Target: <15ms total NLP pipeline

---

### Phase 5: SiGML Generation (Days 14-15)

**Goal**: Convert HamNoSys to SiGML XML format.

#### File: `src/sigml/generator.py`

```python
"""
Generate SiGML (Signing Gesture Markup Language) from HamNoSys.
"""
from typing import List
from ..nlp.dataclasses import GlossPhrase
import xml.etree.ElementTree as ET

class SiGMLGenerator:
    """Convert HamNoSys to SiGML XML."""
    
    def generate(self, gloss_phrase: GlossPhrase) -> str:
        """
        Generate SiGML XML from gloss phrase.
        
        Args:
            gloss_phrase: GlossPhrase with HamNoSys strings
        
        Returns:
            SiGML XML string
        """
        # Create root element
        root = ET.Element('sigml')
        
        # Add each sign
        for gloss in gloss_phrase.glosses:
            sign = ET.SubElement(root, 'hamgestural_sign')
            sign.set('gloss', gloss.split(',')[0])  # Use first token as gloss label
            
            # Add manual sign (hand movements)
            manual = ET.SubElement(sign, 'sign_manual')
            manual.text = gloss
        
        # Convert to string
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Add XML declaration
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
    
    def _escape_xml(self, text: str) -> str:
        """
        Escape XML special characters.
        
        Args:
            text: Raw text
        
        Returns:
            XML-safe text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
```

**Instructions for Copilot**:

- Use xml.etree.ElementTree for XML generation
- Escape special characters
- Target: <5ms

---

### Phase 6: Pipeline Integration (Days 16-19)

**Goal**: Integrate all components with <1000ms end-to-end latency.

#### File: `src/pipeline/orchestrator.py`

```python
"""
Main pipeline orchestrator.
Coordinates all subsystems and worker threads.
"""
import queue
import signal
import sys
from typing import Optional
from ..audio.audio_capture import AudioCapture
from ..asr.asr_worker import ASRWorker
from ..nlp.text_processor import TextProcessor
from ..nlp.grammar_transformer import GrammarTransformer
from ..nlp.gloss_mapper import GlossMapper
from ..database.retriever import GlossRetriever
from ..sigml.generator import SiGMLGenerator

class PipelineOrchestrator:
    """Main pipeline coordinator."""
    
    def __init__(self, config):
        """Initialize pipeline."""
        self.config = config
        
        # Queues
        self.audio_queue = queue.Queue(maxsize=config.pipeline.audio_queue_size)
        self.transcript_queue = queue.Queue(maxsize=config.pipeline.transcript_queue_size)
        self.gloss_queue = queue.Queue(maxsize=config.pipeline.gloss_queue_size)
        
        # Components
        self.audio_capture = AudioCapture(config.audio, self.audio_queue)
        self.asr_worker = ASRWorker(
            self.audio_queue,
            self.transcript_queue,
            config.vosk
        )
        
        # NLP pipeline
        self.text_processor = TextProcessor()
        self.grammar_transformer = GrammarTransformer(self.text_processor)
        self.gloss_retriever = GlossRetriever(
            config.database.db_path,
            config.database.lru_cache_size
        )
        self.gloss_mapper = GlossMapper(
            self.grammar_transformer,
            self.gloss_retriever
        )
        
        # SiGML generator
        self.sigml_generator = SiGMLGenerator()
        
        self.running = False
    
    def start(self):
        """Start pipeline."""
        print("Starting SignVani pipeline...")
        
        # Start audio capture
        self.audio_capture.start()
        
        # Start ASR worker
        self.asr_worker.start()
        
        # Start main processing loop
        self.running = True
        self._process_loop()
    
    def _process_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                # Get transcript
                transcript_event = self.transcript_queue.get(timeout=1.0)
                
                if transcript_event.is_final and transcript_event.text:
                    print(f"\n[ASR] {transcript_event.text}")
                    
                    # Convert to gloss
                    gloss_phrase = self.gloss_mapper.text_to_gloss(
                        transcript_event.text,
                        transcript_event.timestamp
                    )
                    
                    print(f"[GLOSS] {' '.join(gloss_phrase.glosses)}")
                    
                    # Generate SiGML
                    sigml = self.sigml_generator.generate(gloss_phrase)
                    
                    print(f"[SiGML]\n{sigml}\n")
            
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                self.shutdown()
                break
    
    def shutdown(self, timeout: float = 5.0):
        """Graceful shutdown."""
        print("\nShutting down...")
        self.running = False
        
        # Stop audio capture
        self.audio_capture.stop()
        
        # Stop ASR worker
        self.asr_worker.stop()
        self.asr_worker.join(timeout=timeout)
        
        print("✓ Shutdown complete")
```

**Instructions for Copilot**:

- Queue-based pipeline (audio → ASR → NLP → SiGML)
- Graceful shutdown with timeout
- Print output to console (GUI added later)

---

#### File: `main.py`

```python
"""
SignVani entry point.
"""
import argparse
from config.settings import AppConfig
from src.pipeline.orchestrator import PipelineOrchestrator
from src.database.seed_db import seed_database

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='SignVani: Speech to ISL Translator')
    parser.add_argument('--seed-db', action='store_true', help='Seed database with initial glosses')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
    args = parser.parse_args()
    
    # Load configuration
    config = AppConfig()
    
    # Seed database if requested
    if args.seed_db:
        seed_database(config.database.db_path)
        return
    
    # Start pipeline
    orchestrator = PipelineOrchestrator(config)
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        orchestrator.shutdown()

if __name__ == "__main__":
    main()
```

---

## Key Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **End-to-end latency** | <1000ms | Audio input → SiGML output |
| **ASR latency** | <200ms | Vosk processing time |
| **NLP latency** | <15ms | Tokenization → gloss mapping |
| **DB lookup** | <1ms | SQLite query with LRU cache |
| **Memory usage** | <500MB | Peak resident set size |
| **CPU usage** | <80% | Average during inference |
| **Cache hit rate** | >80% | LRU cache effectiveness |

---

## Testing Instructions

### Unit Tests

```bash
pytest tests/unit/ -v --cov=src --cov-report=html
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Performance Benchmarks

```bash
python scripts/benchmark.py
```

---

## RPi4 Deployment

```bash
# Clone repository
git clone <repo>
cd SignVani

# Run deployment script
chmod +x scripts/deploy_rpi.sh
./scripts/deploy_rpi.sh

# Seed database
python3 main.py --seed-db

# Run pipeline
python3 main.py
```

---

## Error Handling Strategy

1. **Audio capture fails**: Log error, attempt restart, fallback to file input
2. **Vosk model not found**: Download automatically via `setup_models.py`
3. **Unknown word**: Fuzzy match → fingerspelling → log for training
4. **Database locked**: Retry with exponential backoff (SQLite timeout)
5. **Queue full**: Drop oldest frames, log warning
6. **Thread deadlock**: Watchdog timer restarts threads after 5s timeout

---

## Optimization Tips for Copilot

1. **Memory**: Always use `__slots__` for data classes
2. **Performance**: Use `numpy` operations, avoid Python loops
3. **Threading**: Use `queue.Queue` for inter-thread communication
4. **Database**: LRU cache for repeated lookups
5. **Audio**: Process in chunks, use float32 for FFT
6. **NLP**: NLTK is lighter than spaCy for this use case
7. **Error handling**: Log and continue, don't crash

---

## Research Foundation

This implementation is based on:

**Dhanjal, A. S., & Singh, W. (2025).** "Multilingual speech to Indian sign language translation using synthetic animation: a resource-efficient approach." *Multimedia Tools and Applications*, Springer.

**Key Insights**:

- HamNoSys encoding: 486 bytes/sign vs 150KB video
- Rule-based grammar preferred over neural networks (limited ISL datasets)
- Offline mandatory for rural India + privacy
- Reported latency: 394.52ms (validates <1000ms target)

---

## Quick Reference: Common Tasks

### Add new gloss to database

```python
from src.database.retriever import GlossRetriever
retriever = GlossRetriever("data/signvani.db")
retriever.add_gloss("NEW-SIGN", "hamnosys_string_here")
```

### Test audio capture

```python
from src.audio.audio_capture import AudioCapture
from config.settings import AudioConfig
import queue

audio_queue = queue.Queue()
capture = AudioCapture(AudioConfig(), audio_queue)
capture.start()
# Speak into microphone
chunk = audio_queue.get()
print(f"Captured {len(chunk.data)} samples")
```

### Benchmark latency

```python
from src.utils.profiler import LatencyProfiler

@LatencyProfiler()
def my_function():
    # Your code here
    pass
```

---

**Document Version**: 1.0 (GitHub Copilot Optimized)  
**Last Updated**: 2025-12-28  
**Status**: Ready for implementation
