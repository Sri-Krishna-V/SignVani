"""
Gloss Retriever

Handles efficient retrieval of HamNoSys strings for ISL glosses.
Uses LRU caching and Full-Text Search (FTS) for performance and fuzzy matching.
"""

import logging
import sqlite3
from functools import lru_cache
from typing import Optional

from config.settings import DatabaseConfig
from src.database.db_manager import DatabaseManager
from src.utils.exceptions import QueryError

database_config = DatabaseConfig()

logger = logging.getLogger(__name__)


class GlossRetriever:
    """
    Retrieves HamNoSys notation for ISL glosses.
    Optimized with LRU cache and FTS5 fuzzy search.
    """

    def __init__(self):
        self.db_manager = DatabaseManager()

    @lru_cache(maxsize=database_config.CACHE_SIZE)
    def get_hamnosys(self, gloss: str) -> Optional[str]:
        """
        Retrieve HamNoSys string for a given gloss.

        Strategy:
        1. Check in-memory LRU cache (handled by decorator)
        2. Exact match in database
        3. Fuzzy match (FTS5) - if enabled

        Args:
            gloss: The ISL gloss to look up (e.g., "HELLO")

        Returns:
            HamNoSys string if found, None otherwise.
        """
        gloss = gloss.upper().strip()

        try:
            with self.db_manager.get_connection() as conn:
                # 1. Exact match
                cursor = conn.execute(
                    "SELECT hamnosys_string FROM gloss_mapping WHERE english_gloss = ?",
                    (gloss,)
                )
                row = cursor.fetchone()
                if row:
                    # Update frequency on cache miss (since we are here)
                    self._update_frequency(conn, gloss)
                    return row['hamnosys_string']

                # 2. Fuzzy match (if enabled)
                if database_config.ENABLE_FTS:
                    # Simple FTS query - looks for similar words
                    # Note: FTS syntax can be complex, here we use simple prefix/token matching
                    # For true fuzzy (levenshtein), we might need a custom function or spellfix1
                    # But standard FTS5 MATCH is a good start for partials
                    try:
                        cursor = conn.execute(
                            "SELECT hamnosys_string, english_gloss FROM gloss_fts WHERE english_gloss MATCH ? ORDER BY rank LIMIT 1",
                            (gloss,)
                        )
                        row = cursor.fetchone()
                        if row:
                            logger.info(
                                f"Fuzzy match: '{gloss}' -> '{row['english_gloss']}'")
                            return row['hamnosys_string']
                    except sqlite3.OperationalError:
                        # FTS query might fail on special characters
                        pass

                # 3. Log unknown word
                self._log_unknown_word(conn, gloss)
                return None

        except sqlite3.Error as e:
            logger.error(f"Database query failed for gloss '{gloss}': {e}")
            raise QueryError(f"Failed to retrieve gloss '{gloss}': {e}")

    def _update_frequency(self, conn: sqlite3.Connection, gloss: str):
        """Update usage frequency for cache optimization."""
        try:
            conn.execute(
                "UPDATE gloss_mapping SET frequency = frequency + 1 WHERE english_gloss = ?",
                (gloss,)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"Failed to update frequency for '{gloss}': {e}")

    def _log_unknown_word(self, conn: sqlite3.Connection, word: str):
        """Log unknown word for future training."""
        try:
            conn.execute(
                """
                INSERT INTO unknown_words (word, occurrence_count) 
                VALUES (?, 1) 
                ON CONFLICT(word) DO UPDATE SET 
                occurrence_count = occurrence_count + 1,
                last_seen = CURRENT_TIMESTAMP
                """,
                (word,)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"Failed to log unknown word '{word}': {e}")

    def add_gloss(self, gloss: str, hamnosys: str, category: str = 'user_defined'):
        """
        Add a new gloss to the database.
        Useful for runtime updates or learning.
        """
        gloss = gloss.upper().strip()
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO gloss_mapping (english_gloss, hamnosys_string, category)
                    VALUES (?, ?, ?)
                    ON CONFLICT(english_gloss) DO UPDATE SET
                    hamnosys_string = excluded.hamnosys_string,
                    updated_at = CURRENT_TIMESTAMP
                    """,
                    (gloss, hamnosys, category)
                )
                conn.commit()
                # Clear cache to ensure consistency
                self.get_hamnosys.cache_clear()
                logger.info(f"Added/Updated gloss: {gloss}")
        except sqlite3.Error as e:
            logger.error(f"Failed to add gloss '{gloss}': {e}")
            raise QueryError(f"Failed to add gloss: {e}")

    def get_stats(self) -> dict:
        """Get database statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                total_glosses = conn.execute(
                    "SELECT COUNT(*) FROM gloss_mapping").fetchone()[0]
                unknown_words = conn.execute(
                    "SELECT COUNT(*) FROM unknown_words").fetchone()[0]
                return {
                    "total_glosses": total_glosses,
                    "unknown_words_tracked": unknown_words
                }
        except sqlite3.Error:
            return {}
