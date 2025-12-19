"""
SignVani Database Initialization Script
Creates database tables and loads seed data
"""
from signvani_service.database import DatabaseManager
from config import settings
import sys
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")


def init_database():
    """Initialize database and load seed data"""
    logger.info(f"Initializing database at {settings.DATABASE_PATH}")

    # Create database manager (this creates tables)
    db = DatabaseManager(str(settings.DATABASE_PATH))

    # Load seed data
    if settings.SEED_DATA_PATH.exists():
        logger.info(f"Loading seed data from {settings.SEED_DATA_PATH}")
        count = db.seed_from_json(settings.SEED_DATA_PATH)
        logger.info(f"Successfully loaded {count} mappings")
    else:
        logger.warning(f"Seed data file not found: {settings.SEED_DATA_PATH}")

    # Print stats
    stats = db.get_stats()
    logger.info(
        f"Database initialized with {stats['total_mappings']} mappings")


if __name__ == "__main__":
    init_database()
