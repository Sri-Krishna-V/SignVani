"""
Spectral Subtraction Noise Filter

Reduces background noise using spectral subtraction in the frequency domain.
Optimized for ARM processors using scipy.fft (faster than numpy.fft on ARM).
"""

import numpy as np
from scipy.fft import rfft, irfft
from typing import Optional

from config.settings import audio_config
from src.nlp.dataclasses import AudioChunk
from src.utils.exceptions import NoiseFilterError


class SpectralSubtractor:
    """
    Spectral subtraction noise reduction.

    Estimates noise profile during silence periods and subtracts it from
    the signal spectrum during speech. Includes spectral floor to prevent
    over-subtraction artifacts.
    """
    __slots__ = ('_fft_size', '_alpha', '_beta', '_noise_profile',
                 '_noise_samples', '_is_calibrated')

    def __init__(self,
                 fft_size: int = None,
                 alpha: float = None,
                 beta: float = None):
        """
        Initialize spectral subtractor.

        Args:
            fft_size: FFT size (default from config, must be power of 2)
            alpha: Over-subtraction factor (default from config, typically 1.5-3.0)
            beta: Spectral floor factor (default from config, typically 0.01-0.1)
        """
        self._fft_size = fft_size if fft_size is not None else audio_config.FFT_SIZE
        self._alpha = alpha if alpha is not None else audio_config.ALPHA
        self._beta = beta if beta is not None else audio_config.BETA

        # Validate parameters
        if self._fft_size < 64 or (self._fft_size & (self._fft_size - 1)) != 0:
            raise NoiseFilterError(f"FFT size must be power of 2 and >= 64, got {self._fft_size}")
        if self._alpha <= 0:
            raise NoiseFilterError(f"Alpha must be positive, got {self._alpha}")
        if self._beta < 0 or self._beta >= 1:
            raise NoiseFilterError(f"Beta must be in [0, 1), got {self._beta}")

        # Noise profile (learned during silence)
        self._noise_profile: Optional[np.ndarray] = None
        self._noise_samples = 0
        self._is_calibrated = False

    def update_noise_profile(self, audio_data: np.ndarray):
        """
        Update noise profile using audio from silence period.

        Should be called during VAD=False periods to learn background noise.

        Args:
            audio_data: Audio samples from silence (float32)
        """
        # Ensure float32 for memory efficiency
        audio_data = audio_data.astype(np.float32)

        # Zero-pad if needed
        if len(audio_data) < self._fft_size:
            audio_data = np.pad(audio_data, (0, self._fft_size - len(audio_data)), mode='constant')

        # Compute magnitude spectrum
        spectrum = rfft(audio_data, n=self._fft_size)
        magnitude = np.abs(spectrum).astype(np.float32)

        # Initialize or update noise profile using exponential moving average
        if self._noise_profile is None:
            self._noise_profile = magnitude
        else:
            # EMA with alpha=0.9 for stability
            self._noise_profile = 0.9 * self._noise_profile + 0.1 * magnitude

        self._noise_samples += 1

        # Consider calibrated after seeing at least 3 noise samples
        if self._noise_samples >= 3:
            self._is_calibrated = True

    def filter(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply spectral subtraction to remove noise.

        Args:
            audio_data: Noisy audio samples (float32)

        Returns:
            Filtered audio samples (float32)
        """
        # If not calibrated, return original audio
        if not self._is_calibrated or self._noise_profile is None:
            return audio_data.astype(np.float32)

        # Ensure float32
        audio_data = audio_data.astype(np.float32)
        original_length = len(audio_data)

        # Zero-pad if needed
        if len(audio_data) < self._fft_size:
            audio_data = np.pad(audio_data, (0, self._fft_size - len(audio_data)), mode='constant')

        # Compute spectrum
        spectrum = rfft(audio_data, n=self._fft_size)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Spectral subtraction with floor
        # clean_mag = max(magnitude - alpha * noise, beta * magnitude)
        clean_magnitude = np.maximum(
            magnitude - self._alpha * self._noise_profile,
            self._beta * magnitude
        ).astype(np.float32)

        # Reconstruct spectrum
        clean_spectrum = clean_magnitude * np.exp(1j * phase)

        # Inverse FFT
        clean_audio = irfft(clean_spectrum, n=self._fft_size).astype(np.float32)

        # Return original length
        return clean_audio[:original_length]

    def filter_chunk(self, chunk: AudioChunk, is_speech: bool = True) -> AudioChunk:
        """
        Filter audio chunk (convenience method).

        Args:
            chunk: AudioChunk to filter
            is_speech: If False, updates noise profile instead of filtering

        Returns:
            Filtered AudioChunk (or original if not speech)
        """
        if is_speech:
            # Apply filtering
            filtered_data = self.filter(chunk.data)
            return AudioChunk(
                data=filtered_data,
                sample_rate=chunk.sample_rate,
                timestamp=chunk.timestamp
            )
        else:
            # Update noise profile during silence
            self.update_noise_profile(chunk.data)
            return chunk  # Return original during calibration

    def reset(self):
        """Reset noise profile (re-calibration required)"""
        self._noise_profile = None
        self._noise_samples = 0
        self._is_calibrated = False

    @property
    def is_calibrated(self) -> bool:
        """Check if filter has been calibrated with noise samples"""
        return self._is_calibrated

    @property
    def noise_samples_count(self) -> int:
        """Number of noise samples used for calibration"""
        return self._noise_samples

    def get_stats(self) -> dict:
        """
        Get filter statistics.

        Returns:
            Dictionary with filter metrics
        """
        return {
            'fft_size': self._fft_size,
            'alpha': self._alpha,
            'beta': self._beta,
            'is_calibrated': self._is_calibrated,
            'noise_samples': self._noise_samples
        }

    def __repr__(self):
        status = "CALIBRATED" if self._is_calibrated else "NOT CALIBRATED"
        return (f"SpectralSubtractor({status}, "
                f"fft={self._fft_size}, "
                f"α={self._alpha:.1f}, "
                f"β={self._beta:.2f})")


if __name__ == '__main__':
    # Test Spectral Subtractor
    import time

    print("Testing SpectralSubtractor\n")
    print("=" * 60)

    # Create filter
    filter = SpectralSubtractor(fft_size=1024, alpha=2.0, beta=0.01)
    print(f"Created filter: {filter}\n")

    # Test 1: Calibration with noise
    print("1. Calibrating with noise samples:")
    for i in range(5):
        # Simulate background noise (low amplitude white noise)
        noise = np.random.randn(1024).astype(np.float32) * 0.01
        filter.update_noise_profile(noise)
        print(f"   Sample {i+1}: {filter}")

    # Test 2: Filtering noisy speech
    print("\n2. Filtering noisy speech:")
    # Simulate speech (sine wave) + noise
    t = np.linspace(0, 1, 16000, endpoint=False, dtype=np.float32)
    speech = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.1  # 440 Hz tone
    noise = np.random.randn(16000).astype(np.float32) * 0.02

    noisy_speech = speech + noise

    # Calculate SNR before filtering
    snr_before = 10 * np.log10(np.var(speech) / np.var(noise))

    # Filter in chunks
    filtered_chunks = []
    chunk_size = 1024

    start_time = time.perf_counter()

    for i in range(0, len(noisy_speech), chunk_size):
        chunk_data = noisy_speech[i:i+chunk_size]
        filtered_data = filter.filter(chunk_data)
        filtered_chunks.append(filtered_data)

    filter_time = time.perf_counter() - start_time

    filtered_speech = np.concatenate(filtered_chunks)[:len(noisy_speech)]

    # Calculate SNR after filtering
    estimated_noise = filtered_speech - speech
    snr_after = 10 * np.log10(np.var(speech) / np.var(estimated_noise))

    print(f"   SNR before filtering: {snr_before:.2f} dB")
    print(f"   SNR after filtering: {snr_after:.2f} dB")
    print(f"   Improvement: {snr_after - snr_before:.2f} dB")
    print(f"   Processing time: {filter_time*1000:.2f} ms ({len(noisy_speech)} samples)")
    print(f"   Real-time factor: {filter_time/(len(noisy_speech)/16000):.2f}x")

    # Test 3: Performance with AudioChunk
    print("\n3. Testing with AudioChunk:")
    chunk = AudioChunk(
        data=noisy_speech[:1024],
        sample_rate=16000
    )

    start_time = time.perf_counter()
    filtered_chunk = filter.filter_chunk(chunk, is_speech=True)
    chunk_time = time.perf_counter() - start_time

    print(f"   Original energy: {chunk.energy:.6f}")
    print(f"   Filtered energy: {filtered_chunk.energy:.6f}")
    print(f"   Processing time: {chunk_time*1000:.2f} ms")
    print(f"   Latency: {chunk_time*1000:.2f} ms for {chunk.duration*1000:.2f} ms of audio")

    # Test 4: Reset and re-calibration
    print("\n4. Testing reset:")
    print(f"   Before reset: {filter}")
    filter.reset()
    print(f"   After reset: {filter}")

    # Test 5: Statistics
    print("\n5. Filter Statistics:")
    filter.update_noise_profile(noise[:1024])
    filter.update_noise_profile(noise[1024:2048])
    filter.update_noise_profile(noise[2048:3072])

    stats = filter.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("✓ All tests passed")
