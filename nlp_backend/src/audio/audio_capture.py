"""
Audio Capture System

PyAudio-based non-blocking audio capture with integrated VAD and noise reduction.
Feeds processed audio chunks to a queue for downstream ASR processing.
"""

import pyaudio
import numpy as np
import threading
import queue
import time
import logging
from typing import Optional, Callable

from config.settings import audio_config
from src.nlp.dataclasses import AudioChunk
from src.audio.vad import VoiceActivityDetector
from src.audio.noise_filter import SpectralSubtractor
from src.audio.audio_buffer import CircularAudioBuffer
from src.utils.exceptions import AudioCaptureError, AudioStreamError

logger = logging.getLogger(__name__)


class AudioCaptureSystem:
    """
    Complete audio capture system with integrated processing pipeline.

    Pipeline: PyAudio → VAD → Noise Filter → Buffer → Queue
    Runs in callback mode for minimal latency.
    """

    def __init__(self,
                 output_queue: queue.Queue = None,
                 vad_enabled: bool = None,
                 noise_filter_enabled: bool = None,
                 callback: Optional[Callable[[AudioChunk, bool], None]] = None):
        """
        Initialize audio capture system.

        Args:
            output_queue: Queue to push processed AudioChunks (creates one if None)
            vad_enabled: Enable VAD (default from config)
            noise_filter_enabled: Enable noise filtering (default from config)
            callback: Optional callback(chunk, is_speech) called for each chunk
        """
        # Configuration
        self._sample_rate = audio_config.SAMPLE_RATE
        self._channels = audio_config.CHANNELS
        self._frames_per_buffer = audio_config.FRAMES_PER_BUFFER
        self._format = audio_config.FORMAT

        # Output queue
        self._output_queue = output_queue if output_queue is not None else queue.Queue()

        # Processing components
        self._vad_enabled = vad_enabled if vad_enabled is not None else audio_config.VAD_ENABLED
        self._vad = VoiceActivityDetector() if self._vad_enabled else None

        self._filter_enabled = noise_filter_enabled if noise_filter_enabled is not None else audio_config.NOISE_REDUCTION_ENABLED
        self._noise_filter = SpectralSubtractor() if self._filter_enabled else None

        # Callback
        self._callback = callback

        # PyAudio components
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

        # State
        self._is_running = False
        self._is_calibrating = True  # Start in calibration mode
        self._calibration_frames = 0
        self._calibration_target = 10  # Collect 10 frames of noise before speech processing

        # Statistics
        self._total_frames = 0
        self._speech_frames = 0
        self._silence_frames = 0
        self._errors = 0

        # Thread safety
        self._lock = threading.Lock()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio callback for processing audio frames.

        This runs in a separate thread managed by PortAudio.
        Must be fast to avoid buffer overruns (<64ms for 1024 samples @ 16kHz).
        """
        if status:
            self._errors += 1
            # Log error but continue processing
            # print(f"PyAudio status: {status}")

        try:
            # Convert bytes to numpy array (int16 → float32)
            audio_data = np.frombuffer(
                in_data, dtype=np.int16).astype(np.float32)

            # Normalize to [-1.0, 1.0]
            audio_data = audio_data / 32768.0

            # Create AudioChunk
            chunk = AudioChunk(
                data=audio_data,
                sample_rate=self._sample_rate,
                timestamp=time.time()
            )

            # Process chunk
            is_speech = False

            # VAD detection
            if self._vad is not None:
                is_speech = self._vad.process_chunk(chunk)
            else:
                is_speech = True  # Assume speech if VAD disabled

            # Noise filter calibration and processing
            if self._filter_enabled and self._noise_filter is not None:
                if self._is_calibrating:
                    # Collect noise samples during calibration
                    self._noise_filter.update_noise_profile(chunk.data)
                    self._calibration_frames += 1

                    if self._calibration_frames >= self._calibration_target:
                        self._is_calibrating = False

                    # Don't process chunks during calibration
                    chunk_processed = chunk
                else:
                    # Apply noise filter
                    chunk_processed = self._noise_filter.filter_chunk(
                        chunk, is_speech=is_speech)
            else:
                chunk_processed = chunk

            # Update statistics
            with self._lock:
                self._total_frames += 1
                if is_speech:
                    self._speech_frames += 1
                else:
                    self._silence_frames += 1

            # Push to output queue (only if speech or VAD disabled)
            if is_speech or not self._vad_enabled:
                try:
                    self._output_queue.put_nowait(chunk_processed)
                except queue.Full:
                    # Queue full, drop chunk
                    pass

            # Call user callback if provided
            if self._callback is not None:
                try:
                    self._callback(chunk_processed, is_speech)
                except Exception as e:
                    # Log callback errors but don't crash the stream
                    logger.warning(f"Error in audio callback: {e}")

        except Exception as e:
            self._errors += 1
            logger.error(f"Error in audio processing: {e}")

        # Continue stream
        return (None, pyaudio.paContinue)

    def start(self):
        """
        Start audio capture.

        Opens PyAudio stream in callback mode for minimal latency.

        Raises:
            AudioCaptureError: If capture is already running
            AudioStreamError: If no audio device is available or stream fails
        """
        if self._is_running:
            raise AudioCaptureError("Audio capture already running")

        try:
            # Initialize PyAudio
            self._pyaudio = pyaudio.PyAudio()

            # Check for available input devices
            device_count = self._pyaudio.get_device_count()
            input_device_found = False
            available_devices = []

            for i in range(device_count):
                try:
                    device_info = self._pyaudio.get_device_info_by_index(i)
                    if device_info.get('maxInputChannels', 0) > 0:
                        input_device_found = True
                        available_devices.append(
                            f"  [{i}] {device_info.get('name', 'Unknown')}"
                        )
                except (IOError, OSError):
                    continue

            if not input_device_found:
                self._cleanup()
                raise AudioStreamError(
                    "No audio input device found. Please connect a microphone.\n"
                    "Available audio devices: None"
                )

            # Open stream
            self._stream = self._pyaudio.open(
                format=self._format,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._frames_per_buffer,
                stream_callback=self._audio_callback,
                start=False  # Don't start immediately
            )

            # Start stream
            self._stream.start_stream()
            self._is_running = True

        except AudioStreamError:
            raise
        except OSError as e:
            self._cleanup()
            device_list = '\n'.join(
                available_devices) if available_devices else 'None found'
            raise AudioStreamError(
                f"Failed to open audio device: {e}\n"
                f"Available input devices:\n{device_list}"
            )
        except Exception as e:
            self._cleanup()
            raise AudioStreamError(f"Failed to start audio stream: {e}")

    def stop(self):
        """Stop audio capture and cleanup resources"""
        if not self._is_running:
            return

        self._is_running = False
        self._cleanup()

    def _cleanup(self):
        """Cleanup PyAudio resources"""
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
            except (IOError, OSError) as e:
                # Log but continue cleanup
                pass
            self._stream = None

        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except (IOError, OSError) as e:
                # Log but continue cleanup
                pass
            self._pyaudio = None

    def get_chunk(self, timeout: float = None) -> Optional[AudioChunk]:
        """
        Get next processed audio chunk from queue.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            AudioChunk or None if timeout
        """
        try:
            return self._output_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def reset_calibration(self):
        """Reset noise filter calibration"""
        self._is_calibrating = True
        self._calibration_frames = 0
        if self._noise_filter is not None:
            self._noise_filter.reset()

    @property
    def is_running(self) -> bool:
        """Check if capture is running"""
        return self._is_running

    @property
    def is_calibrated(self) -> bool:
        """Check if noise filter is calibrated"""
        if self._filter_enabled and self._noise_filter is not None:
            return self._noise_filter.is_calibrated
        return True  # Always calibrated if filter disabled

    @property
    def queue_size(self) -> int:
        """Current number of chunks in output queue"""
        return self._output_queue.qsize()

    @property
    def speech_ratio(self) -> float:
        """Ratio of speech to total frames (0.0 to 1.0)"""
        with self._lock:
            if self._total_frames == 0:
                return 0.0
            return self._speech_frames / self._total_frames

    def get_stats(self) -> dict:
        """
        Get capture statistics.

        Returns:
            Dictionary with capture metrics
        """
        with self._lock:
            stats = {
                'is_running': self._is_running,
                'is_calibrated': self.is_calibrated,
                'total_frames': self._total_frames,
                'speech_frames': self._speech_frames,
                'silence_frames': self._silence_frames,
                'speech_ratio': self.speech_ratio,
                'queue_size': self.queue_size,
                'errors': self._errors,
                'sample_rate': self._sample_rate,
                'frames_per_buffer': self._frames_per_buffer,
                'vad_enabled': self._vad_enabled,
                'filter_enabled': self._filter_enabled
            }

        # Add VAD stats if enabled
        if self._vad is not None:
            stats['vad'] = self._vad.get_stats()

        # Add filter stats if enabled
        if self._noise_filter is not None:
            stats['noise_filter'] = self._noise_filter.get_stats()

        return stats

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

    def __repr__(self):
        status = "RUNNING" if self._is_running else "STOPPED"
        calibrated = "CALIBRATED" if self.is_calibrated else "CALIBRATING"
        return (f"AudioCaptureSystem({status}, {calibrated}, "
                f"queue={self.queue_size}, "
                f"speech_ratio={self.speech_ratio:.1%})")


if __name__ == '__main__':
    # Test Audio Capture System
    print("Testing AudioCaptureSystem\n")
    print("=" * 60)
    print("Note: This test requires a microphone connected to your system.")
    print("It will capture audio for 3 seconds and display statistics.\n")

    # Create capture system with less verbose callback
    chunk_count = [0]  # Use list for mutable counter in closure

    def monitor_callback(chunk: AudioChunk, is_speech: bool):
        chunk_count[0] += 1
        # Print only every 10th chunk to reduce output
        if chunk_count[0] % 10 == 0:
            state = "SPEECH" if is_speech else "SILENCE"
            energy = chunk.energy
            print(
                f"  [{state:7s}] Energy: {energy:.6f}, Chunks: {chunk_count[0]}")

    try:
        print("1. Starting audio capture...")
        capture = AudioCaptureSystem(
            vad_enabled=True,
            noise_filter_enabled=True,
            callback=monitor_callback
        )

        capture.start()
        print(f"   Status: {capture}")

        print("\n2. Calibrating noise filter (collecting background noise)...")
        print("   (Please remain quiet for 1 second)")
        time.sleep(1)  # Reduced calibration time

        print("\n3. Processing audio (speak into microphone for 2 seconds)...")
        time.sleep(2)  # Reduced capture time

        print("\n4. Stopping capture...")
        capture.stop()

        print("\n5. Statistics Summary:")
        stats = capture.get_stats()

        # Print condensed stats
        print(f"\n   Audio Processing:")
        print(f"   - Total frames: {stats['total_frames']}")
        print(f"   - Speech frames: {stats['speech_frames']}")
        print(f"   - Speech ratio: {stats['speech_ratio']:.1%}")
        print(f"   - Errors: {stats['errors']}")
        print(f"   - Queue size: {stats['queue_size']}")

        if 'vad' in stats:
            print(f"\n   VAD Status:")
            print(f"   - Threshold: {stats['vad']['threshold']:.4f}")
            print(f"   - Current energy: {stats['vad']['current_energy']:.4f}")
            print(f"   - Speech detected: {stats['vad']['is_speech']}")

        if 'noise_filter' in stats:
            print(f"\n   Noise Filter:")
            print(f"   - Calibrated: {stats['noise_filter']['is_calibrated']}")
            print(
                f"   - Noise samples: {stats['noise_filter']['noise_samples']}")

        print("\n" + "=" * 60)
        print("[OK] Test completed successfully")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test stopped by user")
        capture.stop()

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
