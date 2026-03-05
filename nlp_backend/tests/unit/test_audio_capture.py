"""
Unit Tests for Audio Subsystem

Tests for AudioChunk, CircularAudioBuffer, VAD, SpectralSubtractor, and AudioCaptureSystem.
"""

import pytest
import numpy as np
import time
import queue

from src.nlp.dataclasses import AudioChunk
from src.audio.audio_buffer import CircularAudioBuffer
from src.audio.vad import VoiceActivityDetector, auto_calibrate_threshold
from src.audio.noise_filter import SpectralSubtractor
from src.utils.exceptions import AudioError, VADError, NoiseFilterError


class TestAudioChunk:
    """Test AudioChunk data class"""

    def test_create_chunk(self):
        """Test creating AudioChunk"""
        data = np.random.randn(1024).astype(np.float32)
        chunk = AudioChunk(data, sample_rate=16000)

        assert chunk.sample_rate == 16000
        assert chunk.num_samples == 1024
        assert chunk.data.dtype == np.float32

    def test_chunk_duration(self):
        """Test duration calculation"""
        data = np.zeros(16000, dtype=np.float32)  # 1 second @ 16kHz
        chunk = AudioChunk(data, sample_rate=16000)

        assert abs(chunk.duration - 1.0) < 0.001  # Within 1ms

    def test_chunk_energy(self):
        """Test energy calculation"""
        # Silence
        silence = np.zeros(1024, dtype=np.float32)
        chunk_silence = AudioChunk(silence, sample_rate=16000)
        assert chunk_silence.energy < 0.0001

        # Loud signal
        loud = np.ones(1024, dtype=np.float32)
        chunk_loud = AudioChunk(loud, sample_rate=16000)
        assert chunk_loud.energy > 0.9

    def test_float32_conversion(self):
        """Test automatic conversion to float32"""
        data_int16 = np.random.randint(-32768, 32767, 1024, dtype=np.int16)
        chunk = AudioChunk(data_int16, sample_rate=16000)

        assert chunk.data.dtype == np.float32


class TestCircularAudioBuffer:
    """Test CircularAudioBuffer"""

    def test_create_buffer(self):
        """Test buffer creation"""
        buffer = CircularAudioBuffer(max_size=10)
        assert buffer.max_size == 10
        assert buffer.is_empty()
        assert not buffer.is_full()

    def test_put_get(self):
        """Test putting and getting chunks"""
        buffer = CircularAudioBuffer(max_size=5)

        # Add chunks
        for i in range(3):
            chunk = AudioChunk(np.random.randn(1024).astype(np.float32), 16000)
            success = buffer.put(chunk)
            assert success

        assert buffer.size() == 3

        # Retrieve chunks
        chunk = buffer.get_nowait()
        assert chunk is not None
        assert buffer.size() == 2

    def test_overflow_handling(self):
        """Test automatic overflow handling"""
        buffer = CircularAudioBuffer(max_size=3)

        # Fill buffer
        for i in range(3):
            chunk = AudioChunk(np.random.randn(1024).astype(np.float32), 16000)
            success = buffer.put(chunk)
            assert success

        assert buffer.is_full()

        # Overflow (oldest should be dropped)
        chunk = AudioChunk(np.random.randn(1024).astype(np.float32), 16000)
        success = buffer.put(chunk)
        assert not success  # Indicates overflow
        assert buffer.total_dropped == 1

    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading

        buffer = CircularAudioBuffer(max_size=100)
        num_chunks = 50

        def producer():
            for i in range(num_chunks):
                chunk = AudioChunk(np.random.randn(512).astype(np.float32), 16000)
                buffer.put(chunk)
                time.sleep(0.001)

        def consumer():
            retrieved = 0
            while retrieved < num_chunks:
                chunk = buffer.get(timeout=2.0)
                if chunk:
                    retrieved += 1
                else:
                    break
            return retrieved

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        # All chunks should have been processed
        assert buffer.total_received == num_chunks

    def test_stats(self):
        """Test buffer statistics"""
        buffer = CircularAudioBuffer(max_size=5)

        for i in range(3):
            chunk = AudioChunk(np.random.randn(1024).astype(np.float32), 16000)
            buffer.put(chunk)

        stats = buffer.get_stats()
        assert stats['current_size'] == 3
        assert stats['max_size'] == 5
        assert stats['total_received'] == 3
        assert stats['utilization'] == 0.6


class TestVoiceActivityDetector:
    """Test VoiceActivityDetector"""

    def test_create_vad(self):
        """Test VAD creation"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)
        assert vad.threshold == 0.02
        assert not vad.is_speech()

    def test_silence_detection(self):
        """Test detection of silence"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)

        # Feed low-energy chunks (silence)
        for i in range(5):
            silence = np.random.randn(1024).astype(np.float32) * 0.001
            chunk = AudioChunk(silence, sample_rate=16000)
            is_speech = vad.process_chunk(chunk)

        assert not is_speech  # Should detect silence

    def test_speech_detection(self):
        """Test detection of speech"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)

        # Feed high-energy chunks (speech)
        for i in range(5):
            speech = np.random.randn(1024).astype(np.float32) * 0.1
            chunk = AudioChunk(speech, sample_rate=16000)
            is_speech = vad.process_chunk(chunk)

        assert is_speech  # Should detect speech

    def test_consecutive_frame_requirement(self):
        """Test that VAD requires consecutive frames"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)

        # Alternate between silence and speech (should not trigger)
        for i in range(6):
            if i % 2 == 0:
                audio = np.random.randn(1024).astype(np.float32) * 0.001
            else:
                audio = np.random.randn(1024).astype(np.float32) * 0.1

            chunk = AudioChunk(audio, sample_rate=16000)
            vad.process_chunk(chunk)

        # Should not detect sustained speech
        assert not vad.is_speech()

    def test_auto_calibration(self):
        """Test automatic threshold calibration"""
        # Generate samples with varying energy
        samples = []
        for _ in range(20):
            amplitude = np.random.uniform(0.001, 0.1)
            audio = np.random.randn(1024).astype(np.float32) * amplitude
            samples.append(audio)

        # Calculate threshold at 50th percentile
        threshold = auto_calibrate_threshold(samples, percentile=50)
        assert threshold > 0
        assert threshold < 1.0

    def test_threshold_setter(self):
        """Test threshold update"""
        vad = VoiceActivityDetector(threshold=0.02)
        vad.threshold = 0.05
        assert vad.threshold == 0.05

        with pytest.raises(VADError):
            vad.threshold = -0.01  # Invalid threshold


class TestSpectralSubtractor:
    """Test SpectralSubtractor"""

    def test_create_filter(self):
        """Test filter creation"""
        filter = SpectralSubtractor(fft_size=1024, alpha=2.0, beta=0.01)
        assert not filter.is_calibrated

    def test_noise_calibration(self):
        """Test noise profile learning"""
        filter = SpectralSubtractor(fft_size=1024)

        # Feed noise samples
        for i in range(5):
            noise = np.random.randn(1024).astype(np.float32) * 0.01
            filter.update_noise_profile(noise)

        assert filter.is_calibrated
        assert filter.noise_samples_count >= 3

    def test_filtering(self):
        """Test noise filtering"""
        filter = SpectralSubtractor(fft_size=1024, alpha=2.0, beta=0.01)

        # Calibrate with noise
        for i in range(5):
            noise = np.random.randn(1024).astype(np.float32) * 0.02
            filter.update_noise_profile(noise)

        # Create noisy speech (sine wave + noise)
        t = np.linspace(0, 1, 1024, endpoint=False, dtype=np.float32)
        speech = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.1
        noise = np.random.randn(1024).astype(np.float32) * 0.02
        noisy = speech + noise

        # Filter
        filtered = filter.filter(noisy)

        # Check that filtering occurred
        assert len(filtered) == len(noisy)
        assert filtered.dtype == np.float32

    @pytest.mark.timeout(0.1)
    def test_filter_performance(self):
        """Test that filtering is fast (<100ms for 1s of audio)"""
        filter = SpectralSubtractor(fft_size=1024)

        # Calibrate
        for i in range(5):
            noise = np.random.randn(1024).astype(np.float32) * 0.01
            filter.update_noise_profile(noise)

        # Filter 1 second of audio
        audio = np.random.randn(16000).astype(np.float32) * 0.05

        start = time.perf_counter()
        filtered = filter.filter(audio)
        duration = time.perf_counter() - start

        # Should be much faster than real-time
        assert duration < 0.1  # 100ms for 1s of audio

    def test_invalid_parameters(self):
        """Test invalid parameter handling"""
        with pytest.raises(NoiseFilterError):
            SpectralSubtractor(fft_size=100)  # Not power of 2

        with pytest.raises(NoiseFilterError):
            SpectralSubtractor(alpha=-1.0)  # Negative alpha

        with pytest.raises(NoiseFilterError):
            SpectralSubtractor(beta=1.5)  # Beta >= 1


class TestIntegration:
    """Integration tests for audio subsystem"""

    def test_vad_with_buffer(self):
        """Test VAD integrated with buffer"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)
        buffer = CircularAudioBuffer(max_size=10)

        # Generate mixed audio (silence → speech → silence)
        amplitudes = [0.001, 0.001, 0.001, 0.1, 0.1, 0.1, 0.001, 0.001]

        for amp in amplitudes:
            audio = np.random.randn(1024).astype(np.float32) * amp
            chunk = AudioChunk(audio, sample_rate=16000)

            is_speech = vad.process_chunk(chunk)

            # Only add speech chunks to buffer
            if is_speech:
                buffer.put(chunk)

        # Buffer should contain only speech chunks
        # (after VAD stabilizes, 3 high-energy chunks)
        assert buffer.size() >= 2  # At least some speech detected

    def test_filter_with_vad(self):
        """Test noise filter integrated with VAD"""
        vad = VoiceActivityDetector(threshold=0.02, frame_count=3)
        filter = SpectralSubtractor(fft_size=1024)

        # Phase 1: Calibration with silence
        for i in range(5):
            noise = np.random.randn(1024).astype(np.float32) * 0.01
            chunk = AudioChunk(noise, sample_rate=16000)
            is_speech = vad.process_chunk(chunk)

            if not is_speech:
                filter.update_noise_profile(chunk.data)

        assert filter.is_calibrated

        # Phase 2: Filter speech
        speech = np.random.randn(1024).astype(np.float32) * 0.1
        chunk = AudioChunk(speech, sample_rate=16000)
        is_speech = vad.process_chunk(chunk)

        if is_speech:
            filtered_chunk = filter.filter_chunk(chunk, is_speech=True)
            assert filtered_chunk.num_samples == chunk.num_samples


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
