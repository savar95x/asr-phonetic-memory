import re
import sys
from pathlib import Path

# Ensure src can be imported when executing from the project root
sys.path.append(str(Path(__file__).parent.parent))
from src.engine.phonetics import get_phonetic_keys

def update_seed():
    sql_path = Path("seeds/default.sql")
    if not sql_path.exists():
        print(f"Error: {sql_path} not found.")
        return

    content = sql_path.read_text(encoding="utf-8")

    # 1. Target the Entities Block
    # Extracts: (id, canonical_form, entity_type, pri, sec)
    def entity_replacer(match):
        row_id, canonical, ent_type = match.group(1), match.group(2), match.group(3)
        pri, sec = get_phonetic_keys(canonical)
        return f"('{row_id}', '{canonical}', '{ent_type}', '{pri}', '{sec}')"

    entities_pattern = re.compile(r"(INSERT INTO entities.*?VALUES\s*)(.*?)(;)", re.DOTALL | re.IGNORECASE)
    
    def process_entities_block(block_match):
        prefix, values, suffix = block_match.groups()
        updated_values = re.sub(
            r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'[^']*',\s*'[^']*'\)", 
            entity_replacer, 
            values
        )
        return prefix + updated_values + suffix

    content = entities_pattern.sub(process_entities_block, content)

    # 2. Target the Phonetic Aliases Block
    # Extracts: (id, entity_id, alias, pri, sec)
    def alias_replacer(match):
        row_id, ent_id, alias = match.group(1), match.group(2), match.group(3)
        pri, sec = get_phonetic_keys(alias)
        return f"('{row_id}', '{ent_id}', '{alias}', '{pri}', '{sec}')"

    aliases_pattern = re.compile(r"(INSERT INTO phonetic_aliases.*?VALUES\s*)(.*?)(;)", re.DOTALL | re.IGNORECASE)

    def process_aliases_block(block_match):
        prefix, values, suffix = block_match.groups()
        updated_values = re.sub(
            r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'[^']*',\s*'[^']*'\)", 
            alias_replacer, 
            values
        )
        return prefix + updated_values + suffix

    content = aliases_pattern.sub(process_aliases_block, content)

    # Overwrite the SQL file with the computed hashes
    sql_path.write_text(content, encoding="utf-8")
    print(f"Successfully updated all phonetic hashes in {sql_path.name}")

if __name__ == "__main__":
    update_seed()
