"""Database module - SQLite connection management and gloss retrieval."""

from src.database.db_manager import DatabaseManager
from src.database.retriever import GlossRetriever

__all__ = ['DatabaseManager', 'GlossRetriever']
