# src/cli.py

import click
import json
import time
from pathlib import Path
from src.db.client import KiviDB
from dotenv import load_dotenv

load_dotenv()
db = KiviDB()

@click.group()
def cli():
    """Kivi Phonetic Memory Layer CLI"""
    pass

# ==========================================
# 1. kivi learn
# ==========================================
@cli.command()
@click.option('--asr', required=True, help="Raw ASR hypothesis transcript")
@click.option('--final', required=True, help="Corrected ground-truth transcript")
@click.option('--type', 'entity_types', multiple=True, help="Entity type (e.g. PERSON, TECH_TERM). Can be passed multiple times.")
def learn(asr: str, final: str, entity_types: tuple):
    from src.engine.aligner import extract_learning_pairs
    from src.engine.phonetics import get_phonetic_keys
    """Aligns tokens, extracts entities, computes phonetics, and stores them in memory."""
    pairs = extract_learning_pairs(asr, final)
    learned_entities = []

    num_pairs = len(pairs)
    num_types = len(entity_types)

    # Safe positional mapping check
    if num_types > num_pairs:
        click.secho(f"Warning: Provided {num_types} types but only extracted {num_pairs} entities. Excess types will be ignored.", fg="yellow", err=True)

    for i, pair in enumerate(pairs):
        pri_meta, sec_meta = get_phonetic_keys(pair['canonical'])
        alias_pri, alias_sec = get_phonetic_keys(pair['alias'])
        
        # Positional mapping: default to None (NULL in SQL) if we run out of types
        current_type = entity_types[i] if i < num_types else None

        entity_id = db.learn_entity(
            canonical=pair['canonical'],
            alias=pair['alias'],
            entity_type=current_type,
            primary_meta=pri_meta,
            sec_meta=sec_meta,
            alias_pri=alias_pri,
            alias_sec=alias_sec,
            context=pair['context']
        )
        
        # Read back current confidence and the newly calculated weights
        records = db.inspect_entities(pair['canonical'])
        confidence = records[0]['confidence_score'] if records else 0.70
        updated_weights = records[0]['context_weights'] if records else {}
        
        learned_entities.append({
            "canonical": pair['canonical'],
            "alias": pair['alias'],
            "entity_type": current_type,
            "primary_metaphone": pri_meta,
            "secondary_metaphone": sec_meta,
            "extracted_context": pair['context'],         
            "updated_context_weights": updated_weights,   
            "confidence_score": confidence
        })

    click.echo(json.dumps({"learned": learned_entities}, indent=2))

# ==========================================
# 2. kivi process
# ==========================================
@cli.command()
@click.option('--asr', required=True, help="Raw ASR hypothesis transcript")
@click.option('--fmt', required=True, help="Base formatted transcript")
def process(asr: str, fmt: str):
    from src.engine.memory import retrieve_candidates
    from src.engine.guard import resolve_ambiguity
    """Executes phonetic indexing, candidate retrieval, and context-guarded formatting."""
    start_time = time.time()
    
    # 1. Sliding window (1-3 n-grams) phonetic retrieval
    candidates = retrieve_candidates(asr, db)
    
    # 2. Zero-candidate shortcut bypasses LLM
    if not candidates:
        latency_ms = int((time.time() - start_time) * 1000)
        click.echo(json.dumps({
            "asr": asr,
            "formatted": fmt,
            "memory_aware": fmt,
            "interventions": [],
            "latency_ms": latency_ms
        }, indent=2))
        return

    # 3. LLM Context Guard Disambiguation
    decision = resolve_ambiguity(asr, fmt, candidates)
    latency_ms = int((time.time() - start_time) * 1000)
    
    click.echo(json.dumps({
        "asr": asr,
        "formatted": fmt,
        "memory_aware": decision.get("output", fmt),
        "interventions": decision.get("interventions", []),
        "latency_ms": latency_ms
    }, indent=2))

# ==========================================
# 3. kivi inspect
# ==========================================
@cli.command()
@click.option('--entity', default=None, help="Filter by canonical name")
def inspect(entity: str):
    """Dumps known canonical entities, phonetic keys, context triggers, and confidence."""
    records = db.inspect_entities(entity)
    click.echo(json.dumps(records, indent=2))

# ==========================================
# 4. kivi forget
# ==========================================
@cli.command()
@click.option('--entity', required=True, help="Canonical name of the entity to forget")
def forget(entity: str):
    """Completely drops a learned entity from memory."""
    success = db.forget_entity(entity)
    if success:
        click.secho(f"Entity '{entity}' forgotten successfully.", fg="green")
    else:
        click.secho(f"Warning: Entity '{entity}' not found in database.", fg="red", err=True)

# ==========================================
# 5. kivi penalize
# ==========================================
@cli.command()
@click.option('--entity', required=True, help="Canonical name of the entity to penalize")
def penalize(entity: str):
    """Reduces confidence score and logs a rejected LLM intervention for an entity."""
    success = db.penalize_entity(entity)
    if success:
        click.secho(f"Entity '{entity}' penalized. Confidence score has been reduced.", fg="yellow")
    else:
        click.secho(f"Warning: Entity '{entity}' not found in database.", fg="red", err=True)

# ==========================================
# 6. kivi reset
# ==========================================
@cli.command()
@click.option('--seed', is_flag=True, help="Load default seed baseline data after reset")
def reset(seed: bool):
    """Wipes the database and reapplies schema/seed."""
    schema_path = Path("src/db/schema.sql")
    if not schema_path.exists():
        click.secho(f"Error: {schema_path} not found.", fg="red")
        return
        
    db.reset(schema_path)
    
    if seed:
        seed_path = Path("seeds/default.sql")
        if seed_path.exists():
            with open(seed_path, "r") as f:
                db.conn.executescript(f.read())
            click.secho("Database reset and seeded successfully.", fg="green")
            return
            
    click.secho("Database wiped and clean schema applied.", fg="yellow")

# ==========================================
# 7. kivi eval
# ==========================================
@cli.command(name="eval")
@click.option('--dataset', required=True, type=click.Path(exists=True), help="Path to evaluation JSON")
@click.option('--output', required=True, type=click.Path(), help="Path to write evaluation results")
def run_eval_cmd(dataset: str, output: str):
    """Executes the evaluation benchmark suite across all edge-case categories."""
    from eval.runner import run_eval
    click.echo(f"Running evaluation on {dataset}...")
    run_eval(dataset_path=dataset, output_path=output)
    click.secho(f"Evaluation finished. Metrics written to {output}", fg="green")

if __name__ == "__main__":
    cli()
