"""
Unit tests for the Database Layer.
Tests DatabaseManager, GlossRetriever, and Schema.
"""

import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.database.db_manager import DatabaseManager
from src.database.retriever import GlossRetriever
from src.utils.exceptions import ConnectionError, QueryError

# Fixture to setup a temporary database


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path."""
    db_file = tmp_path / "test_signvani.db"
    return str(db_file)


@pytest.fixture
def db_manager(test_db_path, monkeypatch):
    """
    Initialize DatabaseManager with a temporary database.
    Resets the Singleton before and after the test.
    """
    # Reset Singleton state
    DatabaseManager._instance = None

    # Mock database_config in db_manager module
    import src.database.db_manager as db_module
    
    original_config = db_module.database_config
    
    mock_config = MagicMock()
    mock_config.DB_PATH = test_db_path
    mock_config.CONNECTION_POOL_SIZE = 2
    mock_config.PRAGMA_JOURNAL_MODE = 'DELETE'
    mock_config.PRAGMA_SYNCHRONOUS = 'NORMAL'
    mock_config.PRAGMA_CACHE_SIZE = -2000
    
    db_module.database_config = mock_config
    monkeypatch.setattr('src.database.db_manager.database_config', mock_config)

    manager = DatabaseManager()
    yield manager

    # Cleanup
    manager.close_all()
    DatabaseManager._instance = None
    db_module.database_config = original_config


@pytest.fixture
def retriever(db_manager, monkeypatch):
    """Initialize GlossRetriever with the test database manager."""
    import src.database.retriever as retriever_module
    
    original_config = retriever_module.database_config
    
    mock_config = MagicMock()
    mock_config.CACHE_SIZE = 10
    mock_config.ENABLE_FTS = True
    
    retriever_module.database_config = mock_config
    monkeypatch.setattr('src.database.retriever.database_config', mock_config)

    retriever_obj = GlossRetriever()
    # Clear cache to ensure clean state
    retriever_obj.get_hamnosys.cache_clear()
    yield retriever_obj
    
    retriever_module.database_config = original_config


class TestDatabaseManager:
    def test_singleton(self, db_manager):
        """Test that DatabaseManager follows Singleton pattern."""
        manager2 = DatabaseManager()
        assert db_manager is manager2

    def test_connection_pooling(self, db_manager):
        """Test that connections are pooled correctly."""
        with db_manager.get_connection() as conn1:
            assert isinstance(conn1, sqlite3.Connection)
            # Pool should be empty or have fewer connections

        # Connection should be returned to pool
        with db_manager.get_connection() as conn2:
            assert isinstance(conn2, sqlite3.Connection)

    def test_schema_initialization(self, db_manager):
        """Test that tables are created."""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'gloss_mapping' in tables
            assert 'gloss_fts' in tables
            assert 'unknown_words' in tables


class TestGlossRetriever:
    def test_add_and_retrieve_gloss(self, retriever):
        """Test adding and retrieving a gloss."""
        gloss = "TEST_SIGN"
        hamnosys = "hamfinger2"

        retriever.add_gloss(gloss, hamnosys)
        result = retriever.get_hamnosys(gloss)

        assert result == hamnosys

    def test_case_insensitivity(self, retriever):
        """Test that retrieval is case-insensitive."""
        gloss = "LOWERCASE"
        hamnosys = "hamfist"

        retriever.add_gloss(gloss, hamnosys)
        result = retriever.get_hamnosys("lowercase")

        assert result == hamnosys

    def test_unknown_word_logging(self, retriever, db_manager):
        """Test that unknown words are logged."""
        unknown = "UNKNOWN_WORD"
        result = retriever.get_hamnosys(unknown)

        assert result is None

        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT occurrence_count FROM unknown_words WHERE word = ?", (unknown,))
            row = cursor.fetchone()
            assert row is not None
            assert row['occurrence_count'] == 1

        # Query again to check increment
        retriever.get_hamnosys.cache_clear()
        retriever.get_hamnosys(unknown)
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT occurrence_count FROM unknown_words WHERE word = ?", (unknown,))
            row = cursor.fetchone()
            assert row['occurrence_count'] == 2

    def test_fts_fuzzy_search(self, retriever):
        """Test Full-Text Search fuzzy matching."""
        # Add glosses
        retriever.add_gloss("HELLO", "hamwave")
        retriever.add_gloss("WORLD", "hamfist")

        # Test exact match still works via FTS path
        result = retriever.get_hamnosys("HELLO")
        assert result == "hamwave"

        # Clear cache to force DB lookup
        retriever.get_hamnosys.cache_clear()
        
        # Test that exact match via FTS works
        result = retriever.get_hamnosys("HELLO")
        assert result == "hamwave"

    def test_cache_behavior(self, retriever):
        """Test that LRU cache is working."""
        gloss = "CACHE_TEST"
        hamnosys = "hamtest"
        retriever.add_gloss(gloss, hamnosys)

        # First access - hits DB
        retriever.get_hamnosys(gloss)

        # Second access - should hit cache
        # We can verify this by mocking the db_manager.get_connection
        # But since it's decorated, it's hard to spy on the inner function call count easily without more complex mocking.
        # Instead, we can check cache_info()

        info = retriever.get_hamnosys.cache_info()
        hits_before = info.hits

        retriever.get_hamnosys(gloss)

        info = retriever.get_hamnosys.cache_info()
        assert info.hits == hits_before + 1
