-- src/db/schema.sql
DROP TABLE IF EXISTS context_keywords;
DROP TABLE IF EXISTS phonetic_aliases;
DROP TABLE IF EXISTS memory_stats;
DROP TABLE IF EXISTS global_word_stats;
DROP TABLE IF EXISTS system_stats;
DROP TABLE IF EXISTS entities;

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    canonical_form TEXT NOT NULL UNIQUE,
    entity_type TEXT DEFAULT NULL,
    primary_metaphone TEXT NOT NULL,
    secondary_metaphone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracks the numerator for our Inverse Document Frequency (IDF)
CREATE TABLE IF NOT EXISTS system_stats (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_entities INTEGER DEFAULT 0
);

-- Tracks the denominator: how many unique entities share this keyword
CREATE TABLE IF NOT EXISTS global_word_stats (
    keyword TEXT PRIMARY KEY,
    entity_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS phonetic_aliases (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    primary_metaphone TEXT NOT NULL,
    secondary_metaphone TEXT,
    UNIQUE(entity_id, alias)
);

CREATE TABLE IF NOT EXISTS context_keywords (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL REFERENCES global_word_stats(keyword) ON DELETE CASCADE,
    local_frequency INTEGER DEFAULT 1,
    UNIQUE(entity_id, keyword)
);

CREATE TABLE IF NOT EXISTS memory_stats (
    entity_id TEXT PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    observations_count INTEGER DEFAULT 1,
    successful_interventions INTEGER DEFAULT 0,
    rejected_interventions INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.5
);

CREATE INDEX IF NOT EXISTS idx_entities_metaphone ON entities(primary_metaphone);
CREATE INDEX IF NOT EXISTS idx_aliases_metaphone ON phonetic_aliases(primary_metaphone);
CREATE INDEX IF NOT EXISTS idx_context_keyword ON context_keywords(keyword);
