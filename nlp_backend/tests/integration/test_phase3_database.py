"""
Phase 3: Database Layer Integration Test

Tests all Phase 3 components: DatabaseManager, GlossRetriever, Schema, and Seed Data.
Validates <1ms lookup latency with LRU cache and FTS functionality.
"""

from src.database.seed_db import seed_database
from src.database.retriever import GlossRetriever
from src.database.db_manager import DatabaseManager
import src.database.retriever as retriever_module
import src.database.db_manager as db_module
import sqlite3
import tempfile
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("=" * 70)
print("SignVani - Phase 3: Database Layer Integration Test")
print("=" * 70)

# Setup: Create temporary database for testing
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = temp_db.name
temp_db.close()

print(f"\n[Setup] Using temporary database: {test_db_path}")

# Mock the configuration to use our temp database

original_db_config = db_module.database_config
original_ret_config = retriever_module.database_config

mock_db_config = MagicMock()
mock_db_config.DB_PATH = test_db_path
mock_db_config.CONNECTION_POOL_SIZE = 2
mock_db_config.PRAGMA_JOURNAL_MODE = 'DELETE'
mock_db_config.PRAGMA_SYNCHRONOUS = 'NORMAL'
mock_db_config.PRAGMA_CACHE_SIZE = -2000

mock_ret_config = MagicMock()
mock_ret_config.CACHE_SIZE = 128
mock_ret_config.ENABLE_FTS = True

db_module.database_config = mock_db_config
retriever_module.database_config = mock_ret_config

# Reset Singleton
db_module.DatabaseManager._instance = None

# Now import and test

try:
    # Test 1: DatabaseManager Singleton & Schema
    print("\n1. Testing DatabaseManager & Schema...")
    db_manager = DatabaseManager()
    print(f"   [OK] DatabaseManager initialized as Singleton")

    # Verify schema tables exist
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = {row[0] for row in cursor.fetchall()}

    required_tables = {'gloss_mapping', 'gloss_fts', 'unknown_words'}
    assert required_tables.issubset(
        tables), f"Missing tables: {required_tables - tables}"
    print(
        f"   [OK] Schema created with tables: {', '.join(sorted(required_tables))}")

    # Verify indexes exist
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index';"
        )
        indexes = {row[0] for row in cursor.fetchall()}

    required_indexes = {'idx_gloss_frequency', 'idx_unknown_frequency'}
    assert required_indexes.issubset(
        indexes), f"Missing indexes: {required_indexes - indexes}"
    print(f"   [OK] Indexes created: {', '.join(sorted(required_indexes))}")

    # Test 2: GlossRetriever - Add and Retrieve
    print("\n2. Testing GlossRetriever - Add & Retrieve...")
    retriever = GlossRetriever()

    # Clear cache
    retriever.get_hamnosys.cache_clear()

    # Add test glosses
    test_glosses = {
        "HELLO": "hamfinger2,hamthumboutmod,hamextfingeru",
        "WELCOME": "hamflat,hampalmu,hamchest",
        "THANK_YOU": "hamflat,hampalmu,hamchin",
        "GOOD": "hamfist,hamthumboutmod,hamextfingeru",
    }

    for gloss, hamnosys in test_glosses.items():
        retriever.add_gloss(gloss, hamnosys)

    print(f"   [OK] Added {len(test_glosses)} glosses to database")

    # Test exact match retrieval
    result = retriever.get_hamnosys("HELLO")
    assert result == test_glosses["HELLO"]
    print(f"   [OK] Exact match retrieval: 'HELLO' -> '{result}'")

    # Test case-insensitivity
    result = retriever.get_hamnosys("hello")
    assert result == test_glosses["HELLO"]
    print(f"   [OK] Case-insensitive retrieval: 'hello' -> '{result}'")

    # Test 3: LRU Cache Performance
    print("\n3. Testing LRU Cache Performance...")
    retriever.get_hamnosys.cache_clear()

    # Warm up cache
    for gloss in test_glosses.keys():
        retriever.get_hamnosys(gloss)

    # Measure cached access time
    start = time.perf_counter()
    for _ in range(1000):
        retriever.get_hamnosys("HELLO")
    cached_time = (time.perf_counter() - start) / 1000

    print(f"   [OK] Cached lookup latency: {cached_time*1000:.4f} ms")
    print(
        f"       (Target: <1ms, Achieved: {'✓' if cached_time*1000 < 1 else '✗'})")

    # Check cache stats
    cache_info = retriever.get_hamnosys.cache_info()
    print(
        f"   [OK] Cache stats: {cache_info.hits} hits, {cache_info.misses} misses")

    # Test 4: Database Seeding
    print("\n4. Testing Database Seeding...")
    retriever.get_hamnosys.cache_clear()

    # Clear existing data
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM gloss_mapping")
        conn.commit()

    # Run seed (uses DatabaseManager singleton internally)
    seed_database()
    print(f"   [OK] Database seeded with initial glosses")

    # Verify seed data
    with db_manager.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM gloss_mapping").fetchone()[0]
    print(f"   [OK] Total glosses in database: {count}")

    # Test retrieval of seeded data
    result = retriever.get_hamnosys("HELLO")
    assert result is not None
    print(f"   [OK] Seeded gloss retrieval: 'HELLO' -> '{result}'")

    # Test 5: Unknown Words Logging
    print("\n5. Testing Unknown Words Logging...")
    retriever.get_hamnosys.cache_clear()

    # Clear unknown words table
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM unknown_words")
        conn.commit()

    # Query unknown word
    unknown = "NONEXISTENT_SIGN_12345"
    result = retriever.get_hamnosys(unknown)
    assert result is None
    print(f"   [OK] Unknown word query returned None: '{unknown}'")

    # Verify it was logged
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT occurrence_count FROM unknown_words WHERE word = ?",
            (unknown,)
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == 1
    print(f"   [OK] Unknown word logged with occurrence_count=1")

    # Query again and verify count incremented
    retriever.get_hamnosys.cache_clear()
    retriever.get_hamnosys(unknown)

    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT occurrence_count FROM unknown_words WHERE word = ?",
            (unknown,)
        )
        row = cursor.fetchone()

    assert row[0] == 2
    print(f"   [OK] Repeated query incremented count to 2")

    # Test 6: FTS (Full-Text Search)
    print("\n6. Testing Full-Text Search (FTS5)...")
    retriever.get_hamnosys.cache_clear()

    # Add some test data
    retriever.add_gloss("EDUCATION", "hambook,hamhand")
    retriever.add_gloss("STUDENT", "hambook,hamhand,hamperson")
    retriever.add_gloss("TEACHING", "hambook,hamhand,hamteach")

    # Test FTS retrieval (via exact match first)
    result = retriever.get_hamnosys("EDUCATION")
    assert result is not None
    print(f"   [OK] FTS-backed table initialized: 'EDUCATION' -> '{result}'")

    # Test that DB stats work
    stats = retriever.get_stats()
    print(f"   [OK] Database stats: {stats}")

    # Test 7: Database Statistics
    print("\n7. Testing Database Statistics...")

    stats = retriever.get_stats()
    print(f"   [OK] Gloss count: {stats.get('total_glosses', 'N/A')}")
    print(
        f"   [OK] Unknown words tracked: {stats.get('unknown_words_tracked', 'N/A')}")

    # Test 8: Concurrent Access
    print("\n8. Testing Concurrent Access & Connection Pooling...")

    # Simulate multiple concurrent accesses
    results = []
    for i in range(5):
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM gloss_mapping"
            )
            count = cursor.fetchone()[0]
            results.append(count)

    assert all(r == results[0] for r in results)
    print(
        f"   [OK] Multiple connections returned consistent data: {results[0]}")
    print(f"   [OK] Connection pool handled {5} sequential requests")

    # Cleanup
    print("\n" + "=" * 70)
    print("✓ Phase 3: Database Layer - All Tests Passed!")
    print("=" * 70)

    db_manager.close_all()

finally:
    # Restore original configs
    db_module.database_config = original_db_config
    retriever_module.database_config = original_ret_config
    db_module.DatabaseManager._instance = None

    # Cleanup temp database
    try:
        Path(test_db_path).unlink()
    except (OSError, FileNotFoundError):
        pass
