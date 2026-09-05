# src/db/client.py

import sqlite3
import json
import math
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(".kivi/memory.db")

class KiviDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.row_factory = sqlite3.Row
        
        # Inject standard math.log so we can compute TF-IDF entirely in SQL
        self.conn.create_function("LOG", 1, math.log)

    def reset(self, schema_path: Path):
        """Wipes the database and applies the schema."""
        with open(schema_path, "r") as f:
            schema = f.read()
        self.conn.executescript(schema)
        # Initialize the baseline system stats row
        self.conn.execute("INSERT OR IGNORE INTO system_stats (id, total_entities) VALUES (1, 0)")

    def learn_entity(self, canonical: str, alias: str, entity_type: Optional[str], primary_meta: str, sec_meta: str, context: List[str], alias_pri, alias_sec):
        """Upserts an entity, its phonetic alias, and local/global context frequencies."""
        entity_id = canonical.lower().replace(" ", "_")
        
        with self.conn:
            # 1. Insert or update entity
            self.conn.execute("""
                INSERT INTO entities (id, canonical_form, entity_type, primary_metaphone, secondary_metaphone)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(canonical_form) DO UPDATE SET 
                updated_at = CURRENT_TIMESTAMP,
                entity_type = COALESCE(?, entity_type)
            """, (entity_id, canonical, entity_type, primary_meta, sec_meta, entity_type))
            
            # 2. Maintain accurate total entity count for IDF calculations
            self.conn.execute("""
                INSERT INTO system_stats (id, total_entities) 
                VALUES (1, (SELECT COUNT(*) FROM entities))
                ON CONFLICT(id) DO UPDATE SET total_entities = (SELECT COUNT(*) FROM entities)
            """)
            
            # 3. Insert or update alias
            self.conn.execute("""
                INSERT OR IGNORE INTO phonetic_aliases (id, entity_id, alias, primary_metaphone, secondary_metaphone)
                VALUES (?, ?, ?, ?, ?)
            """, (f"{entity_id}_{alias}", entity_id, alias, alias_pri, alias_sec))
            
            # 4. Update memory stats (Asymptotic curve)
            cursor = self.conn.execute("SELECT observations_count FROM memory_stats WHERE entity_id = ?", (entity_id,))
            row = cursor.fetchone()
            new_count = row['observations_count'] + 1 if row else 1
            new_confidence = 1.0 - (1.0 - 0.7) * math.exp(-0.3 * (new_count - 1))
            
            self.conn.execute("""
                INSERT INTO memory_stats (entity_id, observations_count, confidence_score)
                VALUES (?, ?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET 
                observations_count = ?,
                confidence_score = ?
            """, (entity_id, new_count, new_confidence, new_count, new_confidence))
            
            # 5. Process Context Keywords for TF-IDF tracking
            for kw in context:
                # Ensure the keyword exists in the global tracker
                self.conn.execute("""
                    INSERT OR IGNORE INTO global_word_stats (keyword, entity_count) 
                    VALUES (?, 0)
                """, (kw,))
                
                # Check if this keyword is new to this specific entity
                cursor = self.conn.execute("SELECT 1 FROM context_keywords WHERE entity_id = ? AND keyword = ?", (entity_id, kw))
                is_new_link = cursor.fetchone() is None

                # Upsert the local Term Frequency
                self.conn.execute("""
                    INSERT INTO context_keywords (id, entity_id, keyword, local_frequency)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(entity_id, keyword) DO UPDATE SET local_frequency = local_frequency + 1
                """, (f"{entity_id}_{kw}", entity_id, kw))

                # If this is the first time this entity used this word, increment the global document frequency
                if is_new_link:
                    self.conn.execute("""
                        UPDATE global_word_stats 
                        SET entity_count = entity_count + 1 
                        WHERE keyword = ?
                    """, (kw,))
                    
        return entity_id

    def get_candidates(self, primary_meta: str, secondary_meta: str) -> List[Dict]:
        """Retrieves matching candidates, filtering contexts directly via calculated TF-IDF scores."""
        if not primary_meta:
            return []
            
        # Smoothed TF-IDF formula to prevent division by zero or negative logs:
        # TF = local_frequency
        # IDF = LOG( (total_entities + 2.0) / (entity_count + 1.0) )
        # Filter threshold: >= 0.2 strips out widely used generic words.
        
        query = """
            WITH tfidf_keywords AS (
                SELECT 
                    c.entity_id, 
                    c.keyword,
                    (c.local_frequency * LOG( (s.total_entities + 2.0) / (g.entity_count + 1.0) )) AS weight
                FROM context_keywords c
                JOIN global_word_stats g ON c.keyword = g.keyword
                JOIN system_stats s ON s.id = 1
                WHERE (c.local_frequency * LOG( (s.total_entities + 2.0) / (g.entity_count + 1.0) )) >= 0.2
            )
            SELECT 
                e.canonical_form, 
                e.id, 
                e.entity_type,
                m.confidence_score,
                GROUP_CONCAT(DISTINCT tk.keyword) as keywords,
                GROUP_CONCAT(DISTINCT a.alias) as aliases
            FROM entities e
            JOIN memory_stats m ON e.id = m.entity_id
            LEFT JOIN phonetic_aliases a ON e.id = a.entity_id
            LEFT JOIN tfidf_keywords tk ON e.id = tk.entity_id
            WHERE 
                e.primary_metaphone = ? OR e.secondary_metaphone = ?
                OR a.primary_metaphone = ? OR a.secondary_metaphone = ?
            GROUP BY e.id
            HAVING m.confidence_score >= 0.3
        """
        cursor = self.conn.execute(query, (primary_meta, secondary_meta, primary_meta, secondary_meta))
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["keywords"] = d["keywords"].split(",") if d["keywords"] else []
            d["aliases"] = d["aliases"].split(",") if d["aliases"] else []
            results.append(d)
        return results

    def inspect_entities(self, entity_name: Optional[str] = None) -> List[Dict]:
        """Retrieves stored memory states including their dynamic TF-IDF weights."""
        query = """
            WITH tfidf_keywords AS (
                SELECT 
                    c.entity_id, 
                    c.keyword,
                    (c.local_frequency * LOG( (s.total_entities + 2.0) / (g.entity_count + 1.0) )) AS weight
                FROM context_keywords c
                JOIN global_word_stats g ON c.keyword = g.keyword
                JOIN system_stats s ON s.id = 1
            )
            SELECT 
                e.id,
                e.canonical_form,
                e.entity_type,
                e.primary_metaphone,
                e.secondary_metaphone,
                m.observations_count,
                m.confidence_score,
                GROUP_CONCAT(DISTINCT a.alias) as aliases,
                -- Use a distinct separator to split keyword and weight safely
                GROUP_CONCAT(DISTINCT tk.keyword || ':' || ROUND(tk.weight, 3)) as context_weights
            FROM entities e
            LEFT JOIN memory_stats m ON e.id = m.entity_id
            LEFT JOIN phonetic_aliases a ON e.id = a.entity_id
            LEFT JOIN tfidf_keywords tk ON e.id = tk.entity_id
        """
        params = []
        if entity_name:
            query += " WHERE LOWER(e.canonical_form) = LOWER(?)"
            params.append(entity_name)

        query += " GROUP BY e.id ORDER BY m.confidence_score DESC;"

        cursor = self.conn.execute(query, tuple(params))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            # Parse the concatenated string into a clean dictionary
            context_dict = {}
            if r["context_weights"]:
                for pair in r["context_weights"].split(","):
                    kw, weight = pair.split(":")
                    context_dict[kw] = float(weight)

            # Sort the dictionary by weight descending so the strongest triggers are first
            sorted_context = dict(sorted(context_dict.items(), key=lambda item: item[1], reverse=True))

            results.append({
                "canonical_form": r["canonical_form"],
                "entity_type": r["entity_type"],
                "primary_metaphone": r["primary_metaphone"],
                "secondary_metaphone": r["secondary_metaphone"],
                "aliases": r["aliases"].split(",") if r["aliases"] else [],
                "context_weights": sorted_context,
                "confidence_score": round(r["confidence_score"] or 0.0, 2),
                "observations": r["observations_count"] or 0
            })
        return results
