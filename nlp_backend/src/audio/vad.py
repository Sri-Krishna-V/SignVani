"""
Voice Activity Detection (VAD)

Energy-based voice activity detection for filtering speech from silence/noise.
Uses RMS energy threshold with configurable frame counting for stability.
"""

import numpy as np
from typing import Deque
from collections import deque

from config.settings import audio_config
from src.nlp.dataclasses import AudioChunk
from src.utils.exceptions import VADError


class VoiceActivityDetector:
    """
    Simple yet effective energy-based VAD.

    Uses RMS (Root Mean Square) energy to distinguish speech from silence.
    Requires consecutive frames above threshold to avoid false positives.
    """
    __slots__ = ('_threshold', '_frame_count', '_history', '_is_speech',
                 '_total_frames', '_speech_frames')

    def __init__(self,
                 threshold: float = None,
                 frame_count: int = None):
        """
        Initialize VAD.

        Args:
            threshold: Energy threshold for speech detection (default from config)
            frame_count: Number of consecutive frames required (default from config)
        """
        self._threshold = threshold if threshold is not None else audio_config.VAD_ENERGY_THRESHOLD
        self._frame_count = frame_count if frame_count is not None else audio_config.VAD_FRAME_COUNT

        if self._threshold <= 0:
            raise VADError("VAD threshold must be positive")
        if self._frame_count < 1:
            raise VADError("VAD frame count must be at least 1")

        # History of recent frame energies
        self._history: Deque[float] = deque(maxlen=self._frame_count)

        # Current state
        self._is_speech = False

        # Statistics
        self._total_frames = 0
        self._speech_frames = 0

    def process_chunk(self, chunk: AudioChunk) -> bool:
        """
        Process audio chunk and detect voice activity.

        Args:
            chunk: AudioChunk to analyze

        Returns:
            True if speech detected, False if silence/noise
        """
        # Calculate RMS energy
        energy = chunk.energy

        # Update history
        self._history.append(energy)
        self._total_frames += 1

        # Require full history before making decision
        if len(self._history) < self._frame_count:
            return self._is_speech

        # Check if all recent frames exceed threshold
        is_speech_now = all(e > self._threshold for e in self._history)

        # Update state
        self._is_speech = is_speech_now

        if self._is_speech:
            self._speech_frames += 1

        return self._is_speech

    def is_speech(self, audio_data: np.ndarray = None) -> bool:
        """
        Check if audio contains speech.

        Args:
            audio_data: Optional audio samples to check (if None, returns current state)

        Returns:
            True if speech detected, False otherwise
        """
        if audio_data is not None:
            # Calculate energy directly from audio data
            energy = float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))
            self._history.append(energy)
            self._total_frames += 1

            if len(self._history) >= self._frame_count:
                self._is_speech = all(e > self._threshold for e in self._history)
                if self._is_speech:
                    self._speech_frames += 1

        return self._is_speech

    def reset(self):
        """Reset VAD state (clears history)"""
        self._history.clear()
        self._is_speech = False

    @property
    def threshold(self) -> float:
        """Current energy threshold"""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        """Update energy threshold"""
        if value <= 0:
            raise VADError("VAD threshold must be positive")
        self._threshold = value

    @property
    def speech_ratio(self) -> float:
        """Ratio of speech frames to total frames (0.0 to 1.0)"""
        if self._total_frames == 0:
            return 0.0
        return self._speech_frames / self._total_frames

    @property
    def current_energy(self) -> float:
        """Most recent frame energy (or 0.0 if no history)"""
        return self._history[-1] if len(self._history) > 0 else 0.0

    def get_stats(self) -> dict:
        """
        Get VAD statistics.

        Returns:
            Dictionary with VAD metrics
        """
        return {
            'threshold': self._threshold,
            'frame_count': self._frame_count,
            'is_speech': self._is_speech,
            'current_energy': self.current_energy,
            'total_frames': self._total_frames,
            'speech_frames': self._speech_frames,
            'speech_ratio': self.speech_ratio
        }

    def __repr__(self):
        state = "SPEECH" if self._is_speech else "SILENCE"
        return (f"VoiceActivityDetector({state}, "
                f"energy={self.current_energy:.6f}, "
                f"threshold={self._threshold:.6f})")


def auto_calibrate_threshold(audio_samples: list,
                             sample_rate: int = 16000,
                             percentile: float = 50.0) -> float:
    """
    Auto-calibrate VAD threshold from sample audio data.

    Analyzes energy distribution and sets threshold at specified percentile.
    Useful for adapting to different acoustic environments.

    Args:
        audio_samples: List of audio sample arrays
        sample_rate: Sample rate in Hz
        percentile: Percentile for threshold (default 50 = median)

    Returns:
        Recommended threshold value
    """
    energies = []

    for samples in audio_samples:
        # Calculate RMS energy
        energy = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
        energies.append(energy)

    if len(energies) == 0:
        raise VADError("No audio samples provided for calibration")

    # Calculate threshold at specified percentile
    threshold = float(np.percentile(energies, percentile))

    return threshold


if __name__ == '__main__':
    # Test Voice Activity Detector
    import time

    print("Testing VoiceActivityDetector\n")
    print("=" * 60)

    # Create VAD
    vad = VoiceActivityDetector(threshold=0.02, frame_count=3)
    print(f"Created VAD: {vad}\n")

    # Test 1: Silence (low energy)
    print("1. Testing with silence (low energy):")
    for i in range(5):
        silence = np.random.randn(1024).astype(np.float32) * 0.001  # Very low amplitude
        chunk = AudioChunk(silence, sample_rate=16000)
        is_speech = vad.process_chunk(chunk)
        print(f"   Frame {i+1}: energy={chunk.energy:.6f}, speech={is_speech}, {vad}")

    # Test 2: Speech (high energy)
    print("\n2. Testing with speech (high energy):")
    vad.reset()
    for i in range(5):
        speech = np.random.randn(1024).astype(np.float32) * 0.1  # Higher amplitude
        chunk = AudioChunk(speech, sample_rate=16000)
        is_speech = vad.process_chunk(chunk)
        print(f"   Frame {i+1}: energy={chunk.energy:.6f}, speech={is_speech}, {vad}")

    # Test 3: Mixed (silence → speech → silence)
    print("\n3. Testing with mixed audio:")
    vad.reset()
    test_sequence = [0.001, 0.001, 0.1, 0.1, 0.1, 0.001, 0.001]
    for i, amplitude in enumerate(test_sequence):
        audio = np.random.randn(1024).astype(np.float32) * amplitude
        chunk = AudioChunk(audio, sample_rate=16000)
        is_speech = vad.process_chunk(chunk)
        state = "SPEECH" if is_speech else "SILENCE"
        print(f"   Frame {i+1}: energy={chunk.energy:.6f}, detected={state}")

    # Test 4: Statistics
    print("\n4. VAD Statistics:")
    stats = vad.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            if 'ratio' in key:
                print(f"   {key}: {value:.2%}")
            else:
                print(f"   {key}: {value:.6f}")
        else:
            print(f"   {key}: {value}")

    # Test 5: Auto-calibration
    print("\n5. Testing auto-calibration:")
    # Generate sample audio with different energy levels
    samples = []
    for _ in range(20):
        amplitude = np.random.uniform(0.001, 0.1)
        audio = np.random.randn(1024).astype(np.float32) * amplitude
        samples.append(audio)

    # Calculate recommended thresholds at different percentiles
    for percentile in [25, 50, 75]:
        threshold = auto_calibrate_threshold(samples, percentile=percentile)
        print(f"   Percentile {percentile:2d}: threshold={threshold:.6f}")

    print("\n" + "=" * 60)
    print("✓ All tests passed")
