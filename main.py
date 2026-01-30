"""
SignVani - Speech to Indian Sign Language Translator
Entry Point

Optimized for Raspberry Pi 4 deployment.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path (must be done before local imports)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.orchestrator import PipelineOrchestrator
from src.database.seed_db import seed_database
from config.settings import logging_config


def setup_logging(verbose: bool = False):
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

    level = logging.DEBUG if verbose else getattr(logging, logging_config.LOG_LEVEL)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def run_text_mode(text: str, avatar: bool = True):
    """
    Process text directly without audio/ASR.

    Args:
        text: English text to translate
        avatar: Send output to avatar player
    """
    import time
    from src.nlp.gloss_mapper import GlossMapper
    from src.sigml.generator import SiGMLGenerator
    from src.sigml.avatar_player import CWASAPlayer, CWASAPlayerError

    logger = logging.getLogger("SignVani")
    logger.info(f"Text mode: processing '{text}'")

    # Initialize NLP pipeline (includes WordNet warmup)
    print("Loading NLP models...", end=" ", flush=True)
    start = time.time()
    gloss_mapper = GlossMapper(prewarm=True)
    sigml_generator = SiGMLGenerator()
    print(f"done ({time.time()-start:.1f}s)")

    # Process text
    start = time.time()
    gloss_phrase = gloss_mapper.process(text)
    sigml_output = sigml_generator.generate(gloss_phrase)
    process_time = (time.time() - start) * 1000

    # Output results
    print("\n" + "="*60)
    print(f"INPUT:  {text}")
    print(f"GLOSS:  {gloss_phrase.gloss_string}")
    print(f"SiGML:  {len(sigml_output.sigml_xml)} bytes")
    print(f"TIME:   {process_time:.0f}ms")

    if avatar:
        player = CWASAPlayer(auto_launch=False)
        if player.is_player_running():
            try:
                player.send_sigml(sigml_output.sigml_xml)
                print(f"AVATAR: ✓ Sent to CWASA player")
            except CWASAPlayerError as e:
                print(f"AVATAR: ✗ Error: {e}")
        else:
            print(f"AVATAR: ⚠ Player not running")

    print("="*60)

    # Print full SiGML for debugging
    print(f"\nGenerated SiGML:")
    print(sigml_output.sigml_xml)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SignVani: Speech to ISL Translator")
    parser.add_argument('--seed-db', action='store_true',
                        help="Seed the database with HamNoSys glosses")
    parser.add_argument('--force-seed', action='store_true',
                        help="Force update existing glosses during seeding")
    parser.add_argument('--text', '-t', type=str, metavar='TEXT',
                        help="Process text directly (bypass audio/ASR)")
    parser.add_argument('--no-avatar', action='store_true',
                        help="Disable avatar output in text mode")
    parser.add_argument('--verbose', '-v', action='store_true',
                        help="Enable verbose (debug) logging")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger("SignVani")

    # Seed database mode
    if args.seed_db:
        logger.info("Seeding database with HamNoSys data...")
        seed_database(force_update=args.force_seed)
        logger.info("Database seeding complete.")
        return

    # Text processing mode (bypass audio/ASR)
    if args.text:
        run_text_mode(args.text, avatar=not args.no_avatar)
        return

    # Full pipeline mode (audio -> ASR -> NLP -> SiGML)
    logger.info("Initializing SignVani full pipeline...")

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
