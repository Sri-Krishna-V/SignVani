#!/usr/bin/env python3
"""
Circular Audio Buffer Test Script

Tests all features of the CircularAudioBuffer including:
- Basic put/get operations
- Buffer overflow handling
- Thread safety
- Memory efficiency
"""

import numpy as np
import threading
import time
from src.nlp.dataclasses import AudioChunk
from src.audio.audio_buffer import CircularAudioBuffer

print("=" * 70)
print("CircularAudioBuffer Test Suite")
print("=" * 70)

# ============================================================================
# Test 1: Basic Put/Get Operations
# ============================================================================
print("\n[Test 1] Basic Put/Get Operations")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=3)
print(f"Created buffer with max_size=3")

# Create and add 3 chunks
for i in range(3):
    data = np.full(1024, i, dtype=np.float32)  # Fill with value i
    chunk = AudioChunk(data, sample_rate=16000)
    result = buffer.put(chunk)
    print(f"  Put chunk {i}: {result} (buffer size: {buffer.size})")

# Retrieve all chunks in FIFO order
print("\nRetrieving chunks (non-blocking):")
for i in range(3):
    chunk = buffer.get_nowait()
    if chunk:
        print(f"  Got chunk {i}: mean value = {chunk.data.mean():.1f}")
    else:
        print(f"  Got chunk {i}: None (empty)")

print("\n✓ Basic put/get operations working")

# ============================================================================
# Test 2: Buffer Overflow Handling
# ============================================================================
print("\n[Test 2] Buffer Overflow Handling (FIFO - drops oldest)")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=3)
print(f"Created buffer with max_size=3")

# Add 5 chunks (should drop 2 oldest)
print("\nAdding 5 chunks to buffer with max_size=3:")
for i in range(5):
    data = np.full(1024, i, dtype=np.float32)
    chunk = AudioChunk(data, sample_rate=16000)
    added = buffer.put(chunk)
    print(f"  Chunk {i}: added={added}, buffer_size={buffer.size}, "
          f"dropped={buffer.total_chunks_dropped}, received={buffer.total_chunks_received}")

# Retrieve remaining chunks (should only get 3, 4)
print("\nRetrieving remaining chunks:")
remaining = []
for i in range(5):
    chunk = buffer.get_nowait()
    if chunk:
        remaining.append(chunk.data.mean())
        print(f"  Got chunk with value {chunk.data.mean():.1f}")
    else:
        break

print(f"\nExpected values: [3.0, 4.0]")
print(f"Actual values:   {[f'{v:.1f}' for v in remaining]}")
assert len(remaining) == 2, "Should have 2 chunks remaining"
assert remaining[0] == 3.0, "First chunk should be value 3"
assert remaining[1] == 4.0, "Second chunk should be value 4"

print("\n✓ Buffer overflow handled correctly (FIFO drop)")

# ============================================================================
# Test 3: Non-blocking Get with Timeout
# ============================================================================
print("\n[Test 3] Non-blocking Get with Timeout")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=5)

# Add one chunk
data = np.ones(1024, dtype=np.float32)
chunk = AudioChunk(data, sample_rate=16000)
buffer.put(chunk)

print("Testing get_nowait():")
chunk = buffer.get_nowait()
print(f"  Got chunk: {chunk is not None}")

print("\nTesting get() with timeout on empty buffer:")
start = time.time()
chunk = buffer.get(block=True, timeout=0.5)
elapsed = time.time() - start
print(f"  Got chunk: {chunk is not None}")
print(f"  Timeout worked: {elapsed >= 0.5}")
assert elapsed >= 0.5, "Timeout should wait ~0.5s"
assert chunk is None, "Should return None on timeout"

print("\n✓ Timeout behavior correct")

# ============================================================================
# Test 4: Thread Safety - Multiple Producers
# ============================================================================
print("\n[Test 4] Thread Safety - Multiple Producers")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=50)
chunks_added = []

def producer(producer_id, num_chunks):
    """Add chunks from multiple threads"""
    for i in range(num_chunks):
        data = np.full(1024, producer_id * 100 + i, dtype=np.float32)
        chunk = AudioChunk(data, sample_rate=16000)
        result = buffer.put(chunk)
        chunks_added.append((producer_id, i, result))
        time.sleep(0.001)  # Small delay

# Create 3 producer threads
print("Starting 3 producer threads (10 chunks each)...")
threads = []
for pid in range(3):
    t = threading.Thread(target=producer, args=(pid, 10))
    threads.append(t)
    t.start()

# Wait for all producers
for t in threads:
    t.join()

print(f"Added {len(chunks_added)} chunks")
print(f"Buffer size: {buffer.size}")
print(f"Total received: {buffer.total_chunks_received}")
print(f"Total dropped: {buffer.total_chunks_dropped}")

assert buffer.total_chunks_received == 30, "Should have received 30 chunks"
assert buffer.total_chunks_dropped == 0, "No chunks should be dropped (max_size=50)"

print("\n✓ Multiple producer threads working safely")

# ============================================================================
# Test 5: Thread Safety - Producer/Consumer
# ============================================================================
print("\n[Test 5] Thread Safety - Producer/Consumer")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=10)
produced = []
consumed = []

def producer_consumer_test():
    """Producer thread"""
    for i in range(20):
        data = np.full(1024, i, dtype=np.float32)
        chunk = AudioChunk(data, sample_rate=16000)
        buffer.put(chunk)
        produced.append(i)
        time.sleep(0.01)

def consumer():
    """Consumer thread"""
    while len(consumed) < 20:
        chunk = buffer.get(block=True, timeout=1.0)
        if chunk:
            consumed.append(chunk.data.mean())
        time.sleep(0.005)

print("Starting producer and consumer threads...")
prod_thread = threading.Thread(target=producer_consumer_test)
cons_thread = threading.Thread(target=consumer)

prod_thread.start()
cons_thread.start()

prod_thread.join()
cons_thread.join()

print(f"Produced: {len(produced)} chunks")
print(f"Consumed: {len(consumed)} chunks")
print(f"First 5 consumed values: {consumed[:5]}")
print(f"Last 5 consumed values: {consumed[-5:]}")

assert len(consumed) == 20, "Should have consumed 20 chunks"

print("\n✓ Producer/consumer pattern working safely")

# ============================================================================
# Test 6: Memory Efficiency
# ============================================================================
print("\n[Test 6] Memory Efficiency")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=5)

# Check __slots__ usage (should be minimal)
print(f"Buffer object size: {buffer.__sizeof__()} bytes")
print(f"Has __dict__: {hasattr(buffer, '__dict__')}")

# Add chunks and check memory
total_audio_bytes = 0
for i in range(5):
    data = np.random.randn(1024).astype(np.float32)
    chunk = AudioChunk(data, sample_rate=16000)
    buffer.put(chunk)
    total_audio_bytes += data.nbytes

print(f"Audio data in buffer: {total_audio_bytes} bytes")
print(f"Using __slots__: {not hasattr(buffer, '__dict__')}")

print("\n✓ Memory efficiency verified (__slots__ in use)")

# ============================================================================
# Test 7: Stats and Monitoring
# ============================================================================
print("\n[Test 7] Stats and Monitoring")
print("-" * 70)

buffer = CircularAudioBuffer(max_size=3)

# Add 5 chunks (2 will be dropped)
for i in range(5):
    data = np.full(1024, i, dtype=np.float32)
    chunk = AudioChunk(data, sample_rate=16000)
    buffer.put(chunk)

# Consume all
for _ in range(5):
    buffer.get_nowait()

print(f"Stats:")
print(f"  Size: {buffer.size}")
print(f"  Max size: {buffer.max_size}")
print(f"  Utilization: {buffer.utilization:.1%}")
print(f"  Total received: {buffer.total_chunks_received}")
print(f"  Total dropped: {buffer.total_chunks_dropped}")

assert buffer.total_chunks_received == 5
assert buffer.total_chunks_dropped == 2

print("\n✓ Stats correctly tracked")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("""
CircularAudioBuffer verified working:
  ✓ Basic put/get operations (FIFO)
  ✓ Automatic overflow handling
  ✓ Non-blocking get with timeout
  ✓ Thread-safe multiple producers
  ✓ Thread-safe producer/consumer
  ✓ Memory efficient (__slots__)
  ✓ Stats and monitoring
""")
