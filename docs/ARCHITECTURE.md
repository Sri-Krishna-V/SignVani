# SignVani Architecture

## Overview

SignVani is an offline, edge-computing solution designed to convert spoken English into Indian Sign Language (ISL) visual output. It targets the Raspberry Pi 4 platform and emphasizes low latency and memory efficiency.

## System Data Flow

```mermaid
graph TD
    Mic[Microphone] --> AudioCapture[Audio Capture System]
    AudioCapture -->|Raw Audio| VAD[Voice Activity Detection]
    VAD -->|Speech Segments| NoiseFilter[Spectral Subtraction]
    NoiseFilter -->|Clean Audio| AudioBuffer[Circular Buffer]
    AudioBuffer -->|AudioChunk| AudioQueue[Audio Queue]
    AudioQueue --> ASRWorker[ASR Worker Thread]
    ASRWorker -->|Audio Bytes| VoskEngine[Vosk ASR Engine]
    VoskEngine -->|TranscriptEvent| TranscriptQueue[Transcript Queue]
    TranscriptQueue --> NLP[NLP Engine (Pending)]
    NLP --> DB[Database (Pending)]
    DB --> SiGML[SiGML Generator (Pending)]
    SiGML --> Avatar[Avatar Renderer (Pending)]
```

## Core Subsystems

### 1. Audio Subsystem (`src/audio/`)

Responsible for capturing audio, detecting speech, and reducing noise.

* **`AudioCaptureSystem`**: Manages the PyAudio stream in non-blocking callback mode.
* **`VoiceActivityDetector`**: Uses energy thresholding to distinguish speech from silence.
* **`SpectralSubtractor`**: Performs frequency-domain noise reduction using `scipy.fft`.
* **`CircularAudioBuffer`**: A thread-safe ring buffer to store audio chunks before processing.

### 2. ASR Subsystem (`src/asr/`)

Responsible for converting audio into text.

* **`VoskEngine`**: A singleton wrapper around the Vosk offline ASR library. It manages the model lifecycle and provides thread-safe access to the recognizer.
* **`ASRWorker`**: A background thread that consumes `AudioChunk` objects from the `AudioQueue`, converts them to the format required by Vosk, and pushes `TranscriptEvent` objects to the `TranscriptQueue`.

### 3. Configuration (`config/`)

* **`settings.py`**: Uses frozen dataclasses to define immutable configuration parameters for all subsystems. This ensures consistency and prevents runtime modification of critical settings.

## Data Structures (`src/nlp/dataclasses.py`)

* **`AudioChunk`**: Represents a chunk of audio data. Uses `__slots__` and `float32` for memory efficiency.
* **`TranscriptEvent`**: Represents a recognized text segment.

## Design Principles

* **Offline-First**: No dependency on cloud APIs.
* **Memory Efficiency**: Extensive use of `__slots__`, `float32`, and generators.
* **Thread Safety**: All shared resources (queues, buffers, engines) are thread-safe.
* **Latency Focused**: Processing pipelines are designed to minimize delay.
