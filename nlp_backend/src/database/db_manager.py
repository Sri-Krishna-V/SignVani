"""
Database Connection Manager

Handles SQLite connection pooling and thread-safe access.
Implements singleton pattern to ensure a single pool instance.
"""

import sqlite3
import queue
import threading
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config.settings import DatabaseConfig
from src.utils.exceptions import ConnectionError, SchemaError, DatabaseError

database_config = DatabaseConfig()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe SQLite connection manager with pooling.
    Singleton pattern ensures unified access to the database.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = database_config.DB_PATH
        self.pool_size = database_config.CONNECTION_POOL_SIZE
        self.pool = queue.Queue(maxsize=self.pool_size)
        self._initialized = True

        # Initialize pool
        try:
            self._initialize_pool()
            logger.info(
                f"Database manager initialized with {self.pool_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new configured SQLite connection."""
        try:
            # check_same_thread=False is required for pooling, but we must ensure
            # only one thread uses the connection at a time (handled by queue)
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=5.0  # Default timeout
            )
            conn.row_factory = sqlite3.Row

            # Apply PRAGMA settings for performance/reliability
            conn.execute(
                f"PRAGMA journal_mode={database_config.PRAGMA_JOURNAL_MODE}")
            conn.execute(
                f"PRAGMA synchronous={database_config.PRAGMA_SYNCHRONOUS}")
            conn.execute(
                f"PRAGMA cache_size={database_config.PRAGMA_CACHE_SIZE}")

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            return conn
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to create database connection: {e}")

    def _initialize_pool(self):
        """Initialize the connection pool and schema."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema first with a temporary connection
        self._init_schema()

        # Fill the pool
        for _ in range(self.pool_size):
            self.pool.put(self._create_connection())

    def _init_schema(self):
        """Initialize database schema from SQL file."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise SchemaError(f"Schema file not found at {schema_path}")

        try:
            # Use a temporary connection for schema initialization
            conn = self._create_connection()
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.close()
        except sqlite3.Error as e:
            raise SchemaError(f"Failed to initialize schema: {e}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection from the pool.
        Context manager ensures connection is returned to pool.

        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT ...")
        """
        conn = None
        try:
            # Wait for a connection to become available
            conn = self.pool.get(timeout=5.0)
            yield conn
        except queue.Empty:
            logger.error("Database connection pool exhausted")
            raise ConnectionError("Database connection pool exhausted")
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in database operation: {e}")
            raise DatabaseError(f"Unexpected error: {e}")
        finally:
            if conn:
                self.pool.put(conn)

    def close_all(self):
        """Close all connections in the pool. Call on application shutdown."""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break
        logger.info("All database connections closed")
