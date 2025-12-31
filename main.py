"""
SignVani - Speech to Indian Sign Language Translator
Entry Point

Optimized for Raspberry Pi 4 deployment.
"""

from src.pipeline.orchestrator import PipelineOrchestrator
from src.database.seed_db import seed_database
from config.settings import logging_config
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path (must be done before local imports)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Configure logging based on settings."""
    # Ensure log directory exists
    log_dir = Path(logging_config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler for RPi deployment
    if logging_config.CONSOLE_LOG_ENABLED:
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_dir / 'signvani.log',
                maxBytes=logging_config.MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=logging_config.BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")

    logging.basicConfig(
        level=getattr(logging, logging_config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SignVani: Speech to ISL Translator")
    parser.add_argument('--seed-db', action='store_true',
                        help="Seed the database with initial glosses")
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
