"""
SignVani Database Manager
SQLite database operations for gloss-to-HamNoSys mappings
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for SignVani"""

    def __init__(self, db_path: str):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and tables exist"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            self._create_tables(conn)
            self._create_indexes(conn)
            self._optimize_sqlite(conn)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS gloss_hamnosys_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gloss_word TEXT NOT NULL,
                hamnosys_xml TEXT NOT NULL,
                english_word TEXT,
                confidence_score REAL DEFAULT 1.0,
                region TEXT DEFAULT 'Mumbai',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS conversion_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                gloss_output TEXT NOT NULL,
                processing_time REAL,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS missing_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gloss_word TEXT NOT NULL UNIQUE,
                frequency INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance"""
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_gloss_word 
                ON gloss_hamnosys_mappings(gloss_word);
            
            CREATE INDEX IF NOT EXISTS idx_english_word 
                ON gloss_hamnosys_mappings(english_word);
            
            CREATE INDEX IF NOT EXISTS idx_region 
                ON gloss_hamnosys_mappings(region);
            
            CREATE INDEX IF NOT EXISTS idx_missing_word 
                ON missing_words(gloss_word);
        """)

    def _optimize_sqlite(self, conn: sqlite3.Connection):
        """Apply SQLite optimizations for Raspberry Pi"""
        conn.executescript("""
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA cache_size = -2000;
            PRAGMA temp_store = MEMORY;
            PRAGMA mmap_size = 30000000000;
        """)

    # ============================================
    # HamNoSys Mapping Operations
    # ============================================

    def get_hamnosys(self, gloss_word: str, region: Optional[str] = None) -> Optional[Dict]:
        """
        Retrieve HamNoSys mapping for a gloss word

        Args:
            gloss_word: ISL gloss word (uppercase)
            region: Regional variant (Mumbai, Delhi, etc.)

        Returns:
            Dictionary with mapping data or None
        """
        query = """
            SELECT id, gloss_word, hamnosys_xml, english_word, 
                   confidence_score, region, created_at
            FROM gloss_hamnosys_mappings
            WHERE gloss_word = ?
        """

        params = [gloss_word.upper()]

        if region:
            query += " AND region = ?"
            params.append(region)

        query += " ORDER BY confidence_score DESC LIMIT 1"

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()

            if row:
                return dict(row)

            # Log missing word
            self._log_missing_word(gloss_word)
            return None

    def get_hamnosys_batch(self, gloss_words: List[str], region: Optional[str] = None) -> Dict[str, Dict]:
        """
        Retrieve HamNoSys mappings for multiple gloss words

        Args:
            gloss_words: List of ISL gloss words
            region: Regional variant

        Returns:
            Dictionary mapping gloss_word to mapping data
        """
        if not gloss_words:
            return {}

        placeholders = ','.join('?' * len(gloss_words))
        query = f"""
            SELECT id, gloss_word, hamnosys_xml, english_word, 
                   confidence_score, region, created_at
            FROM gloss_hamnosys_mappings
            WHERE gloss_word IN ({placeholders})
        """

        params = [word.upper() for word in gloss_words]

        if region:
            query += " AND region = ?"
            params.append(region)

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            result = {row['gloss_word']: dict(row) for row in rows}

            # Log missing words
            found_words = set(result.keys())
            missing_words = set(w.upper() for w in gloss_words) - found_words
            for word in missing_words:
                self._log_missing_word(word)

            return result

    def add_hamnosys_mapping(
        self,
        gloss_word: str,
        hamnosys_xml: str,
        english_word: Optional[str] = None,
        confidence_score: float = 1.0,
        region: str = "Mumbai"
    ) -> int:
        """
        Add new HamNoSys mapping to database

        Returns:
            ID of inserted row
        """
        query = """
            INSERT INTO gloss_hamnosys_mappings 
            (gloss_word, hamnosys_xml, english_word, confidence_score, region)
            VALUES (?, ?, ?, ?, ?)
        """

        with self.get_connection() as conn:
            cursor = conn.execute(
                query,
                (gloss_word.upper(), hamnosys_xml,
                 english_word, confidence_score, region)
            )
            return cursor.lastrowid

    def update_hamnosys_mapping(self, mapping_id: int, hamnosys_xml: str, confidence_score: float = 1.0):
        """Update existing HamNoSys mapping"""
        query = """
            UPDATE gloss_hamnosys_mappings
            SET hamnosys_xml = ?, confidence_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        with self.get_connection() as conn:
            conn.execute(query, (hamnosys_xml, confidence_score, mapping_id))

    def search_mappings(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search for mappings by gloss or English word"""
        query = """
            SELECT id, gloss_word, hamnosys_xml, english_word, confidence_score, region
            FROM gloss_hamnosys_mappings
            WHERE gloss_word LIKE ? OR english_word LIKE ?
            ORDER BY confidence_score DESC
            LIMIT ?
        """

        pattern = f"%{search_term}%"

        with self.get_connection() as conn:
            cursor = conn.execute(query, (pattern, pattern, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============================================
    # Logging Operations
    # ============================================

    def log_conversion(
        self,
        input_text: str,
        gloss_output: str,
        processing_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log a conversion operation"""
        query = """
            INSERT INTO conversion_logs 
            (input_text, gloss_output, processing_time, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        """

        with self.get_connection() as conn:
            conn.execute(query, (input_text, gloss_output,
                         processing_time, success, error_message))

    def _log_missing_word(self, gloss_word: str):
        """Log a missing gloss word for future database expansion"""
        query = """
            INSERT INTO missing_words (gloss_word, frequency, last_seen)
            VALUES (?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(gloss_word) DO UPDATE SET
                frequency = frequency + 1,
                last_seen = CURRENT_TIMESTAMP
        """

        with self.get_connection() as conn:
            conn.execute(query, (gloss_word.upper(),))

    def get_missing_words(self, limit: int = 50) -> List[Tuple[str, int]]:
        """Get most frequently missing words"""
        query = """
            SELECT gloss_word, frequency
            FROM missing_words
            ORDER BY frequency DESC
            LIMIT ?
        """

        with self.get_connection() as conn:
            cursor = conn.execute(query, (limit,))
            return [(row['gloss_word'], row['frequency']) for row in cursor.fetchall()]

    # ============================================
    # Statistics
    # ============================================

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            # Total mappings
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM gloss_hamnosys_mappings")
            total_mappings = cursor.fetchone()['count']

            # Regions
            cursor = conn.execute(
                "SELECT DISTINCT region FROM gloss_hamnosys_mappings")
            regions = [row['region'] for row in cursor.fetchall()]

            # Most common words
            cursor = conn.execute("""
                SELECT gloss_word, COUNT(*) as count
                FROM gloss_hamnosys_mappings
                GROUP BY gloss_word
                ORDER BY count DESC
                LIMIT 10
            """)
            most_common = [dict(row) for row in cursor.fetchall()]

            # Database size
            db_size_mb = self.db_path.stat().st_size / \
                (1024 * 1024) if self.db_path.exists() else 0

            return {
                'total_mappings': total_mappings,
                'regions': regions,
                'most_common_words': most_common,
                'database_size_mb': round(db_size_mb, 2)
            }

    # ============================================
    # Seed Data Operations
    # ============================================

    def seed_from_json(self, json_path: Path) -> int:
        """
        Seed database from JSON file

        Returns:
            Number of mappings added
        """
        if not json_path.exists():
            logger.warning(f"Seed file not found: {json_path}")
            return 0

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        with self.get_connection() as conn:
            for item in data:
                try:
                    conn.execute("""
                        INSERT INTO gloss_hamnosys_mappings 
                        (gloss_word, hamnosys_xml, english_word, confidence_score, region)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        item['gloss_word'].upper(),
                        item['hamnosys_xml'],
                        item.get('english_word'),
                        item.get('confidence_score', 1.0),
                        item.get('region', 'Mumbai')
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Skipping duplicate: {item['gloss_word']}")

        logger.info(f"Seeded {count} mappings from {json_path}")
        return count

    def clear_mappings(self):
        """Clear all mappings (use with caution)"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM gloss_hamnosys_mappings")
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='gloss_hamnosys_mappings'")

        logger.warning("All gloss-HamNoSys mappings have been cleared")


if __name__ == "__main__":
    # Test database operations
    logging.basicConfig(level=logging.INFO)

    db = DatabaseManager("../data/signvani.db")

    # Get stats
    stats = db.get_stats()
    print("Database Statistics:")
    print(json.dumps(stats, indent=2))
