"""
Seed Database

Populates the SQLite database with ISL glosses and HamNoSys mappings.
Uses expanded vocabulary from hamnosys_data module (200+ entries).
"""

import logging
from src.database.db_manager import DatabaseManager
from src.database.hamnosys_data import (
    get_all_glosses,
    get_category_for_gloss,
    GREETINGS, PRONOUNS, VERBS, NOUNS, ADJECTIVES, NUMBERS, PREPOSITIONS, COLORS, FINGERSPELLING
)
from src.utils.exceptions import SeedDataError

logger = logging.getLogger(__name__)


def get_glosses_with_categories() -> dict:
    """
    Get all glosses with their categories for database seeding.

    Returns:
        Dict with gloss as key and (hamnosys, category) tuple as value
    """
    result = {}
    all_glosses = get_all_glosses()

    for gloss, hamnosys in all_glosses.items():
        category = get_category_for_gloss(gloss)
        result[gloss] = (hamnosys, category)

    return result


def seed_database(force_update: bool = False):
    """
    Populate the database with gloss mappings from hamnosys_data.

    Args:
        force_update: If True, update existing entries with new HamNoSys data
    """
    db_manager = DatabaseManager()
    glosses_with_categories = get_glosses_with_categories()

    try:
        with db_manager.get_connection() as conn:
            inserted = 0
            updated = 0

            for gloss, (hamnosys, category) in glosses_with_categories.items():
                if force_update:
                    # Upsert: insert or update
                    cursor = conn.execute(
                        """
                        INSERT INTO gloss_mapping (english_gloss, hamnosys_string, category, frequency)
                        VALUES (?, ?, ?, 100)
                        ON CONFLICT(english_gloss) DO UPDATE SET
                            hamnosys_string = excluded.hamnosys_string,
                            category = excluded.category,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (gloss, hamnosys, category)
                    )
                    if cursor.rowcount > 0:
                        # Check if it was insert or update
                        check = conn.execute(
                            "SELECT frequency FROM gloss_mapping WHERE english_gloss = ?",
                            (gloss,)
                        ).fetchone()
                        if check and check[0] == 100:
                            inserted += 1
                        else:
                            updated += 1
                else:
                    # Insert only if not exists
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO gloss_mapping (english_gloss, hamnosys_string, category, frequency)
                        VALUES (?, ?, ?, 100)
                        """,
                        (gloss, hamnosys, category)
                    )
                    if cursor.rowcount > 0:
                        inserted += 1

            conn.commit()

            total = len(glosses_with_categories)
            logger.info(f"Database seeded: {inserted} new, {updated} updated (Total available: {total})")
            print(f"✓ Database seeded: {inserted} new glosses added")
            if updated > 0:
                print(f"✓ {updated} existing glosses updated")
            print(f"  Total glosses available: {total}")

            # Print category breakdown
            print(f"\n  Categories:")
            print(f"    Greetings: {len(GREETINGS)}")
            print(f"    Pronouns: {len(PRONOUNS)}")
            print(f"    Verbs: {len(VERBS)}")
            print(f"    Nouns: {len(NOUNS)}")
            print(f"    Adjectives: {len(ADJECTIVES)}")
            print(f"    Numbers: {len(NUMBERS)}")
            print(f"    Prepositions: {len(PREPOSITIONS)}")
            print(f"    Colors: {len(COLORS)}")
            print(f"    Fingerspelling: {len(FINGERSPELLING)}")

    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        raise SeedDataError(f"Database seeding failed: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed SignVani database with HamNoSys data")
    parser.add_argument('--force', '-f', action='store_true',
                        help="Force update existing entries with new HamNoSys data")
    args = parser.parse_args()

    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    seed_database(force_update=args.force)
