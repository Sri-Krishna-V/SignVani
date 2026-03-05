# API Reference

## Audio Subsystem

### `src.audio.audio_capture.AudioCaptureSystem`

The main entry point for audio capture.

* `__init__(output_queue, vad_enabled, noise_filter_enabled)`: Initializes the capture system.
* `start()`: Starts the audio stream.
* `stop()`: Stops the audio stream.

### `src.audio.vad.VoiceActivityDetector`

Detects speech in audio chunks.

* `process_chunk(chunk: AudioChunk) -> bool`: Returns `True` if speech is detected.

### `src.audio.noise_filter.SpectralSubtractor`

Reduces background noise.

* `update_noise_profile(audio_data)`: Learns noise profile from silence.
* `filter(audio_data) -> np.ndarray`: Returns denoised audio.

## ASR Subsystem

### `src.asr.vosk_engine.VoskEngine`

Singleton wrapper for Vosk.

* `process_audio(audio_data: bytes) -> Optional[Dict]`: Processes raw audio bytes.
* `get_final_result() -> Dict`: Flushes the recognizer buffer.

### `src.asr.asr_worker.ASRWorker`

Thread for asynchronous ASR.

* `__init__(input_queue, output_queue)`: Connects audio input to transcript output.
* `run()`: Main loop processing audio chunks.
* `stop()`: Signals the worker to stop.

## Data Classes

### `src.nlp.dataclasses.AudioChunk`

* `data`: `np.ndarray` (float32)
* `sample_rate`: `int`
* `timestamp`: `float`
* `energy`: `float` (property)

### `src.nlp.dataclasses.TranscriptEvent`

* `text`: `str`
* `confidence`: `float`
* `is_final`: `bool`
