"""
SignVani - Speech to Indian Sign Language Translator
Entry Point
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.settings import logging_config
from src.pipeline.orchestrator import PipelineOrchestrator
from src.database.seed_db import seed_database

def setup_logging():
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, logging_config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Add FileHandler if needed
        ]
    )

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SignVani: Speech to ISL Translator")
    parser.add_argument('--seed-db', action='store_true', help="Seed the database with initial glosses")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("SignVani")

    if args.seed_db:
        logger.info("Seeding database...")
        seed_database()
        logger.info("Database seeded.")
        return

    logger.info("Initializing SignVani...")
    
    try:
        orchestrator = PipelineOrchestrator()
        orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
