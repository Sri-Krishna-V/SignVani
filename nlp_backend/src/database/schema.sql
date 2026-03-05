-- Gloss-to-HamNoSys mapping table
CREATE TABLE IF NOT EXISTS gloss_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    english_gloss TEXT NOT NULL UNIQUE,
    hamnosys_string TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    frequency INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by gloss
CREATE INDEX IF NOT EXISTS idx_gloss_frequency 
ON gloss_mapping(english_gloss, frequency DESC);

-- Full-text search for fuzzy matching (unknown words)
CREATE VIRTUAL TABLE IF NOT EXISTS gloss_fts 
USING fts5(english_gloss, hamnosys_string, content=gloss_mapping);

-- Trigger to keep FTS table in sync
CREATE TRIGGER IF NOT EXISTS gloss_fts_sync_insert 
AFTER INSERT ON gloss_mapping BEGIN
    INSERT INTO gloss_fts(rowid, english_gloss, hamnosys_string)
    VALUES (new.id, new.english_gloss, new.hamnosys_string);
END;

CREATE TRIGGER IF NOT EXISTS gloss_fts_sync_update 
AFTER UPDATE ON gloss_mapping BEGIN
    UPDATE gloss_fts 
    SET english_gloss = new.english_gloss,
        hamnosys_string = new.hamnosys_string
    WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS gloss_fts_sync_delete
AFTER DELETE ON gloss_mapping BEGIN
    INSERT INTO gloss_fts(gloss_fts, rowid, english_gloss, hamnosys_string)
    VALUES('delete', old.id, old.english_gloss, old.hamnosys_string);
END;

-- Table to log unknown words for future training
CREATE TABLE IF NOT EXISTS unknown_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    occurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unknown_frequency 
ON unknown_words(occurrence_count DESC);
