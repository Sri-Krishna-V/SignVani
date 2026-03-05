"""
Circular Audio Buffer

Thread-safe circular buffer for audio data with automatic overflow handling.
Uses __slots__ for memory efficiency on embedded systems.
"""

import threading
from collections import deque
from typing import Optional
import numpy as np

from src.nlp.dataclasses import AudioChunk
from src.utils.exceptions import AudioError


class CircularAudioBuffer:
    """
    Thread-safe circular buffer for AudioChunk objects.

    Automatically handles overflow by dropping oldest chunks (FIFO).
    Optimized for low-latency audio streaming on embedded systems.
    """
    __slots__ = ('_buffer', '_max_size', '_lock', '_total_chunks_received',
                 '_total_chunks_dropped', '_is_active')

    def __init__(self, max_size: int = 10):
        """
        Initialize circular buffer.

        Args:
            max_size: Maximum number of AudioChunk objects to store
        """
        if max_size < 1:
            raise AudioError("Buffer size must be at least 1")

        self._buffer = deque(maxlen=max_size)
        self._max_size = max_size
        self._lock = threading.Lock()
        self._total_chunks_received = 0
        self._total_chunks_dropped = 0
        self._is_active = True

    def put(self, chunk: AudioChunk) -> bool:
        """
        Add audio chunk to buffer (thread-safe).

        If buffer is full, oldest chunk is automatically dropped.

        Args:
            chunk: AudioChunk to add

        Returns:
            True if added, False if dropped due to buffer full
        """
        if not self._is_active:
            return False

        with self._lock:
            was_full = len(self._buffer) >= self._max_size
            self._buffer.append(chunk)
            self._total_chunks_received += 1

            if was_full:
                self._total_chunks_dropped += 1
                return False

            return True

    def get(self, block: bool = True, timeout: float = None) -> Optional[AudioChunk]:
        """
        Get oldest audio chunk from buffer (thread-safe).

        Args:
            block: If True, wait for chunk to be available
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            AudioChunk or None if timeout/empty
        """
        if block:
            # Blocking mode with timeout
            import time
            start_time = time.time()

            while self._is_active:
                with self._lock:
                    if len(self._buffer) > 0:
                        return self._buffer.popleft()

                # Check timeout
                if timeout is not None and (time.time() - start_time) > timeout:
                    return None

                # Small sleep to avoid busy waiting
                time.sleep(0.001)  # 1ms

            return None
        else:
            # Non-blocking mode
            with self._lock:
                if len(self._buffer) > 0:
                    return self._buffer.popleft()
                return None

    def get_nowait(self) -> Optional[AudioChunk]:
        """Get chunk without blocking (alias for get(block=False))"""
        return self.get(block=False)

    def clear(self):
        """Clear all chunks from buffer (thread-safe)"""
        with self._lock:
            self._buffer.clear()

    def is_empty(self) -> bool:
        """Check if buffer is empty (thread-safe)"""
        with self._lock:
            return len(self._buffer) == 0

    def is_full(self) -> bool:
        """Check if buffer is full (thread-safe)"""
        with self._lock:
            return len(self._buffer) >= self._max_size

    def size(self) -> int:
        """Get current number of chunks in buffer (thread-safe)"""
        with self._lock:
            return len(self._buffer)

    def stop(self):
        """Stop accepting new chunks and signal waiting threads"""
        self._is_active = False

    @property
    def max_size(self) -> int:
        """Maximum buffer capacity"""
        return self._max_size

    @property
    def utilization(self) -> float:
        """Buffer utilization as percentage (0.0 to 1.0)"""
        with self._lock:
            return len(self._buffer) / self._max_size

    @property
    def total_received(self) -> int:
        """Total chunks received since creation"""
        return self._total_chunks_received

    @property
    def total_dropped(self) -> int:
        """Total chunks dropped due to overflow"""
        return self._total_chunks_dropped

    @property
    def drop_rate(self) -> float:
        """Percentage of chunks dropped (0.0 to 1.0)"""
        if self._total_chunks_received == 0:
            return 0.0
        return self._total_chunks_dropped / self._total_chunks_received

    def get_stats(self) -> dict:
        """
        Get buffer statistics.

        Returns:
            Dictionary with buffer metrics
        """
        with self._lock:
            return {
                'current_size': len(self._buffer),
                'max_size': self._max_size,
                'utilization': self.utilization,
                'total_received': self._total_chunks_received,
                'total_dropped': self._total_chunks_dropped,
                'drop_rate': self.drop_rate,
                'is_active': self._is_active
            }

    def __repr__(self):
        stats = self.get_stats()
        return (f"CircularAudioBuffer("
                f"size={stats['current_size']}/{stats['max_size']}, "
                f"utilization={stats['utilization']:.1%}, "
                f"dropped={stats['total_dropped']})")


if __name__ == '__main__':
    # Test circular buffer
    import time

    print("Testing CircularAudioBuffer\n")
    print("=" * 60)

    # Create buffer
    buffer = CircularAudioBuffer(max_size=5)
    print(f"Created buffer: {buffer}")

    # Test adding chunks
    print("\n1. Adding chunks to buffer:")
    for i in range(3):
        chunk = AudioChunk(
            data=np.random.randn(1024).astype(np.float32),
            sample_rate=16000
        )
        success = buffer.put(chunk)
        print(f"   Chunk {i+1}: {'Added' if success else 'Dropped'} - {buffer}")

    # Test overflow
    print("\n2. Testing overflow (adding beyond max_size):")
    for i in range(5):
        chunk = AudioChunk(
            data=np.random.randn(1024).astype(np.float32),
            sample_rate=16000
        )
        success = buffer.put(chunk)
        print(f"   Chunk {i+1}: {'Added' if success else 'Dropped'} - {buffer}")

    # Test retrieval
    print("\n3. Retrieving chunks:")
    for i in range(3):
        chunk = buffer.get_nowait()
        if chunk:
            print(f"   Retrieved chunk {i+1}: {chunk}")
        else:
            print(f"   No chunk available")

    # Test statistics
    print("\n4. Buffer Statistics:")
    stats = buffer.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2%}" if 'rate' in key or 'utilization' in key else f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

    # Test threading
    print("\n5. Testing thread safety:")
    def producer(buffer, num_chunks):
        for i in range(num_chunks):
            chunk = AudioChunk(
                data=np.random.randn(512).astype(np.float32),
                sample_rate=16000
            )
            buffer.put(chunk)
            time.sleep(0.01)

    def consumer(buffer, num_chunks):
        retrieved = 0
        while retrieved < num_chunks:
            chunk = buffer.get(timeout=1.0)
            if chunk:
                retrieved += 1
            else:
                break
        return retrieved

    buffer.clear()
    import threading as th

    producer_thread = th.Thread(target=producer, args=(buffer, 10))
    consumer_thread = th.Thread(target=consumer, args=(buffer, 10))

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

    print(f"   Thread test complete: {buffer}")
    print(f"   Final stats: {buffer.get_stats()}")

    print("\n" + "=" * 60)
    print("✓ All tests passed")
